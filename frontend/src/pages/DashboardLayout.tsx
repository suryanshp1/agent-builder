/**
 * Dashboard Layout Component
 */

import { useState } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function DashboardLayout() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b border-gray-200">
                <div className="px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                            className="p-2 rounded-lg hover:bg-gray-100 transition"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                            </svg>
                        </button>
                        <h1 className="text-2xl font-bold text-gray-900">AgentBuilder</h1>
                    </div>

                    <div className="flex items-center space-x-4">
                        <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">{user?.email}</p>
                            <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            <div className="flex">
                {/* Sidebar */}
                <aside
                    className={`${isSidebarOpen ? 'w-64' : 'w-0'
                        } transition-all duration-300 overflow-hidden bg-white border-r border-gray-200 h-[calc(100vh-73px)]`}
                >
                    <nav className="p-4 space-y-2">
                        <NavLink to="/dashboard" icon="📊">
                            Overview
                        </NavLink>
                        <NavLink to="/dashboard/agents" icon="🤖">
                            Agents
                        </NavLink>
                        <NavLink to="/dashboard/workflows" icon="🔄">
                            Workflows
                        </NavLink>
                        <NavLink to="/dashboard/tools" icon="🔧">
                            Tools
                        </NavLink>
                        <NavLink to="/dashboard/executions" icon="📝">
                            Executions
                        </NavLink>
                    </nav>
                </aside>

                {/* Main Content */}
                <main className="flex-1 p-8">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

function NavLink({ to, icon, children }: { to: string; icon: string; children: React.ReactNode }) {
    return (
        <Link
            to={to}
            className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-blue-50 hover:text-blue-700 transition"
        >
            <span className="text-xl">{icon}</span>
            <span className="font-medium">{children}</span>
        </Link>
    );
}
