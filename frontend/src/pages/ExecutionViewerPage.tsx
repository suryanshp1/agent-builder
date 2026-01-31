/**
 * Execution Viewer Page
 * 
 * Real-time execution monitoring with WebSocket log streaming
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import { useExecutionStream } from '../hooks/useExecutionStream';
import apiClient from '../lib/api';

export default function ExecutionViewerPage() {
    const { executionId } = useParams<{ executionId: string }>();
    const navigate = useNavigate();

    const { logs, executionState, isConnected, error: wsError } = useExecutionStream(executionId || null);
    const [execution, setExecution] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Fetch initial execution details
    useEffect(() => {
        if (executionId) {
            fetchExecution();
        }
    }, [executionId]);

    const fetchExecution = async () => {
        if (!executionId) return;

        try {
            const data = await apiClient.getExecution(executionId);
            setExecution(data);
        } catch (err) {
            console.error('Failed to fetch execution:', err);
        } finally {
            setIsLoading(false);
        }
    };

    // Make execution logs readable for Copilot
    useCopilotReadable({
        description: "Current execution logs and state",
        value: {
            status: executionState?.status || execution?.status,
            totalLogs: logs.length,
            recentLogs: logs.slice(-5).map(l => ({
                type: l.log_type,
                step: l.step_number,
            })),
            hasErrors: logs.some(l => l.log_type === 'error'),
        },
    });

    // Copilot action: Summarize execution
    useCopilotAction({
        name: "summarizeExecution",
        description: "Summarize the execution results and logs",
        parameters: [],
        handler: async () => {
            const status = executionState?.status || execution?.status;
            const errorLogs = logs.filter(l => l.log_type === 'error');
            const toolCalls = logs.filter(l => l.log_type === 'tool_start');

            let summary = `Execution ${status}. `;
            summary += `${logs.length} total log entries. `;
            summary += `${toolCalls.length} tool calls made. `;

            if (errorLogs.length > 0) {
                summary += `${errorLogs.length} errors encountered.`;
            }

            return summary;
        },
    });

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'success':
                return 'bg-green-100 text-green-800 border-green-200';
            case 'running':
                return 'bg-blue-100 text-blue-800 border-blue-200';
            case 'failed':
                return 'bg-red-100 text-red-800 border-red-200';
            case 'pending':
                return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const getLogIcon = (logType: string) => {
        switch (logType) {
            case 'llm_start':
                return '🤖';
            case 'llm_end':
                return '💬';
            case 'tool_start':
                return '🔧';
            case 'tool_end':
                return '✓';
            case 'error':
                return '❌';
            default:
                return '📝';
        }
    };

    const formatTimestamp = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    const currentStatus = executionState?.status || execution?.status || 'unknown';

    return (
        <div className="max-w-6xl">
            {/* Header */}
            <div className="mb-6">
                <div className="flex items-center space-x-4 mb-4">
                    <button
                        onClick={() => navigate('/dashboard/executions')}
                        className="text-gray-600 hover:text-gray-900"
                    >
                        ← Back
                    </button>
                    <h2 className="text-3xl font-bold text-gray-900">Execution Details</h2>
                </div>

                {/* Status Bar */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-4">
                            <span className={`px-4 py-2 rounded-lg border font-semibold ${getStatusColor(currentStatus)}`}>
                                {currentStatus.toUpperCase()}
                            </span>
                            {isConnected && (
                                <span className="flex items-center text-green-600 text-sm">
                                    <span className="w-2 h-2 bg-green-600 rounded-full mr-2 animate-pulse"></span>
                                    Live
                                </span>
                            )}
                        </div>
                        <div className="text-sm text-gray-600">
                            ID: <code className="bg-gray-100 px-2 py-1 rounded">{executionId}</code>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <div className="text-gray-600">Started</div>
                            <div className="font-semibold">
                                {executionState?.started_at || execution?.started_at
                                    ? new Date(executionState?.started_at || execution?.started_at).toLocaleString()
                                    : 'N/A'}
                            </div>
                        </div>
                        <div>
                            <div className="text-gray-600">Completed</div>
                            <div className="font-semibold">
                                {executionState?.completed_at || execution?.completed_at
                                    ? new Date(executionState?.completed_at || execution?.completed_at).toLocaleString()
                                    : 'In progress...'}
                            </div>
                        </div>
                        <div>
                            <div className="text-gray-600">Total Logs</div>
                            <div className="font-semibold">{logs.length}</div>
                        </div>
                        <div>
                            <div className="text-gray-600">Agent</div>
                            <div className="font-semibold">
                                {execution?.agent_id ? (
                                    <Link
                                        to={`/dashboard/agents/${execution.agent_id}`}
                                        className="text-blue-600 hover:text-blue-700"
                                    >
                                        View Agent →
                                    </Link>
                                ) : (
                                    'N/A'
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Error Message */}
            {wsError && (
                <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                    WebSocket Error: {wsError}
                </div>
            )}

            {/* Logs */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                    <h3 className="text-xl font-semibold text-gray-900">Execution Logs</h3>
                    <p className="text-sm text-gray-600 mt-1">
                        Real-time streaming {isConnected && '(connected)'}
                    </p>
                </div>

                <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
                    {logs.length === 0 ? (
                        <div className="p-12 text-center text-gray-500">
                            <div className="text-4xl mb-2">📝</div>
                            <p>No logs yet. Waiting for execution to start...</p>
                        </div>
                    ) : (
                        logs.map((log, index) => (
                            <div key={log.id || index} className="p-4 hover:bg-gray-50 transition">
                                <div className="flex items-start space-x-3">
                                    <span className="text-2xl">{getLogIcon(log.log_type)}</span>
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="flex items-center space-x-3">
                                                <span className="font-semibold text-gray-900">
                                                    Step {log.step_number}
                                                </span>
                                                <span className="text-sm px-2 py-1 bg-gray-100 rounded">
                                                    {log.log_type}
                                                </span>
                                            </div>
                                            <span className="text-sm text-gray-500">
                                                {formatTimestamp(log.timestamp)}
                                            </span>
                                        </div>
                                        <div className="text-sm text-gray-700">
                                            {log.log_type === 'tool_start' && (
                                                <div>
                                                    <span className="font-medium">Tool: </span>
                                                    {log.log_data.tool || 'Unknown'}
                                                    {log.log_data.input && (
                                                        <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                                                            {JSON.stringify(log.log_data.input, null, 2)}
                                                        </pre>
                                                    )}
                                                </div>
                                            )}
                                            {log.log_type === 'tool_end' && (
                                                <div>
                                                    <span className="font-medium">Output: </span>
                                                    <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-x-auto max-h-32">
                                                        {typeof log.log_data.output === 'string'
                                                            ? log.log_data.output
                                                            : JSON.stringify(log.log_data.output, null, 2)}
                                                    </pre>
                                                </div>
                                            )}
                                            {log.log_type === 'llm_start' && (
                                                <div>
                                                    <span className="font-medium">Model: </span>
                                                    {log.log_data.model || 'Unknown'}
                                                </div>
                                            )}
                                            {log.log_type === 'llm_end' && (
                                                <div>
                                                    <span className="font-medium">Response received</span>
                                                </div>
                                            )}
                                            {log.log_type === 'error' && (
                                                <div className="text-red-600">
                                                    <span className="font-medium">Error: </span>
                                                    {log.log_data.error || 'Unknown error'}
                                                </div>
                                            )}
                                            {!['tool_start', 'tool_end', 'llm_start', 'llm_end', 'error'].includes(log.log_type) && (
                                                <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                                                    {JSON.stringify(log.log_data, null, 2)}
                                                </pre>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Output */}
            {(executionState?.output_data || execution?.output_data) && (
                <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4">Final Output</h3>
                    <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto">
                        {JSON.stringify(executionState?.output_data || execution?.output_data, null, 2)}
                    </pre>
                </div>
            )}

            {/* Error */}
            {(executionState?.error_message || execution?.error_message) && (
                <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-6">
                    <h3 className="text-xl font-semibold text-red-900 mb-4">Error</h3>
                    <p className="text-red-700">{executionState?.error_message || execution?.error_message}</p>
                </div>
            )}
        </div>
    );
}
