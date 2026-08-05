from langgraph.graph import StateGraph, END
from ai_agents.graph_state import StartupState

from ai_agents.agents.idea_agent import run_idea_agent
from ai_agents.agents.market_agent import run_market_agent
from ai_agents.agents.competitor_agent import run_competitor_agent
from ai_agents.agents.roadmap_agent import run_roadmap_agent
from ai_agents.agents.persona_agent import run_persona_agent
from ai_agents.agents.prd_agent import run_prd_agent
from ai_agents.agents.legal_agent import run_legal_agent


def idea_node(state):
    print("🚀 Running Idea Agent...", flush=True)
    result = run_idea_agent(state["idea"])
    print("✅ Idea Agent Finished", flush=True)
    return {"idea_result": result}


def market_node(state):
    print("🚀 Running Market Agent...", flush=True)
    result = run_market_agent(state["idea"])
    print("✅ Market Agent Finished", flush=True)
    return {"market_result": result}


def competitor_node(state):
    print("🚀 Running Competitor Agent...", flush=True)
    result = run_competitor_agent(
        state["idea_result"],
        state["market_result"]
    )
    print("✅ Competitor Agent Finished", flush=True)
    return {"competitor_result": result}


def roadmap_node(state):
    print("🚀 Running Roadmap Agent...", flush=True)
    result = run_roadmap_agent(
        state["idea_result"],
        state["market_result"],
        state["competitor_result"]
    )
    print("✅ Roadmap Agent Finished", flush=True)
    return {"roadmap_result": result}


def persona_node(state):
    print("🚀 Running Persona Agent...", flush=True)
    result = run_persona_agent(state["idea_result"])
    print("✅ Persona Agent Finished", flush=True)
    return {"persona_result": result}


def prd_node(state):
    print("🚀 Running PRD Agent...", flush=True)
    result = run_prd_agent(
        state["idea_result"],
        state["roadmap_result"]
    )
    print("✅ PRD Agent Finished", flush=True)
    return {"prd_result": result}


def legal_node(state):
    print("🚀 Running Legal Agent...", flush=True)
    result = run_legal_agent(state["idea_result"])
    print("✅ Legal Agent Finished", flush=True)
    return {"legal_result": result}


graph = StateGraph(StartupState)

graph.add_node("idea", idea_node)
graph.add_node("market", market_node)
graph.add_node("competitor", competitor_node)
graph.add_node("roadmap", roadmap_node)
graph.add_node("persona", persona_node)
graph.add_node("prd", prd_node)
graph.add_node("legal", legal_node)

graph.set_entry_point("idea")

# ── PARALLEL FAN-OUT ──────────────────────────────────────────
# persona and legal only need idea_result, so they run concurrently
# with the market -> competitor -> roadmap -> prd chain instead of
# waiting for it to finish. This cuts wall-clock time noticeably
# since persona + legal (2 LLM calls) now overlap with the 4-call
# chain instead of adding 2 more sequential calls after it.
graph.add_edge("idea", "market")
graph.add_edge("idea", "persona")
graph.add_edge("idea", "legal")

graph.add_edge("market", "competitor")
graph.add_edge("competitor", "roadmap")
graph.add_edge("roadmap", "prd")

graph.add_edge("prd", END)
graph.add_edge("persona", END)
graph.add_edge("legal", END)

workflow = graph.compile()

