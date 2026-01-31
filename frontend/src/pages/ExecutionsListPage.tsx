/**
 * Executions List Page
 * 
 * View execution history with filtering and status
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../lib/api';

interface Execution {
    id: string;
    agent_id?: string;
    workflow_id?: string;
    status: string;
    started_at: string;
    completed_at?: string;
    input_data?: any;
}

export default function ExecutionsListPage() {
    const [executions, setExecutions] = useState<Execution[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('all');

    useEffect(() => {
        fetchExecutions();
    }, [statusFilter]);

    const fetchExecutions = async () => {
        try {
            const filters: any = {};
            if (statusFilter !== 'all') {
                filters.status = statusFilter;
            }

            const response = await apiClient.listExecutions(filters);
            setExecutions(response.executions || []);
        } catch (err) {
            console.error('Failed to fetch executions:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const getStatusBadge = (status: string) => {
        const styles = {
            success: 'bg-green-100 text-green-800',
            running: 'bg-blue-100 text-blue-800',
            failed: 'bg-red-100 text-red-800',
            pending: 'bg-yellow-100 text-yellow-800',
            cancelled: 'bg-gray-100 text-gray-800',
        }[status] || 'bg-gray-100 text-gray-800';

        return (
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${styles}`}>
                {status}
            </span>
        );
    };

    const getDuration = (started: string, completed?: string) => {
        if (!completed) return 'In progress...';

        const start = new Date(started).getTime();
        const end = new Date(completed).getTime();
        const durationMs = end - start;

        if (durationMs < 1000) return `${durationMs}ms`;
        if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
        return `${(durationMs / 60000).toFixed(1)}m`;
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-3xl font-bold text-gray-900">Executions</h2>
                    <p className="text-gray-600 mt-2">Monitor and review agent execution history</p>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
                <div className="flex items-center space-x-4">
                    <label className="text-sm font-medium text-gray-700">Status:</label>
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        <option value="all">All</option>
                        <option value="running">Running</option>
                        <option value="success">Success</option>
                        <option value="failed">Failed</option>
                        <option value="pending">Pending</option>
                    </select>
                </div>
            </div>

            {/* Executions Table */}
            {executions.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                    <div className="text-6xl mb-4">📝</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No executions found</h3>
                    <p className="text-gray-600">
                        {statusFilter !== 'all'
                            ? `No ${statusFilter} executions`
                            : 'Execute an agent to see results here'}
                    </p>
                </div>
            ) : (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Type
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Started
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Duration
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {executions.map((execution) => (
                                <tr key={execution.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {getStatusBadge(execution.status)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {execution.agent_id ? '🤖 Agent' : '🔄 Workflow'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(execution.started_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {getDuration(execution.started_at, execution.completed_at)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <Link
                                            to={`/dashboard/executions/${execution.id}`}
                                            className="text-blue-600 hover:text-blue-700 font-medium"
                                        >
                                            View Details →
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
