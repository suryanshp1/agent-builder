from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitSDK, LangGraphAGUIAgent
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

router = APIRouter()

# --- Basic Agent Definition ---

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]

def call_model(state):
    # This is a placeholder for the actual agent logic
    # In a real implementation, you would use a Language Model here
    return {"messages": [{"role": "assistant", "content": "I am the AgentBuilder Assistant. I can help you configure your agents."}]}

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)
agent_graph = workflow.compile()

# --- Workaround for CopilotKit SDK Issue ---
class FixedLangGraphAgent(LangGraphAGUIAgent):
    def dict_repr(self):
        return {
            "id": self.name,
            "name": self.name,
            "description": self.description,
            "type": "langgraph",
        }

# --- SDK Setup with Protocol Fix ---

class FixedCopilotKitSDK(CopilotKitSDK):
    """Override to return agents as object instead of array for React SDK compatibility"""
    def info(self, *, context):
        result = super().info(context=context)
        # Convert agents array to object keyed by agent name
        if "agents" in result and isinstance(result["agents"], list):
            agents_obj = {agent["name"]: agent for agent in result["agents"]}
            result["agents"] = agents_obj
        return result

sdk = FixedCopilotKitSDK(
    agents=[
        FixedLangGraphAgent(
            name="default",
            description="Helpful assistant for building agents and workflows",
            graph=agent_graph,
        )
    ],
)

add_fastapi_endpoint(router, sdk, "/copilot")
