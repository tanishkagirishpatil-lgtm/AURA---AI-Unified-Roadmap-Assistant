from ai_agents.llm import llm
from ai_agents.models.legal_schema import LegalOutput
from ai_agents.utils.file_writer import save_output
from ai_agents.utils.safe_llm import extract_json_safe, safe_validate


LEGAL_PROMPT = """
You are a startup legal readiness advisor (not a lawyer — general guidance only).

Assess IP and legal readiness SPECIFIC to the startup idea below.

Return ONLY valid JSON in this exact format:

{{
  "readiness_score": 0,
  "readiness_label": "string (e.g. Good, Needs Work, At Risk)",
  "summary": "string (1-2 sentences)",
  "trademark_checklist": [
    {{ "text": "string", "status": "ok", "note": "string" }}
  ],
  "copyright_checklist": [
    {{ "text": "string", "status": "ok", "note": "string" }}
  ],
  "patent_checklist": [
    {{ "text": "string", "status": "ok", "note": "string" }}
  ]
}}

REQUIREMENTS

- readiness_score: an integer 0-100 reflecting overall legal readiness
  for a startup at MVP/pre-launch stage.
- status must be one of exactly: "ok", "warn", "risk"
- trademark_checklist: at least 3 items relevant to protecting THIS
  product's brand name and identity.
- copyright_checklist: at least 3 items relevant to THIS product's
  content, code, and data (e.g. privacy policy, third-party licenses).
- patent_checklist: at least 3 items assessing whether THIS product's
  core technical approach may be patentable, and next steps.
- Ground every item in specifics of the idea below (e.g. reference the
  product category, core algorithm, or data handling approach), not
  generic boilerplate.
- No empty strings. No empty arrays.

STARTUP INFORMATION

Product:
{product_name}

Category:
{category}

Solution:
{recommended_solution}

Target Users:
{target_users}

Return ONLY JSON.
"""


def run_legal_agent(idea_result):

    prompt = LEGAL_PROMPT.format(
        product_name=idea_result.product_name,
        category=idea_result.category,
        recommended_solution=idea_result.recommended_solution,
        target_users=idea_result.target_users,
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

    print("\n===== RAW LEGAL DATA =====")
    print(data)
    print("===========================\n")

    validated = safe_validate(LegalOutput, data)

    save_output(
        validated.model_dump(),
        "legal_output.json"
    )

    return validated