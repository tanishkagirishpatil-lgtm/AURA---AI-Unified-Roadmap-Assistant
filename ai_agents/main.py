import sys
import json
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from workflow import workflow

def main():
    idea = sys.argv[1] if len(sys.argv) > 1 else input("Enter your startup idea: ")

    try:
        result = workflow.invoke({"idea": idea})

        roadmap_result = result.get("roadmap_result")
        market_result  = result.get("market_result")
        competitor_result = result.get("competitor_result")
        idea_result    = result.get("idea_result")
        persona_result = result.get("persona_result")
        prd_result     = result.get("prd_result")
        legal_result   = result.get("legal_result")

        output = {
            "success": True,
            "data": {
                "idea":       idea_result.model_dump()       if hasattr(idea_result, "model_dump")       else idea_result,
                "market":     market_result.model_dump()     if hasattr(market_result, "model_dump")     else market_result,
                "competitor": competitor_result.model_dump() if hasattr(competitor_result, "model_dump") else competitor_result,
                "roadmap":    roadmap_result.model_dump()    if hasattr(roadmap_result, "model_dump")    else roadmap_result,
                "personas":   persona_result.model_dump()    if hasattr(persona_result, "model_dump")    else persona_result,
                "prd":        prd_result.model_dump()        if hasattr(prd_result, "model_dump")        else prd_result,
                "legal":      legal_result.model_dump()      if hasattr(legal_result, "model_dump")      else legal_result,
            }
        }

    except Exception as e:
        output = {
            "success": False,
            "error": str(e)
        }

    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()