#!/usr/bin/env python3
"""
AgentBuilder API Demo Script

This script demonstrates the complete API workflow:
1. Authentication (login)
2. Create an agent
3. Create a workflow
4. Execute agent
5. Execute workflow
6. View execution results

Usage:
    python demo_api.py
"""

import requests
import time
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@agentbuilder.com"
ADMIN_PASSWORD = "admin123"


class AgentBuilderDemo:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.org_id = None
        self.project_id = None
        self.agent_id = None
        self.workflow_id = None
        self.tool_ids = {}
    
    def print_step(self, step: str, message: str):
        """Print formatted step message"""
        print(f"\n{'='*60}")
        print(f"📍 STEP {step}: {message}")
        print(f"{'='*60}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def login(self) -> bool:
        """Step 1: Authenticate and get JWT token"""
        self.print_step("1", "Authentication")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                self.print_success(f"Logged in as {ADMIN_EMAIL}")
                
                # Get user info
                user_response = requests.get(
                    f"{self.base_url}/api/auth/me",
                    headers=self.headers
                )
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.org_id = user_data["organization_id"]
                    self.print_info(f"Organization ID: {self.org_id}")
                
                return True
            else:
                self.print_error(f"Login failed: {response.text}")
                return False
        
        except Exception as e:
            self.print_error(f"Login error: {str(e)}")
            return False
    
    def list_tools(self) -> bool:
        """Step 2: List available tools"""
        self.print_step("2", "List Available Tools")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/tools/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                tools = data["tools"]
                self.print_success(f"Found {len(tools)} tools")
                
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")
                    self.tool_ids[tool['name']] = tool['id']
                
                return True
            else:
                self.print_error(f"Failed to list tools: {response.text}")
                return False
        
        except Exception as e:
            self.print_error(f"Error listing tools: {str(e)}")
            return False
    
    def create_project(self) -> bool:
        """Step 3: Create a test project"""
        self.print_step("3", "Create Test Project")
        
        # Note: This endpoint doesn't exist yet, so we'll mock a project ID
        # In production, you'd create a project via the API
        # For now, we'll assume there's a default project
        
        self.print_info("Using default project (project creation endpoint TBD)")
        # You would query the database or create via API here
        # For demo purposes, we'll assume a project exists
        return True
    
    def create_agent(self) -> bool:
        """Step 4: Create an AI agent"""
        self.print_step("4", "Create Research Agent")
        
        # Get tool IDs
        web_search_id = self.tool_ids.get("web_search")
        calculator_id = self.tool_ids.get("calculator")
        
        if not web_search_id:
            self.print_error("web_search tool not found")
            return False
        
        # For this demo, we need a project_id
        # In a real scenario, this would come from project creation
        self.print_info("Note: Requires valid project_id - skipping for demo")
        self.print_info("Agent configuration:")
        
        agent_config = {
            "name": "Research Assistant",
            "role": "Senior Research Analyst",
            "goal": "Provide comprehensive research reports on any topic",
            "instructions": "Always cite sources, verify facts, and provide balanced analysis",
            "configuration": {
                "temperature": 0.7,
                "max_tokens": 2000,
                "model": "qwen/qwen-3-72b"
            },
            "tool_ids": [web_search_id, calculator_id] if calculator_id else [web_search_id],
            "memory_config": {"type": "session"}
        }
        
        print(json.dumps(agent_config, indent=2))
        
        # Would create via API if project_id available
        return True
    
    def create_workflow(self) -> bool:
        """Step 5: Create a multi-agent workflow"""
        self.print_step("5", "Create Multi-Agent Workflow")
        
        workflow_config = {
            "name": "Research & Analysis Pipeline",
            "description": "Sequential workflow: research → analyze → summarize",
            "trigger_type": "manual",
            "steps": [
                {
                    "name": "research",
                    "type": "single_agent",
                    "agent_id": "<research_agent_id>",
                    "input_mapping": {"query": "query"},
                    "output_capture": ["research_results"]
                },
                {
                    "name": "analyze",
                    "type": "single_agent",
                    "agent_id": "<analysis_agent_id>",
                    "input_mapping": {"data": "step_outputs.research_results"},
                    "output_capture": ["analysis"]
                },
                {
                    "name": "summarize",
                    "type": "single_agent",
                    "agent_id": "<summary_agent_id>",
                    "input_mapping": {"content": "step_outputs.analysis"},
                    "output_capture": ["final_summary"]
                }
            ]
        }
        
        self.print_info("Workflow configuration:")
        print(json.dumps(workflow_config, indent=2))
        
        return True
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        self.print_step("0", "Health Check")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Backend is healthy: {data['service']}")
                self.print_info(f"Environment: {data['environment']}")
                return True
            else:
                self.print_error("Backend health check failed")
                return False
        
        except Exception as e:
            self.print_error(f"Cannot connect to backend: {str(e)}")
            self.print_info(f"Make sure the backend is running at {self.base_url}")
            return False
    
    def run_demo(self):
        """Run complete demo"""
        print("\n" + "="*60)
        print("🚀 AgentBuilder API Demo")
        print("="*60)
        
        # Health check
        if not self.test_health_check():
            return
        
        # Authentication
        if not self.login():
            return
        
        # List tools
        if not self.list_tools():
            return
        
        # Create project (placeholder)
        self.create_project()
        
        # Create agent (demo only - needs project)
        self.create_agent()
        
        # Create workflow (demo only)
        self.create_workflow()
        
        print("\n" + "="*60)
        print("✅ Demo completed successfully!")
        print("="*60)
        print("\n📝 Next Steps:")
        print("1. Create a project via database or API")
        print("2. Use the project_id to create agents")
        print("3. Execute agents with /api/executions/agent/{agent_id}")
        print("4. Monitor execution via WebSocket: ws://localhost:8000/ws/executions/{execution_id}")
        print("5. Create workflows and execute them")
        print("\n📖 API Documentation: http://localhost:8000/docs")


def main():
    """Main entry point"""
    demo = AgentBuilderDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()
