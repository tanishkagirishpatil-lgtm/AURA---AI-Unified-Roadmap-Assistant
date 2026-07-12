from ai_agents.llm import llm
from ai_agents.models.idea_schema import IdeaOutput
from ai_agents.utils.file_writer import save_output
from ai_agents.utils.safe_llm import extract_json_safe, safe_validate


IDEA_PROMPT = """
Analyze the startup idea.

Return ONLY valid JSON.

{{
  "product_name": "",
  "category": "",
  "target_users": "",
  "confidence_score": 0,
  "problem_statement": "",
  "recommended_solution": "",
  "market_size": "",
  "target_users_count": 0,
  "revenue_model": "",
  "competitor_count": 0,
  "mvp_features_count": 0,
  "market_opportunity_summary": "",
  "next_steps": []
}}

confidence_score must be an integer between 0 and 100.

Startup Idea:
{idea}
"""

def run_idea_agent(user_input: str):

    prompt = IDEA_PROMPT.format(idea=user_input)

    response = llm.invoke(prompt)

    try:
        data = extract_json_safe(response.content)

    except Exception:
        repair_prompt = (
            "Convert the following into valid JSON only. "
            "Do not add explanations.\n\n"
            + response.content
        )

        repaired = llm.invoke(repair_prompt)

        data = extract_json_safe(repaired.content)

    print("\n===== RAW IDEA DATA =====")
    print(data)
    print("========================\n")

    validated = safe_validate(IdeaOutput, data)

    save_output(
        validated.model_dump(),
        "idea_output.json"
    )

    return validated