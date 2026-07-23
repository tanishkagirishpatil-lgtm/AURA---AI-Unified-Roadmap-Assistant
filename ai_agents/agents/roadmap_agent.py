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

    def safe_phases(value):
        phases = safe_list(value)
        for phase in phases:
            tasks = phase.get("tasks")
            if not isinstance(tasks, list) or not tasks:
                phase["tasks"] = []
            else:
                phase["tasks"] = [str(t) for t in tasks]
        return phases

    return {
        "executive_summary": safe_dict(data.get("executive_summary")),
        "development_phases": safe_phases(data.get("development_phases")),
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
# CONSISTENCY GUARANTEE
# -----------------------------
def reconcile_mvp_with_phases(fixed: dict):
    """
    Guarantees the Roadmap and MVP plan describe one coherent execution
    plan, even if the model didn't perfectly follow the prompt's
    consistency instructions. Any mvp_feature / post_mvp_feature that
    isn't already named in some phase's tasks gets appended as a task
    to the most appropriate phase.
    """
    phases = fixed.get("development_phases", [])
    if not phases:
        return fixed

    def feature_name(item):
        if isinstance(item, dict):
            return item.get("feature") or item.get("value") or ""
        return str(item)

    def find_phase(keywords, fallback):
        for p in phases:
            name = str(p.get("name", "")).lower()
            if any(kw in name for kw in keywords):
                return p
        return fallback

    build_phase = find_phase(
        ["develop", "build", "mvp"],
        phases[1] if len(phases) > 1 else phases[0]
    )
    scale_phase = find_phase(
        ["scale", "launch", "growth"],
        phases[-1]
    )

    def ensure_tasks(p):
        if not isinstance(p.get("tasks"), list):
            p["tasks"] = []

    ensure_tasks(build_phase)
    ensure_tasks(scale_phase)

    existing_build = " | ".join(str(t).lower() for t in build_phase["tasks"])
    for item in fixed.get("mvp_features", []):
        name = feature_name(item)
        if name and name.lower() not in existing_build:
            build_phase["tasks"].append(f"Build {name}")

    existing_scale = " | ".join(str(t).lower() for t in scale_phase["tasks"])
    for item in fixed.get("post_mvp_features", []):
        name = feature_name(item)
        if name and name.lower() not in existing_scale:
            scale_phase["tasks"].append(f"Build {name}")

    return fixed

# -----------------------------
# PROMPT
# -----------------------------
ROADMAP_PROMPT = """
You are a Senior Startup Product Manager.

Generate a complete startup execution roadmap SPECIFIC to the idea, market, and
competitor information given below. Do not produce generic filler — every phase,
task, sprint, feature, and risk should clearly relate to this specific product.

JSON FORMAT MUST FOLLOW EXACTLY:

{{
  "executive_summary": {{
    "product": "string",
    "estimated_duration": "string",
    "team_size": "string",
    "launch_strategy": "string"
  }},
  "development_phases": [
    {{
      "phase": 1,
      "name": "string",
      "description": "string (1-2 sentence summary of this phase's goal)",
      "start_date": "string",
      "end_date": "string",
      "tasks": ["Build <specific MVP feature name>", "Implement <specific MVP feature name>", "other concrete task"]
    }}
  ],
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
- EVERY development phase must include a "tasks" array with 3 to 6
  concrete, specific, actionable tasks for that phase (not vague
  restatements of the phase name — real to-do items someone could
  check off, e.g. "Set up CI/CD pipeline", "Conduct 10 user interviews",
  "Finalize payment gateway integration")
- minimum 5 MVP features
- minimum 3 post-MVP features
- CONSISTENCY REQUIREMENT (critical): the roadmap and the MVP plan you
  generate in this same response must describe ONE coherent execution
  plan, not two unrelated lists.
  * Every single item in "mvp_features" MUST appear as a task in one
    of the development phases (typically the build/development phase),
    phrased as an implementation task — e.g. if mvp_features includes
    "AI Skill Gap Analyzer", a phase task must say something like
    "Build AI Skill Gap Analyzer" or "Implement AI Skill Gap Analyzer
    (core algorithm + UI)".
  * Every item in "post_mvp_features" should similarly map to a task
    in a later phase (e.g. the scale/post-launch phase).
  * Do not invent generic phase tasks (like "build core features")
    that don't name a specific feature from your own mvp_features or
    post_mvp_features lists — name the actual feature in the task.
- minimum 3 sprints
- minimum 3 launch checklist items
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

    phases = data.get("development_phases", [])

    if len(phases) < 3:
        return True

    for phase in phases:
        if not isinstance(phase, dict):
            return True
        if len(phase.get("tasks", []) or []) < 2:
            return True

    if len(data.get("sprints", [])) < 3:
        return True

    if len(data.get("mvp_features", [])) < 5:
        return True

    if len(data.get("post_mvp_features", [])) < 3:
        return True

    if len(data.get("launch_checklist", [])) < 3:
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

    # These use the REAL field names from each schema (idea_schema,
    # market_schema, competitor_schema) — earlier versions of this
    # function referenced nonexistent fields like "summary",
    # "market_gaps", "risks", "opportunity_gaps", "weaknesses", which
    # always returned empty defaults and left this agent working
    # almost blind.
    idea_context = {
        "product_name": getattr(idea_result, "product_name", ""),
        "category": getattr(idea_result, "category", ""),
        "problem_statement": getattr(idea_result, "problem_statement", ""),
        "recommended_solution": getattr(idea_result, "recommended_solution", ""),
        "target_users": getattr(idea_result, "target_users", ""),
        "revenue_model": getattr(idea_result, "revenue_model", ""),
        "mvp_features_count": getattr(idea_result, "mvp_features_count", 0),
        "next_steps": getattr(idea_result, "next_steps", []),
    }

    market_context = {
        "tam": getattr(market_result, "tam", ""),
        "sam": getattr(market_result, "sam", ""),
        "som": getattr(market_result, "som", ""),
        "industry_trends": getattr(market_result, "industry_trends", []),
        "market_opportunities": getattr(market_result, "market_opportunities", []),
        "threats_and_risks": getattr(market_result, "threats_and_risks", []),
    }

    competitor_context = {
        "competitors": getattr(competitor_result, "competitors", []),
        "market_gap_analysis": getattr(competitor_result, "market_gap_analysis", []),
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
- give EVERY phase a "tasks" array with 3-6 specific, actionable tasks
- make sure every mvp_feature and post_mvp_feature is named explicitly
  inside a phase task (e.g. "Build <feature name>") — the roadmap and
  MVP plan must be ONE consistent plan, not two unrelated lists
- return at least 3 sprints
- return at least 5 MVP features
- return at least 3 post-MVP features
- return at least 3 launch checklist items
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
    fixed = reconcile_mvp_with_phases(fixed)

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