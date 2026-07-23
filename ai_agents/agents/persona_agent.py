from ai_agents.llm import llm
from ai_agents.models.persona_schema import PersonaOutput
from ai_agents.utils.file_writer import save_output
from ai_agents.utils.safe_llm import extract_json_safe, safe_validate


PERSONA_PROMPT = """
You are a Senior UX Researcher.

Create 3-4 REALISTIC user personas SPECIFIC to the startup idea below.
Each persona must clearly relate to the product's actual target users —
do not invent personas unrelated to this idea's audience.

Return ONLY valid JSON in this exact format:

{{
  "personas": [
    {{
      "name": "string",
      "role": "string",
      "age": 0,
      "context": "string",
      "goals": ["string", "string", "string"],
      "pain_points": ["string", "string", "string"],
      "motivation_quote": "string"
    }}
  ]
}}

REQUIREMENTS

- Return 3 to 4 personas.
- Each persona needs a realistic name, role/occupation, and age appropriate
  to the target users described below.
- Each persona needs 2-4 goals and 2-4 pain points, specific to this product.
- motivation_quote should be a short first-person sentence capturing why
  this persona would want this product.
- Personas should represent DIFFERENT segments of the target audience
  (e.g. different roles, contexts, or use cases), not repeats of the same person.
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

Return ONLY JSON.
"""


def run_persona_agent(idea_result):

    prompt = PERSONA_PROMPT.format(
        product_name=idea_result.product_name,
        category=idea_result.category,
        problem_statement=idea_result.problem_statement,
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

    print("\n===== RAW PERSONA DATA =====")
    print(data)
    print("=============================\n")

    validated = safe_validate(PersonaOutput, data)

    save_output(
        validated.model_dump(),
        "persona_output.json"
    )

    return validated