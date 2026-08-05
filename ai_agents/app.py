from flask import Flask, request, jsonify
from ai_agents.workflow import workflow
app = Flask(__name__)

@app.get("/")
def home():
    return {"message": "AURA AI Service Running"}

@app.post("/run")
def run_ai():
    try:
        data = request.get_json()

        idea = (
            f"Project: {data.get('title', '')}. "
            f"Industry: {data.get('industry', '')}. "
            f"Audience: {data.get('audience', '')}. "
            f"Problem: {data.get('problem', '')}. "
            f"Vision: {data.get('vision', '')}. "
            f"Goal: {data.get('goal', '')}."
        )

        result = workflow.invoke({"idea": idea})

        output = {
            "success": True,
            "data": {
                "idea": result.get("idea_result").model_dump() if hasattr(result.get("idea_result"), "model_dump") else result.get("idea_result"),
                "market": result.get("market_result").model_dump() if hasattr(result.get("market_result"), "model_dump") else result.get("market_result"),
                "competitor": result.get("competitor_result").model_dump() if hasattr(result.get("competitor_result"), "model_dump") else result.get("competitor_result"),
                "roadmap": result.get("roadmap_result").model_dump() if hasattr(result.get("roadmap_result"), "model_dump") else result.get("roadmap_result"),
                "personas": result.get("persona_result").model_dump() if hasattr(result.get("persona_result"), "model_dump") else result.get("persona_result"),
                "prd": result.get("prd_result").model_dump() if hasattr(result.get("prd_result"), "model_dump") else result.get("prd_result"),
                "legal": result.get("legal_result").model_dump() if hasattr(result.get("legal_result"), "model_dump") else result.get("legal_result"),
            }
        }

        return jsonify(output)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)