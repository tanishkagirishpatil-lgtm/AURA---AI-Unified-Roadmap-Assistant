from langgraph.graph import StateGraph, END
from ai_agents.graph_state import StartupState

from ai_agents.agents.idea_agent import run_idea_agent

# ❌ NOT USING THESE FOR NOW (TO SAVE GROQ TOKENS)
# from ai_agents.agents.market_agent import run_market_agent
# from ai_agents.agents.competitor_agent import run_competitor_agent
# from ai_agents.agents.roadmap_agent import run_roadmap_agent


# =========================
# STEP 1: IDEA NODE (ONLY ACTIVE)
# =========================
def idea_node(state):
    result = run_idea_agent(state["idea"])
    return {"idea_result": result}


# =========================
# DISABLED NODES (COMMENTED OUT)
# =========================

# def market_node(state):
#     result = run_market_agent(state["idea_result"])
#     return {"market_result": result}

# def competitor_node(state):
#     result = run_competitor_agent(
#         state["idea_result"],
#         state["market_result"]
#     )
#     return {"competitor_result": result}

# def roadmap_node(state):
#     result = run_roadmap_agent(
#         state["idea_result"],
#         state["market_result"],
#         state["competitor_result"]
#     )
#     return {"roadmap_result": result}


# =========================
# GRAPH BUILD (ONLY IDEA)
# =========================

graph = StateGraph(StartupState)

# ONLY ONE NODE ACTIVE
graph.add_node("idea", idea_node)

# ENTRY POINT
graph.set_entry_point("idea")

# END IMMEDIATELY AFTER IDEA
graph.add_edge("idea", END)

workflow = graph.compile()