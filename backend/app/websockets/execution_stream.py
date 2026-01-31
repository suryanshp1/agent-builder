"""
WebSocket endpoints for real-time execution log streaming
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Set
from uuid import UUID
import asyncio
import json
import logging

from app.database import get_db
from app.models.execution import Execution, ExecutionLog

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for execution log streaming
    """
    
    def __init__(self):
        # Map of execution_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, execution_id: str):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = set()
        
        self.active_connections[execution_id].add(websocket)
        logger.info(f"WebSocket connected for execution {execution_id}")
    
    def disconnect(self, websocket: WebSocket, execution_id: str):
        """Remove a WebSocket connection"""
        if execution_id in self.active_connections:
            self.active_connections[execution_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
        
        logger.info(f"WebSocket disconnected for execution {execution_id}")
    
    async def broadcast(self, execution_id: str, message: dict):
        """
        Broadcast a message to all connections for an execution
        
        Args:
            execution_id: Execution UUID
            message: Message to broadcast
        """
        if execution_id not in self.active_connections:
            return
        
        # Remove dead connections
        dead_connections = set()
        
        for connection in self.active_connections[execution_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                dead_connections.add(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.active_connections[execution_id].discard(connection)


# Global connection manager
manager = ConnectionManager()


async def stream_execution_logs(
    websocket: WebSocket,
    execution_id: str,
    db: Session
):
    """
    Stream execution logs to WebSocket client
    
    Args:
        websocket: WebSocket connection
        execution_id: Execution UUID
        db: Database session
    """
    await manager.connect(websocket, execution_id)
    
    try:
        # Get execution
        execution = db.query(Execution).filter(Execution.id == UUID(execution_id)).first()
        
        if not execution:
            await websocket.send_json({
                "type": "error",
                "message": "Execution not found"
            })
            return
        
        # Send initial execution state
        await websocket.send_json({
            "type": "execution_state",
            "data": {
                "id": str(execution.id),
                "status": execution.status,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
            }
        })
        
        # Send existing logs
        logs = db.query(ExecutionLog).filter(
            ExecutionLog.execution_id == UUID(execution_id)
        ).order_by(ExecutionLog.timestamp).all()
        
        for log in logs:
            await websocket.send_json({
                "type": "log",
                "data": {
                    "id": str(log.id),
                    "step_number": log.step_number,
                    "log_type": log.log_type,
                    "log_data": log.log_data,
                    "timestamp": log.timestamp.isoformat()
                }
            })
        
        # Keep connection alive and listen for new logs
        last_log_count = len(logs)
        
        while True:
            # Check for new logs every 1 second
            await asyncio.sleep(1)
            
            # Get updated execution state
            db.refresh(execution)
            
            # Send status updates
            await websocket.send_json({
                "type": "execution_state",
                "data": {
                    "id": str(execution.id),
                    "status": execution.status,
                    "output_data": execution.output_data,
                    "error_message": execution.error_message,
                    "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
                }
            })
            
            # Get new logs
            current_logs = db.query(ExecutionLog).filter(
                ExecutionLog.execution_id == UUID(execution_id)
            ).order_by(ExecutionLog.timestamp).all()
            
            # Send new logs
            if len(current_logs) > last_log_count:
                new_logs = current_logs[last_log_count:]
                for log in new_logs:
                    await websocket.send_json({
                        "type": "log",
                        "data": {
                            "id": str(log.id),
                            "step_number": log.step_number,
                            "log_type": log.log_type,
                            "log_data": log.log_data,
                            "timestamp": log.timestamp.isoformat()
                        }
                    })
                
                last_log_count = len(current_logs)
            
            # If execution is complete, send final message and close
            if execution.status in ["success", "failed", "cancelled"]:
                await websocket.send_json({
                    "type": "execution_complete",
                    "data": {
                        "status": execution.status,
                        "output_data": execution.output_data,
                        "error_message": execution.error_message
                    }
                })
                break
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from execution {execution_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    
    finally:
        manager.disconnect(websocket, execution_id)


async def broadcast_log_update(execution_id: str, log_data: dict):
    """
    Broadcast a log update to all connected clients
    
    This should be called from the Celery task when new logs are created
    
    Args:
        execution_id: Execution UUID
        log_data: Log data to broadcast
    """
    await manager.broadcast(execution_id, {
        "type": "log",
        "data": log_data
    })
