"""
Tool Registry service for loading and managing tools
"""

from langchain_core.tools import StructuredTool
from langchain.tools import tool
from typing import Dict, Any, List
import requests
import logging

from app.config import settings
from app.models.tool import Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Tool registry for loading tools from database and converting to LangChain tools
    """
    
    def __init__(self):
        self.loaded_tools: Dict[str, StructuredTool] = {}
    
    def get_langchain_tool(self, tool_model: Tool) -> StructuredTool:
        """
        Convert Tool model to LangChain Tool
        
        Args:
            tool_model: Tool database model
        
        Returns:
            LangChain Tool instance
        
        Raises:
            ValueError: If tool type is unsupported
        """
        tool_id = str(tool_model.id)
        
        # Check cache
        if tool_id in self.loaded_tools:
            return self.loaded_tools[tool_id]
        
        # Create tool based on type
        if tool_model.type == "prebuilt":
            lc_tool = self._load_prebuilt_tool(tool_model)
        elif tool_model.type == "custom_python":
            lc_tool = self._load_python_tool(tool_model)
        elif tool_model.type == "api":
            lc_tool = self._load_api_tool(tool_model)
        else:
            raise ValueError(f"Unsupported tool type: {tool_model.type}")
        
        # Cache tool
        self.loaded_tools[tool_id] = lc_tool
        
        return lc_tool
    
    def get_tools_for_agent(self, agent) -> List[StructuredTool]:
        """
        Get all tools for an agent from database
        
        Args:
            agent: Agent model instance
        
        Returns:
            List of LangChain Tool instances
        """
        from app.database import SessionLocal
        from app.models.tool import Tool as ToolModel
        
        db = SessionLocal()
        try:
            tools = db.query(ToolModel).filter(ToolModel.id.in_(agent.tool_ids)).all()
            return [self.get_langchain_tool(tool) for tool in tools]
        finally:
            db.close()
    
    def _load_prebuilt_tool(self, tool_model: Tool) -> StructuredTool:
        """Load a prebuilt tool"""
        tool_name = tool_model.name
        
        if tool_name == "web_search":
            return self._create_web_search_tool()
        elif tool_name == "calculator":
            return self._create_calculator_tool()
        elif tool_name == "file_reader":
            return self._create_file_reader_tool()
        elif tool_name == "current_time":
            return self._create_current_time_tool()
        else:
            raise ValueError(f"Unknown prebuilt tool: {tool_name}")
    
    def _load_python_tool(self, tool_model: Tool) -> StructuredTool:
        """Load a custom Python tool"""
        code = tool_model.implementation.get("code", "")
        
        # Create a function from code (sandboxed execution would be needed in production)
        exec_globals = {}
        exec(code, exec_globals)
        
        tool_func = exec_globals.get("execute")
        if not tool_func:
            raise ValueError("Python tool must define an 'execute' function")
        
        return StructuredTool.from_function(
            name=tool_model.name,
            description=tool_model.description,
            func=tool_func
        )
    
    def _load_api_tool(self, tool_model: Tool) -> StructuredTool:
        """Load an API-based tool"""
        impl = tool_model.implementation
        method = impl.get("method", "POST")
        url = impl.get("url")
        headers = impl.get("headers", {})
        
        def api_call(input_data: str) -> str:
            """Make API call"""
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json={"input": input_data},
                    timeout=30
                )
                response.raise_for_status()
                return response.text
            except Exception as e:
                return f"API call failed: {str(e)}"
        
        return StructuredTool.from_function(
            name=tool_model.name,
            description=tool_model.description,
            func=api_call
        )
    
    def _create_web_search_tool(self) -> StructuredTool:
        """Create Serper web search tool"""
        
        @tool
        def web_search(query: str) -> str:
            """
            Search the web using Google Serper API
            
            Args:
                query: Search query string
            
            Returns:
                Search results as formatted string
            """
            try:
                url = "https://google.serper.dev/search"
                headers = {
                    "X-API-KEY": settings.SERPER_API_KEY,
                    "Content-Type": "application/json"
                }
                payload = {
                    "q": query,
                    "num": 5
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                results = []
                
                # Format organic results
                for item in data.get("organic", [])[:5]:
                    results.append(f"**{item.get('title')}**\n{item.get('snippet')}\nURL: {item.get('link')}\n")
                
                return "\n".join(results) if results else "No results found"
            
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                return f"Search failed: {str(e)}"
        
        return web_search
    
    def _create_calculator_tool(self) -> StructuredTool:
        """Create calculator tool"""
        
        @tool
        def calculator(expression: str) -> str:
            """
            Evaluate a mathematical expression
            
            Args:
                expression: Mathematical expression to evaluate
            
            Returns:
                Calculation result or error message
            """
            try:
                # Safe eval with limited builtins
                allowed_names = {
                    "abs": abs, "round": round, "min": min, "max": max,
                    "sum": sum, "pow": pow
                }
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                return str(result)
            except Exception as e:
                return f"Calculation error: {str(e)}"
        
        return calculator
    
    def _create_file_reader_tool(self) -> StructuredTool:
        """Create file reader tool"""
        
        @tool
        def file_reader(file_path: str) -> str:
            """
            Read the contents of a text file
            
            Args:
                file_path: Path to the file to read
            
            Returns:
                File contents or error message
            """
            try:
                import os
                
                # Security: Only allow reading from /tmp or specific directories
                allowed_dirs = ["/tmp", "./data"]
                is_allowed = any(file_path.startswith(d) for d in allowed_dirs)
                
                if not is_allowed:
                    return f"Error: Access denied. Only files in {allowed_dirs} can be read."
                
                if not os.path.exists(file_path):
                    return f"Error: File not found: {file_path}"
                
                # Read file with size limit (1MB)
                max_size = 1024 * 1024
                file_size = os.path.getsize(file_path)
                
                if file_size > max_size:
                    return f"Error: File too large ({file_size} bytes). Maximum size is {max_size} bytes."
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return content
            
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        return file_reader
    
    def _create_current_time_tool(self) -> StructuredTool:
        """Create current time tool"""
        
        @tool
        def current_time(timezone: str = "UTC") -> str:
            """
            Get the current date and time
            
            Args:
                timezone: Timezone name (default: UTC)
            
            Returns:
                Current date and time as string
            """
            try:
                from datetime import datetime
                import pytz
                
                tz = pytz.timezone(timezone)
                now = datetime.now(tz)
                
                return now.strftime("%Y-%m-%d %H:%M:%S %Z")
            
            except Exception as e:
                # Fallback to UTC
                from datetime import datetime
                return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return current_time
    

def initialize_prebuilt_tools(db_session) -> List[Tool]:
    """
    Initialize prebuilt global tools in database
    
    Args:
        db_session: SQLAlchemy session
    
    Returns:
        List of created Tool instances
    """
    prebuilt_tools = [
        {
            "name": "web_search",
            "description": "Search the web for current information using Google Serper API",
            "category": "research",
            "type": "prebuilt",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            },
            "output_schema": {
                "type": "string",
                "description": "Search results as formatted text"
            },
            "implementation": {"builtin": "web_search"},
            "is_global": True
        },
        {
            "name": "calculator",
            "description": "Perform mathematical calculations",
            "category": "data",
            "type": "prebuilt",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression"}
                },
                "required": ["expression"]
            },
            "output_schema": {
                "type": "string",
                "description": "Calculation result"
            },
            "implementation": {"builtin": "calculator"},
            "is_global": True
        },
        {
            "name": "file_reader",
            "description": "Read the contents of a text file from allowed directories",
            "category": "data",
            "type": "prebuilt",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["file_path"]
            },
            "output_schema": {
                "type": "string",
                "description": "File contents or error message"
            },
            "implementation": {"builtin": "file_reader"},
            "is_global": True
        },
        {
            "name": "current_time",
            "description": "Get the current date and time in a specified timezone",
            "category": "data",
            "type": "prebuilt",
            "input_schema": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Timezone name (e.g., UTC, America/New_York)", "default": "UTC"}
                }
            },
            "output_schema": {
                "type": "string",
                "description": "Current date and time as formatted string"
            },
            "implementation": {"builtin": "current_time"},
            "is_global": True
        }
    ]
    
    created_tools = []
    
    for tool_data in prebuilt_tools:
        # Check if tool already exists
        existing = db_session.query(Tool).filter(Tool.name == tool_data["name"]).first()
        
        if not existing:
            tool = Tool(**tool_data)
            db_session.add(tool)
            created_tools.append(tool)
            logger.info(f"Created prebuilt tool: {tool_data['name']}")
    
    if created_tools:
        db_session.commit()
    
    return created_tools
