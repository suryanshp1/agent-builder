/**
 * Agents List Page
 * 
 * View and manage all agents
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../lib/api';

interface Agent {
    id: string;
    name: string;
    role: string;
    goal: string;
    created_at: string;
    tool_ids: string[];
}

export default function AgentsListPage() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchAgents();
    }, []);

    const fetchAgents = async () => {
        try {
            // Note: Requires project_id
            const projectId = localStorage.getItem('current_project_id');
            if (!projectId) {
                setError('No project selected');
                setIsLoading(false);
                return;
            }

            const response = await apiClient.listAgents(projectId);
            setAgents(response.agents || []);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to fetch agents');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (agentId: string) => {
        if (!confirm('Are you sure you want to delete this agent?')) return;

        try {
            await apiClient.deleteAgent(agentId);
            setAgents(agents.filter(a => a.id !== agentId));
        } catch (err: any) {
            alert('Failed to delete agent: ' + (err.response?.data?.detail || err.message));
        }
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
                    <h2 className="text-3xl font-bold text-gray-900">AI Agents</h2>
                    <p className="text-gray-600 mt-2">Manage your AI agents and their configurations</p>
                </div>
                <Link
                    to="/dashboard/agents/new"
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                >
                    + Create Agent
                </Link>
            </div>

            {error && (
                <div className="mb-6 bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-lg">
                    {error}
                    <p className="text-sm mt-2">
                        Configure a project_id first. For demo: Run{' '}
                        <code className="bg-yellow-100 px-2 py-1 rounded">
                            localStorage.setItem('current_project_id', 'your-project-id')
                        </code>
                    </p>
                </div>
            )}

            {agents.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                    <div className="text-6xl mb-4">🤖</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No agents yet</h3>
                    <p className="text-gray-600 mb-6">
                        Create your first AI agent to get started
                    </p>
                    <Link
                        to="/dashboard/agents/new"
                        className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                    >
                        Create Your First Agent
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {agents.map((agent) => (
                        <div
                            key={agent.id}
                            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="text-4xl">🤖</div>
                                <button
                                    onClick={() => handleDelete(agent.id)}
                                    className="text-red-600 hover:text-red-700 text-sm"
                                >
                                    Delete
                                </button>
                            </div>

                            <h3 className="font-semibold text-lg text-gray-900 mb-2">{agent.name}</h3>
                            <p className="text-sm text-gray-600 mb-2">{agent.role}</p>
                            <p className="text-sm text-gray-500 mb-4 line-clamp-2">{agent.goal}</p>

                            <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-500">
                                    {agent.tool_ids?.length || 0} tools
                                </span>
                                <Link
                                    to={`/dashboard/agents/${agent.id}`}
                                    className="text-blue-600 hover:text-blue-700 font-medium"
                                >
                                    View Details →
                                </Link>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
