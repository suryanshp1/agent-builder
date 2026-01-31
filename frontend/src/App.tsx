import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { CopilotProvider } from './components/CopilotProvider';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardLayout from './pages/DashboardLayout';
import AgentsListPage from './pages/AgentsListPage';
import AgentBuilderPage from './pages/AgentBuilderPage';
import ExecutionsListPage from './pages/ExecutionsListPage';
import ExecutionViewerPage from './pages/ExecutionViewerPage';
import WorkflowsListPage from './pages/WorkflowsListPage';
import WorkflowBuilderPage from './pages/WorkflowBuilderPage';
import ToolsPage from './pages/ToolsPage';
import './index.css';

// Dashboard page components (placeholders for now)
function OverviewPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Active Agents" value="0" icon="🤖" />
        <StatCard title="Workflows" value="0" icon="🔄" />
        <StatCard title="Executions Today" value="0" icon="📝" />
      </div>
    </div>
  );
}

function StatCard({ title, value, icon }: { title: string; value: string; icon: string }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <span className="text-4xl">{icon}</span>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <CopilotProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />

            {/* Protected routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<OverviewPage />} />
              <Route path="agents" element={<AgentsListPage />} />
              <Route path="agents/new" element={<AgentBuilderPage />} />
              <Route path="workflows" element={<WorkflowsListPage />} />
              <Route path="workflows/new" element={<WorkflowBuilderPage />} />
              <Route path="tools" element={<ToolsPage />} />
              <Route path="executions" element={<ExecutionsListPage />} />
              <Route path="executions/:executionId" element={<ExecutionViewerPage />} />
            </Route>

            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </CopilotProvider>
    </AuthProvider>
  );
}

export default App;
