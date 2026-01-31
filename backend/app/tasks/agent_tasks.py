from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.agent_tasks.execute_agent_task", bind=True)
def execute_agent_task(self, agent_id: str, input_data: dict, execution_id: str):
    """
    Celery task for executing a single agent
    
    Args:
        agent_id: ID of the agent to execute
        input_data: Input data for the agent
        execution_id: Unique execution ID for tracking
    
    Returns:
        dict: Execution result
    """
    from app.database import SessionLocal
    from app.models.agent import Agent
    from app.models.tool import Tool
    from app.models.execution import Execution, ExecutionLog
    from app.services.agent_engine import AgentEngine
    from uuid import UUID
    import asyncio
    from datetime import datetime
    
    db = SessionLocal()
    
    try:
        logger.info(f"Starting agent execution: {execution_id}")
        
        # Get agent from database
        agent = db.query(Agent).filter(Agent.id == UUID(agent_id)).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Get tools
        tools = db.query(Tool).filter(Tool.id.in_(agent.tool_ids)).all()
        
        # Get execution record
        execution = db.query(Execution).filter(Execution.id == UUID(execution_id)).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        # Update status to running
        execution.status = "running"
        db.commit()
        
        # Define log callback
        def log_callback(log_data):
            """Save log to database"""
            log = ExecutionLog(
                execution_id=UUID(log_data["execution_id"]),
                step_number=log_data["step_number"],
                log_type=log_data["log_type"],
                log_data=log_data["log_data"]
            )
            db.add(log)
            db.commit()
        
        # Execute agent
        engine = AgentEngine()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            engine.execute_agent(
                agent=agent,
                tools=tools,
                input_data=input_data,
                execution_id=UUID(execution_id),
                log_callback=log_callback
            )
        )
        
        # Update execution with result
        execution.status = result["status"]
        execution.output_data = {"output": result.get("output"), "intermediate_steps": str(result.get("intermediate_steps"))}
        execution.completed_at = datetime.utcnow()
        
        # TODO: Calculate actual token usage and cost from LLM response
        execution.total_tokens = 0
        execution.total_cost = 0.0
        
        if result["status"] == "failed":
            execution.error_message = result.get("error")
        
        db.commit()
        
        logger.info(f"Agent execution completed: {execution_id}")
        return {"status": result["status"], "execution_id": execution_id}
        
    except Exception as e:
        logger.error(f"Agent execution failed: {execution_id} - {str(e)}", exc_info=True)
        
        # Update execution status
        try:
            execution = db.query(Execution).filter(Execution.id == UUID(execution_id)).first()
            if execution:
                execution.status = "failed"
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                db.commit()
        except:
            pass
        
        raise
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.agent_tasks.execute_workflow_task", bind=True)
def execute_workflow_task(self, workflow_id: str, input_data: dict, execution_id: str):
    """
    Celery task for executing a workflow
    
    Args:
        workflow_id: ID of the workflow to execute
        input_data: Input data for the workflow
        execution_id: Unique execution ID for tracking
    
    Returns:
        dict: Workflow execution result
    """
    from app.database import SessionLocal
    from app.models.workflow import Workflow
    from app.models.agent import Agent
    from app.models.execution import Execution, ExecutionLog
    from app.services.workflow_engine import WorkflowEngine
    from uuid import UUID
    import asyncio
    from datetime import datetime
    
    db = SessionLocal()
    
    try:
        logger.info(f"Starting workflow execution: {execution_id}")
        
        # Get workflow from database
        workflow = db.query(Workflow).filter(Workflow.id == UUID(workflow_id)).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Get all agents used in workflow
        agent_ids = set()
        for step in workflow.steps:
            if step.get("agent_id"):
                agent_ids.add(UUID(step["agent_id"]))
            if step.get("agent_ids"):
                agent_ids.update([UUID(aid) for aid in step["agent_ids"]])
        
        agents = db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
        
        # Get execution record
        execution = db.query(Execution).filter(Execution.id == UUID(execution_id)).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        # Update status to running
        execution.status = "running"
        db.commit()
        
        # Define log callback
        def log_callback(log_data):
            """Save log to database"""
            log = ExecutionLog(
                execution_id=UUID(log_data["execution_id"]),
                step_number=log_data["step_number"],
                log_type=log_data["log_type"],
                log_data=log_data["log_data"]
            )
            db.add(log)
            db.commit()
        
        # Execute workflow
        engine = WorkflowEngine()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            engine.execute_workflow(
                workflow=workflow,
                agents=agents,
                input_data=input_data,
                execution_id=UUID(execution_id),
                log_callback=log_callback
            )
        )
        
        # Update execution with result
        execution.status = result["status"]
        execution.output_data = {"output": result.get("output"), "messages": result.get("messages")}
        execution.completed_at = datetime.utcnow()
        
        if result["status"] == "failed":
            execution.error_message = result.get("error")
        
        db.commit()
        
        logger.info(f"Workflow execution completed: {execution_id}")
        return {"status": result["status"], "execution_id": execution_id}
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {execution_id} - {str(e)}", exc_info=True)
        
        # Update execution status
        try:
            execution = db.query(Execution).filter(Execution.id == UUID(execution_id)).first()
            if execution:
                execution.status = "failed"
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                db.commit()
        except:
            pass
        
        raise
    
    finally:
        db.close()
