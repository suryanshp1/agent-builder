/**
 * Execute Workflow Modal
 * 
 * Modal dialog for executing a workflow with JSON input
 */

import { useState } from 'react';
import apiClient from '../lib/api';
import { useNavigate } from 'react-router-dom';

interface ExecuteWorkflowModalProps {
    workflowId: string;
    workflowName: string;
    onClose: () => void;
}

export default function ExecuteWorkflowModal({ workflowId, workflowName, onClose }: ExecuteWorkflowModalProps) {
    const navigate = useNavigate();
    const [inputData, setInputData] = useState('{}');
    const [isExecuting, setIsExecuting] = useState(false);
    const [error, setError] = useState('');

    const handleExecute = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsExecuting(true);

        try {
            // Validate JSON
            const parsedInput = JSON.parse(inputData);

            // Execute workflow
            const result = await apiClient.executeWorkflow(workflowId, parsedInput);

            // Navigate to execution detail page
            navigate(`/dashboard/executions/${result.id}`);
        } catch (err: any) {
            if (err instanceof SyntaxError) {
                setError('Invalid JSON format. Please check your input.');
            } else {
                setError(err.response?.data?.detail || 'Failed to execute workflow');
            }
        } finally {
            setIsExecuting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-gray-900">
                        Execute Workflow
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        ✕
                    </button>
                </div>

                <div className="mb-4">
                    <p className="text-sm text-gray-600">
                        Workflow: <span className="font-medium text-gray-900">{workflowName}</span>
                    </p>
                </div>

                {error && (
                    <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleExecute} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Input Data (JSON)
                        </label>
                        <textarea
                            value={inputData}
                            onChange={(e) => setInputData(e.target.value)}
                            rows={10}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                            placeholder='{"key": "value"}'
                        />
                        <p className="mt-2 text-xs text-gray-500">
                            Enter workflow input data as JSON. Example: {' '}
                            <code className="bg-gray-100 px-1 py-0.5 rounded">{'{"query": "search term"}'}</code>
                        </p>
                    </div>

                    <div className="flex justify-end space-x-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                            disabled={isExecuting}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                            disabled={isExecuting}
                        >
                            {isExecuting ? 'Executing...' : '▶ Execute Workflow'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
