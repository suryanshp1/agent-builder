/**
 * Workflow Builder Page
 * 
 * Create and configure multi-agent workflows
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import apiClient from '../lib/api';

interface Agent {
    id: string;
    name: string;
    role: string;
}

interface WorkflowStep {
    id: string;
    name: string;
    agent_id: string;
    type: 'sequential' | 'parallel' | 'conditional';
    config?: any;
}

export default function WorkflowBuilderPage() {
    const navigate = useNavigate();

    // Form state
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [steps, setSteps] = useState<WorkflowStep[]>([]);

    // Data state
    const [agents, setAgents] = useState<Agent[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchAgents();
    }, []);

    const fetchAgents = async () => {
        try {
            const projectId = localStorage.getItem('current_project_id');
            if (!projectId) return;

            const response = await apiClient.listAgents(projectId);
            setAgents(response.agents || []);
        } catch (err) {
            console.error('Failed to fetch agents:', err);
        }
    };

    // Make workflow configuration readable for Copilot
    useCopilotReadable({
        description: "Current workflow configuration being built",
        value: {
            name,
            description,
            totalSteps: steps.length,
            stepTypes: steps.map(s => s.type),
            agentsUsed: steps.map(s => agents.find(a => a.id === s.agent_id)?.name).filter(Boolean),
        },
    });

    // Copilot action: Generate workflow template
    useCopilotAction({
        name: "generateWorkflowTemplate",
        description: "Generate a workflow template based on use case",
        parameters: [
            {
                name: "useCase",
                type: "string",
                description: "The use case (e.g., 'research and summarize', 'multi-step analysis')",
                required: true,
            },
        ],
        handler: async ({ useCase }) => {
            // Generate template based on use case
            const templates: Record<string, any> = {
                research: {
                    name: "Research and Report Workflow",
                    description: "Search, analyze, and create comprehensive report",
                    steps: [
                        { name: "Research", type: "sequential" },
                        { name: "Analyze", type: "sequential" },
                        { name: "Summarize", type: "sequential" },
                    ],
                },
                analysis: {
                    name: "Multi-Step Analysis Workflow",
                    description: "Parallel analysis with final synthesis",
                    steps: [
                        { name: "Data Collection", type: "sequential" },
                        { name: "Parallel Analysis", type: "parallel" },
                        { name: "Synthesis", type: "sequential" },
                    ],
                },
            };

            const template = Object.keys(templates).find(key =>
                useCase.toLowerCase().includes(key)
            ) || 'research';

            const config = templates[template];

            setName(config.name);
            setDescription(config.description);

            // Create step objects
            const newSteps = config.steps.map((step: any, index: number) => ({
                id: `step-${Date.now()}-${index}`,
                name: step.name,
                agent_id: agents[0]?.id || '',
                type: step.type,
                config: {},
            }));

            setSteps(newSteps);

            return `Generated ${config.name} with ${newSteps.length} steps.`;
        },
    });

    const addStep = () => {
        const newStep: WorkflowStep = {
            id: `step-${Date.now()}`,
            name: `Step ${steps.length + 1}`,
            agent_id: agents[0]?.id || '',
            type: 'sequential',
            config: {},
        };
        setSteps([...steps, newStep]);
    };

    const updateStep = (index: number, field: keyof WorkflowStep, value: any) => {
        const updated = [...steps];
        updated[index] = { ...updated[index], [field]: value };
        setSteps(updated);
    };

    const removeStep = (index: number) => {
        setSteps(steps.filter((_, i) => i !== index));
    };

    const moveStep = (index: number, direction: 'up' | 'down') => {
        if (direction === 'up' && index === 0) return;
        if (direction === 'down' && index === steps.length - 1) return;

        const updated = [...steps];
        const newIndex = direction === 'up' ? index - 1 : index + 1;
        [updated[index], updated[newIndex]] = [updated[newIndex], updated[index]];
        setSteps(updated);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const projectId = localStorage.getItem('current_project_id');

            if (!projectId) {
                setError('No project selected');
                setIsLoading(false);
                return;
            }

            // Build workflow config
            const config = {
                steps: steps.map((step, index) => ({
                    step_number: index + 1,
                    agent_id: step.agent_id,
                    type: step.type,
                    config: step.config || {},
                })),
            };

            await apiClient.createWorkflow({
                project_id: projectId,
                name,
                description,
                config,
            });

            navigate('/dashboard/workflows');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create workflow');
        } finally {
            setIsLoading(false);
        }
    };

    const getStepTypeIcon = (type: string) => {
        switch (type) {
            case 'sequential':
                return '→';
            case 'parallel':
                return '⚡';
            case 'conditional':
                return '🔀';
            default:
                return '•';
        }
    };

    return (
        <div className="max-w-5xl">
            <div className="mb-8">
                <h2 className="text-3xl font-bold text-gray-900">Create Workflow</h2>
                <p className="text-gray-600 mt-2">
                    Orchestrate multiple agents in a multi-step workflow
                </p>
            </div>

            {error && (
                <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-8">
                {/* Basic Configuration */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4">Basic Configuration</h3>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Workflow Name *
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Research and Report Workflow"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Description
                            </label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                rows={3}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Multi-step workflow for research and reporting..."
                            />
                        </div>
                    </div>
                </div>

                {/* Workflow Steps */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-xl font-semibold text-gray-900">Workflow Steps</h3>
                        <button
                            type="button"
                            onClick={addStep}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm"
                        >
                            + Add Step
                        </button>
                    </div>

                    {steps.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <div className="text-4xl mb-2">🔄</div>
                            <p>No steps yet. Add your first step to get started.</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {steps.map((step, index) => (
                                <div key={step.id} className="border border-gray-200 rounded-lg p-4">
                                    <div className="flex items-start space-x-4">
                                        {/* Step Number */}
                                        <div className="flex flex-col items-center space-y-1">
                                            <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-semibold">
                                                {index + 1}
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => moveStep(index, 'up')}
                                                disabled={index === 0}
                                                className="text-gray-400 hover:text-gray-600 disabled:opacity-30"
                                            >
                                                ↑
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => moveStep(index, 'down')}
                                                disabled={index === steps.length - 1}
                                                className="text-gray-400 hover:text-gray-600 disabled:opacity-30"
                                            >
                                                ↓
                                            </button>
                                        </div>

                                        {/* Step Configuration */}
                                        <div className="flex-1 space-y-3">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        Step Name
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={step.name}
                                                        onChange={(e) => updateStep(index, 'name', e.target.value)}
                                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                                        placeholder="Research Step"
                                                    />
                                                </div>

                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        Agent
                                                    </label>
                                                    <select
                                                        value={step.agent_id}
                                                        onChange={(e) => updateStep(index, 'agent_id', e.target.value)}
                                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                                    >
                                                        <option value="">Select agent...</option>
                                                        {agents.map((agent) => (
                                                            <option key={agent.id} value={agent.id}>
                                                                {agent.name} ({agent.role})
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        Execution Type
                                                    </label>
                                                    <select
                                                        value={step.type}
                                                        onChange={(e) => updateStep(index, 'type', e.target.value as any)}
                                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                                    >
                                                        <option value="sequential">→ Sequential</option>
                                                        <option value="parallel">⚡ Parallel</option>
                                                        <option value="conditional">🔀 Conditional</option>
                                                    </select>
                                                </div>

                                                <div className="flex items-end">
                                                    <span className="text-2xl">{getStepTypeIcon(step.type)}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Delete Button */}
                                        <button
                                            type="button"
                                            onClick={() => removeStep(index)}
                                            className="text-red-600 hover:text-red-700 mt-2"
                                        >
                                            ✕
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {steps.length > 0 && (
                        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <div className="text-sm text-blue-800">
                                <strong>Execution Flow:</strong> Steps will execute in order from 1 to {steps.length}.
                                Parallel steps run concurrently, sequential steps wait for previous completion.
                            </div>
                        </div>
                    )}
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-4">
                    <button
                        type="button"
                        onClick={() => navigate('/dashboard/workflows')}
                        className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={isLoading || steps.length === 0}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
                    >
                        {isLoading ? 'Creating...' : 'Create Workflow'}
                    </button>
                </div>
            </form>
        </div>
    );
}
