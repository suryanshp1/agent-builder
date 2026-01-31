/**
 * Workflows List Page
 * 
 * View and manage workflows
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../lib/api';

interface Workflow {
    id: string;
    name: string;
    description?: string;
    config: any;
    created_at: string;
}

export default function WorkflowsListPage() {
    const [workflows, setWorkflows] = useState<Workflow[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchWorkflows();
    }, []);

    const fetchWorkflows = async () => {
        try {
            const projectId = localStorage.getItem('current_project_id');
            if (!projectId) {
                setIsLoading(false);
                return;
            }

            const response = await apiClient.listWorkflows(projectId);
            setWorkflows(response.workflows || []);
        } catch (err) {
            console.error('Failed to fetch workflows:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (workflowId: string) => {
        if (!confirm('Are you sure you want to delete this workflow?')) return;

        try {
            // await apiClient.deleteWorkflow(workflowId);  // TODO: Implement deleteWorkflow in API client
            // queryClient.invalidateQueries({ queryKey: ['workflows'] }); // queryClient is not defined in this scope
        } catch (error: any) {
            alert('Failed to delete workflow: ' + (error.response?.data?.detail || error.message));
        }
    };

    const getStepCount = (config: any) => {
        return config?.steps?.length || 0;
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
                    <h2 className="text-3xl font-bold text-gray-900">Workflows</h2>
                    <p className="text-gray-600 mt-2">Orchestrate multi-agent workflows</p>
                </div>
                <Link
                    to="/dashboard/workflows/new"
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                >
                    + Create Workflow
                </Link>
            </div>

            {workflows.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                    <div className="text-6xl mb-4">🔄</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No workflows yet</h3>
                    <p className="text-gray-600 mb-6">
                        Create multi-step workflows to orchestrate multiple agents
                    </p>
                    <Link
                        to="/dashboard/workflows/new"
                        className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                    >
                        Create Your First Workflow
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {workflows.map((workflow) => (
                        <div
                            key={workflow.id}
                            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="text-4xl">🔄</div>
                                <button
                                    onClick={() => handleDelete(workflow.id)}
                                    className="text-red-600 hover:text-red-700 text-sm"
                                >
                                    Delete
                                </button>
                            </div>

                            <h3 className="font-semibold text-lg text-gray-900 mb-2">{workflow.name}</h3>
                            <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                                {workflow.description || 'No description'}
                            </p>

                            <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-500">
                                    {getStepCount(workflow.config)} steps
                                </span>
                                <Link
                                    to={`/dashboard/workflows/${workflow.id}`}
                                    className="text-blue-600 hover:text-blue-700 font-medium"
                                >
                                    View/Edit →
                                </Link>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
