from ai_agents.llm import llm
from ai_agents.models.prd_schema import PRDOutput
from ai_agents.utils.file_writer import save_output
from ai_agents.utils.safe_llm import extract_json_safe, safe_validate


PRD_PROMPT = """
You are a Senior Product Manager writing a Product Requirements Document.

Generate a complete PRD SPECIFIC to the startup idea, MVP features, and
market context below. Do not write generic filler — every objective,
feature, and user story should clearly relate to this specific product.

Return ONLY valid JSON in this exact format:

{{
  "executive_summary": "string (2-4 sentences)",
  "objectives": ["string", "string", "string"],
  "out_of_scope": ["string", "string"],
  "features": ["string", "string", "string"],
  "user_stories": [
    {{
      "id": "US-001",
      "story": "As a [user], I want to [action], so that [benefit].",
      "acceptance_criteria": "string"
    }}
  ],
  "success_metrics": ["string", "string", "string"]
}}

REQUIREMENTS

- executive_summary: 2-4 sentences summarizing the product, its target
  market, and its core value proposition.
- objectives: at least 4 measurable product objectives (include realistic
  numeric targets where relevant, e.g. user counts, retention %, revenue).
- out_of_scope: at least 2 things explicitly excluded from v1.
- features: at least 5 core v1 features, each a short specific description.
- user_stories: at least 4 user stories in "As a ___, I want to ___, so
  that ___" format, each with a concrete, testable acceptance criteria.
- success_metrics: at least 4 measurable success metrics with realistic
  numeric targets.
- No empty strings. No empty arrays.

STARTUP INFORMATION

Product:
{product_name}

Category:
{category}

Problem:
{problem_statement}

Solution:
{recommended_solution}

Target Users:
{target_users}

Revenue Model:
{revenue_model}

MVP FEATURES (from roadmap)
{mvp_features}

Return ONLY JSON.
"""


def run_prd_agent(idea_result, roadmap_result):

    mvp_features = getattr(roadmap_result, "mvp_features", [])

    prompt = PRD_PROMPT.format(
        product_name=idea_result.product_name,
        category=idea_result.category,
        problem_statement=idea_result.problem_statement,
        recommended_solution=idea_result.recommended_solution,
        target_users=idea_result.target_users,
        revenue_model=idea_result.revenue_model,
        mvp_features=str(mvp_features),
    )

    response = llm.invoke(prompt)

    try:
        data = extract_json_safe(response.content)

    except Exception:
        repair_prompt = f"""
Convert this into VALID JSON only.

No markdown.
No explanation.

{response.content}
"""
        repaired = llm.invoke(repair_prompt)
        data = extract_json_safe(repaired.content)

    print("\n===== RAW PRD DATA =====")
    print(data)
    print("=========================\n")

    validated = safe_validate(PRDOutput, data)

    save_output(
        validated.model_dump(),
        "prd_output.json"
    )

    return validated