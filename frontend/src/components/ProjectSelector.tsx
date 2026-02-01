/**
 * Project Selector Component
 * 
 * Dropdown for selecting active project with creation option
 */

import { useState, useEffect } from 'react';
import apiClient from '../lib/api';

interface Project {
    id: string;
    name: string;
    description?: string;
}

export default function ProjectSelector() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [selectedProjectId, setSelectedProjectId] = useState<string>('');
    const [isLoading, setIsLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newProjectName, setNewProjectName] = useState('');
    const [newProjectDescription, setNewProjectDescription] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            setIsLoading(true);
            const data = await apiClient.listProjects();
            setProjects(data);

            // Auto-select from localStorage or first project
            const savedProjectId = localStorage.getItem('current_project_id');
            if (savedProjectId && data.find((p: Project) => p.id === savedProjectId)) {
                setSelectedProjectId(savedProjectId);
            } else if (data.length > 0) {
                const firstProject = data[0];
                setSelectedProjectId(firstProject.id);
                localStorage.setItem('current_project_id', firstProject.id);
            }
        } catch (err) {
            console.error('Failed to fetch projects:', err);
            setError('Failed to load projects');
        } finally {
            setIsLoading(false);
        }
    };

    const handleProjectChange = (projectId: string) => {
        setSelectedProjectId(projectId);
        localStorage.setItem('current_project_id', projectId);
        // Reload the page to refresh data with new project
        window.location.reload();
    };

    const handleCreateProject = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        try {
            const newProject = await apiClient.createProject({
                name: newProjectName,
                description: newProjectDescription,
            });

            setProjects([...projects, newProject]);
            setSelectedProjectId(newProject.id);
            localStorage.setItem('current_project_id', newProject.id);
            setShowCreateModal(false);
            setNewProjectName('');
            setNewProjectDescription('');
            window.location.reload();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create project');
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center space-x-2 text-gray-600">
                <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <span className="text-sm">Loading projects...</span>
            </div>
        );
    }

    if (projects.length === 0) {
        return (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800 text-sm font-medium mb-2">No projects found</p>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                >
                    Create Your First Project
                </button>
            </div>
        );
    }

    return (
        <>
            <div className="flex items-center space-x-3">
                <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Active Project
                    </label>
                    <select
                        value={selectedProjectId}
                        onChange={(e) => handleProjectChange(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        {projects.map((project) => (
                            <option key={project.id} value={project.id}>
                                {project.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="pt-6">
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 whitespace-nowrap"
                        title="Create new project"
                    >
                        + New Project
                    </button>
                </div>
            </div>

            {/* Create Project Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                        <h3 className="text-xl font-semibold text-gray-900 mb-4">
                            Create New Project
                        </h3>

                        {error && (
                            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleCreateProject} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Project Name *
                                </label>
                                <input
                                    type="text"
                                    value={newProjectName}
                                    onChange={(e) => setNewProjectName(e.target.value)}
                                    required
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="My Project"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Description (Optional)
                                </label>
                                <textarea
                                    value={newProjectDescription}
                                    onChange={(e) => setNewProjectDescription(e.target.value)}
                                    rows={3}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="Project description..."
                                />
                            </div>

                            <div className="flex justify-end space-x-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowCreateModal(false);
                                        setNewProjectName('');
                                        setNewProjectDescription('');
                                        setError('');
                                    }}
                                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                                >
                                    Create Project
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
}
