import os
from typing import TypedDict, List, Dict, Any, Callable, Awaitable
from langgraph.graph import StateGraph, END
from backend.agents.ideator import ideate_node
from backend.agents.builder import build_node
from backend.agents.reviewer import review_node

class GraphState(TypedDict):
    prompt: str
    current_code: Dict[str, str]
    plan: Dict[str, Any]
    html: str
    css: str
    js: str
    issues: List[str]
    iterations: int
    max_iterations: int
    
    # Callbacks for streaming UI
    emit_log: Callable[[str, str, Any], Awaitable[None]]
    emit_code: Callable[[str, str, str], Awaitable[None]]
    emit_preview_reload: Callable[[], Awaitable[None]]
    preview_dir: str

async def github_issue_node(state: GraphState):
    await state["emit_log"]("System", "Found issues. Pretending to create GitHub issue...", details=state["issues"])
    # Mocking GitHub issue creation
    return {"iterations": state["iterations"] + 1}

def should_continue(state: GraphState):
    if len(state.get("issues", [])) > 0 and state.get("iterations", 0) < state.get("max_iterations", 3):
        return "github_issue"
    return END

async def run_generation_graph(prompt: str, current_code: Dict[str, str], emit_log, emit_code, emit_preview_reload, preview_dir: str):
    workflow = StateGraph(GraphState)
    
    workflow.add_node("ideator", ideate_node)
    workflow.add_node("builder", build_node)
    workflow.add_node("reviewer", review_node)
    workflow.add_node("github_issue", github_issue_node)
    
    workflow.set_entry_point("ideator")
    
    workflow.add_edge("ideator", "builder")
    workflow.add_edge("builder", "reviewer")
    
    workflow.add_conditional_edges("reviewer", should_continue, {
        "github_issue": "github_issue",
        END: END
    })
    
    workflow.add_edge("github_issue", "ideator")
    
    app = workflow.compile()
    
    initial_state = {
        "prompt": prompt,
        "current_code": current_code,
        "plan": {},
        "html": "",
        "css": "",
        "js": "",
        "issues": [],
        "iterations": 0,
        "max_iterations": 3,
        "emit_log": emit_log,
        "emit_code": emit_code,
        "emit_preview_reload": emit_preview_reload,
        "preview_dir": preview_dir
    }
    
    # We await the whole execution, which inside will await nodes
    await app.ainvoke(initial_state)
