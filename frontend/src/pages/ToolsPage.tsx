/**
 * Tools Registry Page
 * 
 * Browse and manage available tools
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useCopilotReadable } from "@copilotkit/react-core";
import apiClient from '../lib/api';

interface Tool {
    id: string;
    name: string;
    description: string;
    category: string;
    type: string;
    is_global: boolean;
    input_schema?: any;
    output_schema?: any;
}

export default function ToolsPage() {
    const [tools, setTools] = useState<Tool[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [categoryFilter, setCategoryFilter] = useState<string>('all');
    const [typeFilter, setTypeFilter] = useState<string>('all');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchTools();
    }, [categoryFilter, typeFilter]);

    const fetchTools = async () => {
        try {
            const filters: any = {};
            if (categoryFilter !== 'all') filters.category = categoryFilter;
            if (typeFilter !== 'all') filters.type = typeFilter;

            const response = await apiClient.listTools(filters);
            setTools(response.tools || []);
        } catch (err) {
            console.error('Failed to fetch tools:', err);
        } finally {
            setIsLoading(false);
        }
    };

    // Make tools readable for Copilot
    useCopilotReadable({
        description: "Available tools in the registry",
        value: {
            totalTools: tools.length,
            categories: [...new Set(tools.map(t => t.category))],
            types: [...new Set(tools.map(t => t.type))],
            prebuiltCount: tools.filter(t => t.type === 'prebuilt').length,
        },
    });

    const filteredTools = tools.filter(tool =>
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const categories = ['all', ...new Set(tools.map(t => t.category))];
    const types = ['all', ...new Set(tools.map(t => t.type))];

    const getToolIcon = (category: string) => {
        const icons: Record<string, string> = {
            search: '🔍',
            data: '📊',
            communication: '💬',
            utilities: '🔧',
            api: '🌐',
            default: '🛠️',
        };
        return icons[category] || icons.default;
    };

    const getTypeBadge = (type: string) => {
        const styles = {
            prebuilt: 'bg-blue-100 text-blue-800',
            custom: 'bg-purple-100 text-purple-800',
            api: 'bg-green-100 text-green-800',
        }[type] || 'bg-gray-100 text-gray-800';

        return (
            <span className={`px-2 py-1 rounded text-xs font-semibold ${styles}`}>
                {type}
            </span>
        );
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
                    <h2 className="text-3xl font-bold text-gray-900">Tools Registry</h2>
                    <p className="text-gray-600 mt-2">Browse and manage available tools for your agents</p>
                </div>
                <Link
                    to="/dashboard/tools/new"
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                >
                    + Create Custom Tool
                </Link>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Search
                        </label>
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search tools..."
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Category
                        </label>
                        <select
                            value={categoryFilter}
                            onChange={(e) => setCategoryFilter(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            {categories.map(cat => (
                                <option key={cat} value={cat}>
                                    {cat === 'all' ? 'All Categories' : cat}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Type
                        </label>
                        <select
                            value={typeFilter}
                            onChange={(e) => setTypeFilter(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            {types.map(type => (
                                <option key={type} value={type}>
                                    {type === 'all' ? 'All Types' : type}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Tools Grid */}
            {filteredTools.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                    <div className="text-6xl mb-4">🔧</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No tools found</h3>
                    <p className="text-gray-600">
                        {searchQuery ? 'Try different search terms' : 'Create your first custom tool'}
                    </p>
                </div>
            ) : (
                <>
                    <div className="mb-4 text-sm text-gray-600">
                        Showing {filteredTools.length} of {tools.length} tools
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredTools.map((tool) => (
                            <div
                                key={tool.id}
                                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="text-4xl">{getToolIcon(tool.category)}</div>
                                    <div className="flex flex-col gap-2">
                                        {getTypeBadge(tool.type)}
                                        {tool.is_global && (
                                            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-semibold">
                                                Global
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <h3 className="font-semibold text-lg text-gray-900 mb-2">{tool.name}</h3>
                                <p className="text-sm text-gray-600 mb-3 line-clamp-3">{tool.description}</p>

                                <div className="flex items-center justify-between text-xs text-gray-500">
                                    <span className="capitalize">{tool.category}</span>
                                    <button
                                        onClick={() => {
                                            // Show tool details modal
                                            console.log('View tool:', tool.id);
                                        }}
                                        className="text-blue-600 hover:text-blue-700 font-medium"
                                    >
                                        View Details →
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}

            {/* Stats */}
            <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Registry Statistics</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <div className="text-2xl font-bold text-blue-600">
                            {tools.length}
                        </div>
                        <div className="text-sm text-gray-600">Total Tools</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-green-600">
                            {tools.filter(t => t.type === 'prebuilt').length}
                        </div>
                        <div className="text-sm text-gray-600">Prebuilt</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-purple-600">
                            {tools.filter(t => t.type === 'custom').length}
                        </div>
                        <div className="text-sm text-gray-600">Custom</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-yellow-600">
                            {tools.filter(t => t.is_global).length}
                        </div>
                        <div className="text-sm text-gray-600">Global</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
