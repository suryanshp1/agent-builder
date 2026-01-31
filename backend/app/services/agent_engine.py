"""
Agent Engine service for executing LangChain agents with observability
"""

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from app.config import settings
from app.models.agent import Agent
from app.models.tool import Tool
from app.services.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ExecutionCallbackHandler(BaseCallbackHandler):
    """
    Custom callback handler for tracking agent execution logs
    """
    
    def __init__(self, execution_id: UUID, log_callback):
        self.execution_id = execution_id
        self.log_callback = log_callback
        self.step_number = 0
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts"""
        self.step_number += 1
        self.log_callback({
            "execution_id": str(self.execution_id),
            "step_number": self.step_number,
            "log_type": "llm_start",
            "log_data": {
                "prompts": prompts,
                "model": serialized.get("name", "unknown")
            }
        })
    
    def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM completes"""
        self.log_callback({
            "execution_id": str(self.execution_id),
            "step_number": self.step_number,
            "log_type": "llm_end",
            "log_data": {
                "generations": str(response.generations),
                "llm_output": response.llm_output
            }
        })
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when tool starts"""
        self.step_number += 1
        self.log_callback({
            "execution_id": str(self.execution_id),
            "step_number": self.step_number,
            "log_type": "tool_start",
            "log_data": {
                "tool": serialized.get("name", "unknown"),
                "input": input_str
            }
        })
    
    def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when tool completes"""
        self.log_callback({
            "execution_id": str(self.execution_id),
            "step_number": self.step_number,
            "log_type": "tool_end",
            "log_data": {
                "output": output
            }
        })
    
    def on_tool_error(self, error: Exception, **kwargs) -> None:
        """Called when tool encounters an error"""
        self.log_callback({
            "execution_id": str(self.execution_id),
            "step_number": self.step_number,
            "log_type": "error",
            "log_data": {
                "error": str(error),
                "error_type": type(error).__name__
            }
        })


class AgentEngine:
    """
    Agent execution engine using LangChain
    """
    
    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        """
        Initialize the agent engine
        
        Args:
            tool_registry: Tool registry instance (will create if not provided)
        """
        self.tool_registry = tool_registry or ToolRegistry()
    
    def create_agent_executor(
        self,
        agent: Agent,
        tools: List[Tool],
        execution_id: UUID,
        log_callback
    ) -> AgentExecutor:
        """
        Create a LangChain AgentExecutor from Agent configuration
        
        Args:
            agent: Agent model instance
            tools: List of Tool model instances
            execution_id: Execution UUID for logging
            log_callback: Callback function for logging
        
        Returns:
            Configured AgentExecutor
        """
        # Initialize LLM
        llm_config = agent.configuration
        llm = ChatOpenAI(
            model=llm_config.get("model", settings.DEFAULT_MODEL),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 2000),
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
        )
        
        # Load tools from registry
        langchain_tools = []
        for tool in tools:
            try:
                lc_tool = self.tool_registry.get_langchain_tool(tool)
                langchain_tools.append(lc_tool)
            except Exception as e:
                logger.error(f"Failed to load tool {tool.name}: {e}")
        
        # Create prompt template
        system_instructions = agent.instructions or ""
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are {agent.role}.

Your goal: {agent.goal}

{system_instructions}

Use the available tools to accomplish your goal. Think step-by-step and explain your reasoning."""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent_instance = create_openai_tools_agent(
            llm=llm,
            tools=langchain_tools,
            prompt=prompt
        )
        
        # Create executor with callback
        callback_handler = ExecutionCallbackHandler(execution_id, log_callback)
        
        executor = AgentExecutor(
            agent=agent_instance,
            tools=langchain_tools,
            callbacks=[callback_handler],
            verbose=True,
            max_iterations=llm_config.get("max_iterations", 10),
            max_execution_time=llm_config.get("max_execution_time", 300),  # 5 minutes
            return_intermediate_steps=True
        )
        
        return executor
    
    async def execute_agent(
        self,
        agent: Agent,
        tools: List[Tool],
        input_data: Dict[str, Any],
        execution_id: UUID,
        log_callback
    ) -> Dict[str, Any]:
        """
        Execute an agent with given input
        
        Args:
            agent: Agent model instance
            tools: List of Tool model instances
            input_data: Input data for the agent
            execution_id: Execution UUID
            log_callback: Callback function for logging
        
        Returns:
            Execution result with output and metadata
        
        Raises:
            Exception: If execution fails
        """
        try:
            # Create executor
            executor = self.create_agent_executor(agent, tools, execution_id, log_callback)
            
            # Execute agent
            result = await executor.ainvoke({
                "input": input_data.get("query", ""),
                "chat_history": input_data.get("chat_history", [])
            })
            
            return {
                "output": result.get("output"),
                "intermediate_steps": result.get("intermediate_steps"),
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            return {
                "output": None,
                "error": str(e),
                "status": "failed"
            }
