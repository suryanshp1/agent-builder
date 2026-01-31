/**
 * Agent Builder Page
 * 
 * Create and configure AI agents with tools and memory
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import apiClient from '../lib/api';

interface Tool {
    id: string;
    name: string;
    description: string;
    category: string;
    type: string;
}

export default function AgentBuilderPage() {
    const navigate = useNavigate();

    // Form state
    const [name, setName] = useState('');
    const [role, setRole] = useState('');
    const [goal, setGoal] = useState('');
    const [instructions, setInstructions] = useState('');
    const [selectedTools, setSelectedTools] = useState<string[]>([]);
    const [temperature, setTemperature] = useState(0.7);
    const [maxTokens, setMaxTokens] = useState(2000);
    const [model, setModel] = useState('qwen/qwen-3-72b');

    // Data state
    const [tools, setTools] = useState<Tool[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    // Fetch available tools
    useEffect(() => {
        fetchTools();
    }, []);

    const fetchTools = async () => {
        try {
            const response = await apiClient.listTools();
            setTools(response.tools);
        } catch (err) {
            console.error('Failed to fetch tools:', err);
        }
    };

    // Make agent configuration readable for Copilot
    useCopilotReadable({
        description: "Current agent configuration being built",
        value: {
            name,
            role,
            goal,
            instructions,
            selectedTools: selectedTools.map(id =>
                tools.find(t => t.id === id)?.name
            ).filter(Boolean),
            temperature,
            maxTokens,
            model,
        },
    });

    // Copilot action: Generate agent configuration
    useCopilotAction({
        name: "generateAgentConfig",
        description: "Generate an AI agent configuration based on user requirements",
        parameters: [
            {
                name: "useCase",
                type: "string",
                description: "The use case or purpose for the agent (e.g., 'research assistant', 'customer support', 'data analyst')",
                required: true,
            },
        ],
        handler: async ({ useCase }) => {
            // AI-generated suggestions based on use case
            const suggestions: Record<string, any> = {
                research: {
                    name: "Research Assistant",
                    role: "Senior Research Analyst",
                    goal: "Conduct comprehensive research and provide well-sourced, accurate information",
                    instructions: "Always cite sources, verify facts from multiple sources, and provide balanced analysis. Structure findings clearly with key points and supporting evidence.",
                    tools: ['web_search'],
                    temperature: 0.7,
                },
                support: {
                    name: "Customer Support Agent",
                    role: "Customer Support Specialist",
                    goal: "Provide helpful, empathetic customer support and resolve issues efficiently",
                    instructions: "Be friendly and professional. Ask clarifying questions. Provide step-by-step solutions. Escalate complex issues when needed.",
                    tools: [],
                    temperature: 0.5,
                },
                analysis: {
                    name: "Data Analyst",
                    role: "Senior Data Analyst",
                    goal: "Analyze data, identify patterns, and provide actionable insights",
                    instructions: "Focus on data-driven insights. Use statistical methods. Visualize findings clearly. Explain technical concepts simply.",
                    tools: ['calculator'],
                    temperature: 0.3,
                },
            };

            // Match use case to template
            const template = Object.keys(suggestions).find(key =>
                useCase.toLowerCase().includes(key)
            ) || 'research';

            const config = suggestions[template];

            setName(config.name);
            setRole(config.role);
            setGoal(config.goal);
            setInstructions(config.instructions);
            setTemperature(config.temperature);

            // Select tools
            const toolIds = tools
                .filter(t => config.tools.includes(t.name))
                .map(t => t.id);
            setSelectedTools(toolIds);

            return `Generated ${config.name} configuration with ${toolIds.length} tools.`;
        },
    });

    // Copilot action: Suggest tools for agent
    useCopilotAction({
        name: "suggestTools",
        description: "Suggest appropriate tools for the agent based on its role and goal",
        parameters: [],
        handler: async () => {
            const suggestions: string[] = [];

            const text = `${role} ${goal} ${instructions}`.toLowerCase();

            if (text.includes('research') || text.includes('search') || text.includes('web')) {
                suggestions.push('web_search');
            }
            if (text.includes('calculat') || text.includes('math') || text.includes('number')) {
                suggestions.push('calculator');
            }
            if (text.includes('file') || text.includes('read') || text.includes('document')) {
                suggestions.push('file_reader');
            }
            if (text.includes('time') || text.includes('date') || text.includes('schedule')) {
                suggestions.push('current_time');
            }

            const toolIds = tools
                .filter(t => suggestions.includes(t.name))
                .map(t => t.id);

            setSelectedTools(toolIds);

            return `Selected ${toolIds.length} recommended tools: ${suggestions.join(', ')}`;
        },
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            // Note: Requires project_id - for demo, we'll show error
            // In production, get project_id from context or route
            const projectId = localStorage.getItem('current_project_id');

            if (!projectId) {
                setError('No project selected. Please create or select a project first.');
                setIsLoading(false);
                return;
            }

            await apiClient.createAgent({
                project_id: projectId,
                name,
                role,
                goal,
                instructions,
                configuration: {
                    temperature,
                    max_tokens: maxTokens,
                    model,
                },
                tool_ids: selectedTools,
                memory_config: { type: "session" },
            });

            navigate('/dashboard/agents');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create agent');
        } finally {
            setIsLoading(false);
        }
    };

    const toggleTool = (toolId: string) => {
        setSelectedTools(prev =>
            prev.includes(toolId)
                ? prev.filter(id => id !== toolId)
                : [...prev, toolId]
        );
    };

    return (
        <div className="max-w-4xl">
            <div className="mb-8">
                <h2 className="text-3xl font-bold text-gray-900">Create AI Agent</h2>
                <p className="text-gray-600 mt-2">
                    Configure an AI agent with specific role, tools, and behavior
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
                                Agent Name *
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Research Assistant"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Role *
                            </label>
                            <input
                                type="text"
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                                required
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Senior Research Analyst"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Goal *
                            </label>
                            <textarea
                                value={goal}
                                onChange={(e) => setGoal(e.target.value)}
                                required
                                rows={3}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Provide comprehensive research reports on any topic with accurate, well-sourced information"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Instructions
                            </label>
                            <textarea
                                value={instructions}
                                onChange={(e) => setInstructions(e.target.value)}
                                rows={5}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Always cite sources, verify information, provide balanced analysis..."
                            />
                        </div>
                    </div>
                </div>

                {/* Tool Selection */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4">Tools</h3>
                    <p className="text-sm text-gray-600 mb-4">
                        Select tools that the agent can use to accomplish its tasks
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {tools.map((tool) => (
                            <label
                                key={tool.id}
                                className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition ${selectedTools.includes(tool.id)
                                        ? 'border-blue-500 bg-blue-50'
                                        : 'border-gray-200 hover:border-gray-300'
                                    }`}
                            >
                                <input
                                    type="checkbox"
                                    checked={selectedTools.includes(tool.id)}
                                    onChange={() => toggleTool(tool.id)}
                                    className="mt-1 mr-3"
                                />
                                <div>
                                    <div className="font-medium text-gray-900">{tool.name}</div>
                                    <div className="text-sm text-gray-600">{tool.description}</div>
                                    <div className="text-xs text-gray-500 mt-1">
                                        {tool.category} • {tool.type}
                                    </div>
                                </div>
                            </label>
                        ))}
                    </div>
                </div>

                {/* Model Configuration */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4">Model Configuration</h3>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Model
                            </label>
                            <select
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                                <option value="qwen/qwen-3-72b">Qwen 3 72B (Recommended)</option>
                                <option value="openai/gpt-4-turbo">GPT-4 Turbo</option>
                                <option value="anthropic/claude-3-opus">Claude 3 Opus</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Temperature: {temperature}
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.1"
                                value={temperature}
                                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                                className="w-full"
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                                <span>Focused</span>
                                <span>Creative</span>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Max Tokens: {maxTokens}
                            </label>
                            <input
                                type="range"
                                min="500"
                                max="4000"
                                step="100"
                                value={maxTokens}
                                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                                className="w-full"
                            />
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-4">
                    <button
                        type="button"
                        onClick={() => navigate('/dashboard/agents')}
                        className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
                    >
                        {isLoading ? 'Creating...' : 'Create Agent'}
                    </button>
                </div>
            </form>
        </div>
    );
}
