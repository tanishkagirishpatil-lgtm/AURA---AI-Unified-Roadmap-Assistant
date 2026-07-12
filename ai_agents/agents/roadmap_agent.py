from ai_agents.llm import llm
from ai_agents.models.roadmap_schema import RoadmapOutput
from ai_agents.utils.file_writer import save_output
from ai_agents.utils.safe_llm import extract_json_safe, safe_validate


# -----------------------------
# NORMALIZER
# -----------------------------
def normalize_roadmap(data: dict):
    if not isinstance(data, dict):
        return {}

    def safe_list(value):
        if isinstance(value, list):
            return [
                item if isinstance(item, dict) else {"value": str(item)}
                for item in value
            ]
        return []

    def safe_dict(value):
        return value if isinstance(value, dict) else {}

    return {
        "executive_summary": safe_dict(data.get("executive_summary")),
        "development_phases": safe_list(data.get("development_phases")),
        "sprints": safe_list(data.get("sprints")),
        "feature_dependencies": safe_list(data.get("feature_dependencies")),
        "milestones": safe_list(data.get("milestones")),
        "resource_plan": safe_dict(data.get("resource_plan")),
        "risk_plan": safe_list(data.get("risk_plan")),
        "mvp_features": safe_list(data.get("mvp_features")),
        "post_mvp_features": safe_list(data.get("post_mvp_features")),
        "launch_checklist": safe_list(data.get("launch_checklist")),
        "timeline": safe_dict(data.get("timeline")),
        "priority_matrix": safe_list(data.get("priority_matrix")),
    }

# -----------------------------
# PROMPT
# -----------------------------
ROADMAP_PROMPT = """
You are a Senior Startup Product Manager.

Generate a complete startup execution roadmap.

JSON FORMAT MUST FOLLOW EXACTLY:

{{
  "executive_summary": {{
    "product": "string",
    "estimated_duration": "string",
    "team_size": "string",
    "launch_strategy": "string"
  }},
  "development_phases": [],
  "sprints": [
    {{
      "sprint": 1,
      "duration": "2 weeks",
      "goals": ["goal1", "goal2"]
    }}
  ],
  "feature_dependencies": [
    {{
      "feature": "string",
      "depends_on": ["string"]
    }}
  ],
  "milestones": [
    {{
      "name": "string",
      "week": 1
    }}
  ],
  "resource_plan": {{}},
  "risk_plan": [],
  "mvp_features": [],
  "post_mvp_features": [],
  "launch_checklist": [],
  "timeline": {{}},
  "priority_matrix": [
    {{
      "feature": "string",
      "priority": "High",
      "impact": "High",
      "complexity": "Medium"
    }}
  ]
}}

STRICT REQUIREMENTS

- Return ONLY valid JSON
- No markdown
- No explanations
- Use EXACT field names shown above
- Do NOT create product_name
- Do NOT create summary
- Do NOT create sprint_name
- Do NOT create milestone_name
- No empty strings
- No empty arrays
- No empty objects

MANDATORY

- executive_summary fully populated
- minimum 3 development phases
- minimum 3 sprints
- minimum 5 MVP features
- minimum 3 risks
- non-empty resource_plan
- non-empty timeline
- non-empty priority_matrix

IDEA:
{idea}

MARKET:
{market}

COMPETITOR:
{competitor}

Return ONLY JSON.
"""

# -----------------------------
# QUALITY CHECK
# -----------------------------
def is_bad_output(data: dict):

    if not isinstance(data, dict):
        return True

    executive = data.get("executive_summary", {})

    required_exec = [
        executive.get("product"),
        executive.get("estimated_duration"),
        executive.get("team_size"),
        executive.get("launch_strategy"),
    ]

    if any(not value for value in required_exec):
        return True

    if len(data.get("development_phases", [])) < 3:
        return True

    if len(data.get("sprints", [])) < 3:
        return True

    if len(data.get("mvp_features", [])) < 5:
        return True

    if len(data.get("risk_plan", [])) < 3:
        return True

    if len(data.get("priority_matrix", [])) < 3:
        return True

    if not data.get("resource_plan"):
        return True

    if not data.get("timeline"):
        return True

    return False


# -----------------------------
# MAIN AGENT
# -----------------------------
def run_roadmap_agent(
    idea_result,
    market_result,
    competitor_result
):

    idea_context = {
        "product_name": getattr(
            idea_result,
            "product_name",
            ""
        ),
        "summary": getattr(
            idea_result,
            "summary",
            ""
        ),
        "target_users": getattr(
            idea_result,
            "target_users",
            []
        )
    }

    market_context = {
        "market_gaps": getattr(
            market_result,
            "market_gaps",
            []
        ),
        "risks": getattr(
            market_result,
            "risks",
            []
        )
    }

    competitor_context = {
        "opportunity_gaps": getattr(
            competitor_result,
            "opportunity_gaps",
            []
        ),
        "weaknesses": getattr(
            competitor_result,
            "weaknesses",
            []
        )
    }

    prompt = ROADMAP_PROMPT.format(
        idea=str(idea_context),
        market=str(market_context),
        competitor=str(competitor_context)
    )

    data = {}

    for attempt in range(5):

        current_prompt = prompt

        if attempt > 0:
            current_prompt += """

IMPORTANT:

Previous response was rejected.

You MUST:
- fill every field
- return at least 3 phases
- return at least 3 sprints
- return at least 5 MVP features
- return at least 3 risks
- return resource_plan
- return timeline
- return priority_matrix

No empty strings.
No empty arrays.
No empty objects.

Return ONLY valid JSON.
"""

        response = llm.invoke(current_prompt)

        try:
            data = extract_json_safe(response.content)

        except Exception:

            repaired = llm.invoke(
                f"Convert the following into valid JSON only:\n\n{response.content}"
            )

            data = extract_json_safe(
                repaired.content
            )

        if not is_bad_output(data):
            break

    fixed = normalize_roadmap(data)

    print("\n===== RAW ROADMAP DATA =====")
    print(fixed)
    print("===========================\n")

    validated = safe_validate(
        RoadmapOutput,
        fixed
    )

    save_output(
        validated.model_dump(),
        "roadmap_output.json"
    )

    return validated