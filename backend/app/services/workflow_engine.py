"""
Workflow Engine service for multi-agent orchestration using LangGraph
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from typing import TypedDict, Annotated, Sequence, Dict, Any, List
from operator import add
from uuid import UUID
import logging

from app.models.workflow import Workflow
from app.models.agent import Agent
from app.services.agent_engine import AgentEngine
from app.services.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


# Define workflow state
class WorkflowState(TypedDict):
    """State shared across workflow steps"""
    messages: Annotated[Sequence[str], add]
    current_step: int
    step_outputs: Dict[str, Any]
    final_output: Any
    error: str


class WorkflowEngine:
    """
    Workflow execution engine using LangGraph for multi-agent orchestration
    """
    
    def __init__(self):
        self.agent_engine = AgentEngine()
        self.tool_registry = ToolRegistry()
    
    def create_workflow_graph(
        self,
        workflow: Workflow,
        agents_map: Dict[UUID, Agent],
        execution_id: UUID,
        log_callback
    ) -> StateGraph:
        """
        Create a LangGraph workflow from Workflow configuration
        
        Args:
            workflow: Workflow model instance
            agents_map: Dictionary mapping agent IDs to Agent instances
            execution_id: Execution UUID for logging
            log_callback: Callback function for logging
        
        Returns:
            Configured StateGraph
        """
        # Create graph
        graph = StateGraph(WorkflowState)
        
        # Add nodes for each step
        for idx, step_config in enumerate(workflow.steps):
            step_name = step_config.get("name", f"step_{idx}")
            step_type = step_config.get("type")
            
            if step_type == "single_agent":
                # Single agent execution node
                agent_id = UUID(step_config["agent_id"])
                agent = agents_map.get(agent_id)
                
                if not agent:
                    raise ValueError(f"Agent {agent_id} not found for step {step_name}")
                
                # Create node function
                def create_agent_node(agent_inst, step_cfg):
                    async def agent_node(state: WorkflowState) -> WorkflowState:
                        # Map inputs
                        input_mapping = step_cfg.get("input_mapping", {})
                        agent_input = self._map_inputs(input_mapping, state)
                        
                        # Execute agent
                        tools = self.tool_registry.get_tools_for_agent(agent_inst)
                        result = await self.agent_engine.execute_agent(
                            agent=agent_inst,
                            tools=tools,
                            input_data=agent_input,
                            execution_id=execution_id,
                            log_callback=log_callback
                        )
                        
                        # Capture outputs
                        output_vars = step_cfg.get("output_capture", [])
                        for var in output_vars:
                            state["step_outputs"][var] = result.get("output")
                        
                        state["messages"] = state.get("messages", []) + [f"Step {step_cfg['name']}: {result.get('output')}"]
                        state["current_step"] = state.get("current_step", 0) + 1
                        
                        return state
                    
                    return agent_node
                
                graph.add_node(step_name, create_agent_node(agent, step_config))
            
            elif step_type == "conditional":
                # Conditional branch node
                def create_condition_node(step_cfg):
                    def condition_node(state: WorkflowState) -> str:
                        # Evaluate condition
                        condition = step_cfg.get("condition", {})
                        field = condition.get("field")
                        operator = condition.get("operator")
                        value = condition.get("value")
                        
                        # Get field value from state
                        field_value = state["step_outputs"].get(field)
                        
                        # Evaluate
                        if operator == "equals" and field_value == value:
                            return step_cfg.get("true_branch")
                        elif operator == "contains" and value in str(field_value):
                            return step_cfg.get("true_branch")
                        else:
                            return step_cfg.get("false_branch")
                    
                    return condition_node
                
                graph.add_conditional_edges(
                    step_name,
                    create_condition_node(step_config)
                )
            
            elif step_type == "parallel":
                # Parallel agent execution
                agent_ids = [UUID(aid) for aid in step_config.get("agent_ids", [])]
                
                async def parallel_node(state: WorkflowState) -> WorkflowState:
                    # Execute all agents in parallel
                    import asyncio
                    
                    async def run_agent(agent_id):
                        agent = agents_map[agent_id]
                        tools = self.tool_registry.get_tools_for_agent(agent)
                        return await self.agent_engine.execute_agent(
                            agent=agent,
                            tools=tools,
                            input_data=state["step_outputs"],
                            execution_id=execution_id,
                            log_callback=log_callback
                        )
                    
                    results = await asyncio.gather(*[run_agent(aid) for aid in agent_ids])
                    
                    # Aggregate results
                    state["step_outputs"]["parallel_results"] = [r.get("output") for r in results]
                    state["current_step"] = state.get("current_step", 0) + 1
                    
                    return state
                
                graph.add_node(step_name, parallel_node)
        
        # Add edges between sequential steps
        for i in range(len(workflow.steps) - 1):
            current_step = workflow.steps[i].get("name", f"step_{i}")
            next_step = workflow.steps[i + 1].get("name", f"step_{i+1}")
            
            # Only add edge if not a conditional (conditionals define their own edges)
            if workflow.steps[i].get("type") != "conditional":
                graph.add_edge(current_step, next_step)
        
        # Set entry point
        if workflow.steps:
            first_step = workflow.steps[0].get("name", "step_0")
            graph.set_entry_point(first_step)
        
        # Set finish point
        if workflow.steps:
            last_step = workflow.steps[-1].get("name", f"step_{len(workflow.steps)-1}")
            graph.add_edge(last_step, END)
        
        return graph.compile()
    
    def _map_inputs(self, input_mapping: Dict[str, str], state: WorkflowState) -> Dict[str, Any]:
        """
        Map workflow state to agent inputs
        
        Args:
            input_mapping: Mapping configuration
            state: Current workflow state
        
        Returns:
            Mapped input data
        """
        result = {}
        
        for target_key, source_key in input_mapping.items():
            # Support nested keys with dot notation
            if "." in source_key:
                parts = source_key.split(".")
                value = state
                for part in parts:
                    value = value.get(part, {})
            else:
                value = state.get(source_key)
            
            result[target_key] = value
        
        return result
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        agents: List[Agent],
        input_data: Dict[str, Any],
        execution_id: UUID,
        log_callback
    ) -> Dict[str, Any]:
        """
        Execute a workflow
        
        Args:
            workflow: Workflow model instance
            agents: List of Agent instances used in workflow
            input_data: Input data for the workflow
            execution_id: Execution UUID
            log_callback: Callback function for logging
        
        Returns:
            Workflow execution result
        """
        try:
            # Create agents map
            agents_map = {agent.id: agent for agent in agents}
            
            # Create workflow graph
            graph = self.create_workflow_graph(workflow, agents_map, execution_id, log_callback)
            
            # Initialize state
            initial_state = WorkflowState(
                messages=[],
                current_step=0,
                step_outputs=input_data,
                final_output=None,
                error=""
            )
            
            # Execute workflow
            final_state = await graph.ainvoke(initial_state)
            
            return {
                "status": "success",
                "output": final_state.get("final_output") or final_state.get("step_outputs"),
                "messages": final_state.get("messages", [])
            }
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
