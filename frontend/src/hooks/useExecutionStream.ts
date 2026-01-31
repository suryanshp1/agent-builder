/**
 * WebSocket Hook for Execution Log Streaming
 * 
 * Manages WebSocket connection and real-time log updates
 */

import { useEffect, useState, useCallback, useRef } from 'react';

export interface ExecutionLog {
    id: string;
    step_number: number;
    log_type: string;
    log_data: any;
    timestamp: string;
}

export interface ExecutionState {
    id: string;
    status: string;
    started_at?: string;
    completed_at?: string;
    output_data?: any;
    error_message?: string;
}

interface WebSocketMessage {
    type: 'execution_state' | 'log' | 'execution_complete' | 'error';
    data: any;
}

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function useExecutionStream(executionId: string | null) {
    const [logs, setLogs] = useState<ExecutionLog[]>([]);
    const [executionState, setExecutionState] = useState<ExecutionState | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        if (!executionId) return;

        try {
            const ws = new WebSocket(`${WS_BASE_URL}/ws/executions/${executionId}`);

            ws.onopen = () => {
                console.log('WebSocket connected');
                setIsConnected(true);
                setError(null);
            };

            ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data);

                    switch (message.type) {
                        case 'execution_state':
                            setExecutionState(message.data);
                            break;

                        case 'log':
                            setLogs(prev => [...prev, message.data]);
                            break;

                        case 'execution_complete':
                            setExecutionState(prev => ({
                                ...prev,
                                ...message.data,
                            } as ExecutionState));
                            // Close connection on completion
                            ws.close();
                            break;

                        case 'error':
                            setError(message.data.message || 'Unknown error');
                            break;
                    }
                } catch (err) {
                    console.error('Error parsing WebSocket message:', err);
                }
            };

            ws.onerror = (event) => {
                console.error('WebSocket error:', event);
                setError('WebSocket connection error');
                setIsConnected(false);
            };

            ws.onclose = () => {
                console.log('WebSocket closed');
                setIsConnected(false);

                // Auto-reconnect if execution is still running
                if (executionState?.status === 'running') {
                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, 3000);
                }
            };

            wsRef.current = ws;
        } catch (err) {
            console.error('Error creating WebSocket:', err);
            setError('Failed to create WebSocket connection');
        }
    }, [executionId, executionState?.status]);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
    }, []);

    useEffect(() => {
        if (executionId) {
            connect();
        }

        return () => {
            disconnect();
        };
    }, [executionId]);

    return {
        logs,
        executionState,
        isConnected,
        error,
        reconnect: connect,
        disconnect,
    };
}
