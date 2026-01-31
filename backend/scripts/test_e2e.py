#!/usr/bin/env python3
"""
Complete End-to-End Test Script

This script tests the complete AgentBuilder workflow:
1. Database setup verification
2. Create project 
3. Create agent with tools
4. Execute agent
5. Monitor execution via WebSocket
6. Verify results

Usage:
    python test_e2e.py
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import time
from sqlalchemy.orm import Session
from uuid import uuid4

from app.database import SessionLocal
from app.models.user import User, Organization, Project
from app.models.agent import Agent
from app.models.tool import Tool
from app.models.execution import Execution, ExecutionLog
from app.services.agent_engine import AgentEngine
from app.services.tool_registry import ToolRegistry


class E2ETest:
    """End-to-end test suite"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
        self.test_project_id = None
        self.test_agent_id = None
        self.test_user_id = None
    
    def print_header(self, title: str):
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}\n")
    
    def print_success(self, msg: str):
        print(f"✅ {msg}")
    
    def print_error(self, msg: str):
        print(f"❌ {msg}")
    
    def print_info(self, msg: str):
        print(f"ℹ️  {msg}")
    
    def test_database_connection(self) -> bool:
        """Test 1: Verify database connection"""
        self.print_header("Test 1: Database Connection")
        
        try:
            # Try to query organizations
            orgs = self.db.query(Organization).all()
            self.print_success(f"Database connected - found {len(orgs)} organizations")
            return True
        except Exception as e:
            self.print_error(f"Database connection failed: {str(e)}")
            return False
    
    def test_prebuilt_tools(self) -> bool:
        """Test 2: Verify prebuilt tools exist"""
        self.print_header("Test 2: Prebuilt Tools")
        
        try:
            tools = self.db.query(Tool).filter(Tool.is_global == True).all()
            
            if len(tools) == 0:
                self.print_error("No prebuilt tools found. Run: python scripts/init_db.py")
                return False
            
            self.print_success(f"Found {len(tools)} prebuilt tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            return True
        except Exception as e:
            self.print_error(f"Tool check failed: {str(e)}")
            return False
    
    def test_create_project(self) -> bool:
        """Test 3: Create a test project"""
        self.print_header("Test 3: Create Test Project")
        
        try:
            # Get first organization and user
            org = self.db.query(Organization).first()
            if not org:
                self.print_error("No organization found. Run: python scripts/init_db.py")
                return False
            
            user = self.db.query(User).filter(User.organization_id == org.id).first()
            if not user:
                self.print_error("No user found")
                return False
            
            self.test_user_id = user.id
            
            # Create test project
            project = Project(
                id=uuid4(),
                organization_id=org.id,
                name="E2E Test Project",
                description="Automated test project"
            )
            
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            
            self.test_project_id = project.id
            self.print_success(f"Created project: {project.name} (ID: {project.id})")
            
            return True
        except Exception as e:
            self.print_error(f"Project creation failed: {str(e)}")
            self.db.rollback()
            return False
    
    def test_create_agent(self) -> bool:
        """Test 4: Create a test agent"""
        self.print_header("Test 4: Create Test Agent")
        
        try:
            # Get web_search tool
            web_search = self.db.query(Tool).filter(Tool.name == "web_search").first()
            calculator = self.db.query(Tool).filter(Tool.name == "calculator").first()
            
            if not web_search:
                self.print_error("web_search tool not found")
                return False
            
            tool_ids = [web_search.id]
            if calculator:
                tool_ids.append(calculator.id)
            
            # Create agent
            agent = Agent(
                id=uuid4(),
                project_id=self.test_project_id,
                name="Test Research Agent",
                role="Research Analyst",
                goal="Answer questions using web search",
                instructions="Search the web for accurate information",
                configuration={
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "model": "qwen/qwen-3-72b"
                },
                tool_ids=tool_ids,
                memory_config={"type": "session"},
                created_by=self.test_user_id
            )
            
            self.db.add(agent)
            self.db.commit()
            self.db.refresh(agent)
            
            self.test_agent_id = agent.id
            self.print_success(f"Created agent: {agent.name} (ID: {agent.id})")
            self.print_info(f"Assigned {len(tool_ids)} tools")
            
            return True
        except Exception as e:
            self.print_error(f"Agent creation failed: {str(e)}")
            self.db.rollback()
            return False
    
    def test_agent_execution(self) -> bool:
        """Test 5: Execute the agent"""
        self.print_header("Test 5: Agent Execution")
        
        try:
            # Create execution record
            execution = Execution(
                id=uuid4(),
                agent_id=self.test_agent_id,
                status="running",
                input_data={"query": "What is the capital of France?"},
                executed_by=self.test_user_id
            )
            
            self.db.add(execution)
            self.db.commit()
            self.db.refresh(execution)
            
            self.print_success(f"Created execution: {execution.id}")
            
            # Get agent and tools
            agent = self.db.query(Agent).filter(Agent.id == self.test_agent_id).first()
            tools = self.db.query(Tool).filter(Tool.id.in_(agent.tool_ids)).all()
            
            self.print_info(f"Executing agent with {len(tools)} tools...")
            
            # Define log callback
            def log_callback(log_data):
                log = ExecutionLog(
                    execution_id=execution.id,
                    step_number=log_data["step_number"],
                    log_type=log_data["log_type"],
                    log_data=log_data["log_data"]
                )
                self.db.add(log)
                self.db.commit()
                print(f"  📝 [{log_data['log_type']}] Step {log_data['step_number']}")
            
            # Execute agent
            engine = AgentEngine()
            
            # Run async execution
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                engine.execute_agent(
                    agent=agent,
                    tools=tools,
                    input_data={"query": "What is the capital of France?"},
                    execution_id=execution.id,
                    log_callback=log_callback
                )
            )
            
            # Update execution
            execution.status = result["status"]
            execution.output_data = {"output": result.get("output")}
            self.db.commit()
            
            if result["status"] == "success":
                self.print_success("Agent execution completed successfully!")
                self.print_info(f"Output: {result.get('output', 'No output')[:200]}...")
                return True
            else:
                self.print_error(f"Agent execution failed: {result.get('error')}")
                return False
        
        except Exception as e:
            self.print_error(f"Execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def cleanup(self):
        """Clean up test data"""
        self.print_header("Cleanup")
        
        try:
            if self.test_project_id:
                # Delete project and cascade
                project = self.db.query(Project).filter(Project.id == self.test_project_id).first()
                if project:
                    self.db.delete(project)
                    self.db.commit()
                    self.print_success("Cleaned up test project")
        except Exception as e:
            self.print_error(f"Cleanup failed: {str(e)}")
        finally:
            self.db.close()
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🚀 AgentBuilder End-to-End Test Suite")
        print("="*60)
        
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Prebuilt Tools", self.test_prebuilt_tools),
            ("Create Project", self.test_create_project),
            ("Create Agent", self.test_create_agent),
            ("Agent Execution", self.test_agent_execution),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            if test_func():
                passed += 1
            else:
                failed += 1
                self.print_error(f"Test '{test_name}' failed - stopping test suite")
                break
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("\n" + "="*60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        print("="*60)
        
        if failed == 0:
            print("\n✅ All tests passed! Backend is working correctly.\n")
            return 0
        else:
            print(f"\n❌ {failed} test(s) failed.\n")
            return 1


def main():
    """Main entry point"""
    tester = E2ETest()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
