"""
roadmap_agent.py

Drop-in replacement for the Roadmap Agent.

WHY THE OLD VERSION HIT 429s / WORKER TIMEOUTS
------------------------------------------------
1. It forwarded the *entire* idea_result / market_result / competitor_result
   objects into the prompt, instead of the handful of fields actually
   needed to write a roadmap.
2. The prompt embedded a full example JSON payload (dozens of lines) on
   every single call, plus a long block of STRICT/MANDATORY prose.
3. On a bad first attempt, it re-sent that entire oversized prompt again
   PLUS an additional "IMPORTANT: previous response was rejected..."
   block -- i.e. the retry was *more* expensive than the original call.
4. On malformed JSON, it made a SECOND full LLM call just to "repair"
   the JSON -- doubling token spend and latency on the unhappy path,
   which is exactly when you're already closest to a rate limit.
5. All of this ran against llama-3.1-8b-instant on Groq, which has a
   fairly tight tokens-per-minute ceiling -- so a single bad request
   (retry + repair) could burn through several multiples of the tokens
   a healthy request would use, tripping 429s and, since the worker sat
   waiting on 2-3 sequential LLM round trips, eventually SIGKILL from
   Render's timeout.

WHAT CHANGED HERE
------------------------------------------------
- Inputs are trimmed to only the fields specified (product name, problem
  statement, target users, revenue model / top trends, opportunities,
  risks / top 3 competitors, market gap, key strengths & weaknesses).
- The prompt no longer contains a full JSON example -- just a compact
  key-by-key spec of the required shape.
- JSON parsing/repair is done LOCALLY (regex + json.loads), never via a
  second LLM call.
- At most one retry, and the retry prompt is a short delta, not a
  duplicate of the full context.
- API failures (including 429s) are handled by falling back to a
  locally-generated minimal-but-valid roadmap instead of retrying the
  network call -- so a rate-limited request never compounds itself.
- Output shape (RoadmapOutput, function signature, return value) is
  unchanged, so nothing else in the project needs to change.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from ai_agents.llm import llm
from ai_agents.models.roadmap_schema import RoadmapOutput
from ai_agents.utils.file_writer import save_output
from ai_agents.utils.safe_llm import extract_json_safe, safe_validate

MAX_ATTEMPTS = 2      # 1 initial call + at most 1 short retry
LLM_CALL_TIMEOUT = 15  # seconds -- hard local cap per Groq call

# By the time this agent runs, Idea/Market/Competitor have already used
# part of the Gunicorn worker's total request timeout. A hung Groq call
# here can silently burn the rest of that budget and get the whole
# worker SIGKILLed (as opposed to a clean, catchable error). This
# wrapper runs the call in a background thread and gives up locally
# after LLM_CALL_TIMEOUT seconds, so a stall degrades to the fallback
# roadmap instead of taking the process down.
# NOTE: this is a safety net, not a substitute for giving Gunicorn a
# large enough --timeout to cover all four sequential agent calls.
_executor = ThreadPoolExecutor(max_workers=4)


def _invoke_with_timeout(prompt: str, timeout: int = LLM_CALL_TIMEOUT):
    future = _executor.submit(llm.invoke, prompt)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        raise TimeoutError(f"Groq call exceeded {timeout}s local timeout")


# =====================================================================
# CONTEXT TRIMMING
# Only the fields we actually use go into the prompt. This is the
# single biggest lever for cutting token usage.
# =====================================================================
def _top_n(value, n=3):
    """Return at most n items from a list-like field, tolerating
    non-list values (strings, None, etc.) from upstream agents."""
    if isinstance(value, list):
        return value[:n]
    if value:
        return [value]
    return []


def _trim_idea(idea_result):
    return {
        "product": getattr(idea_result, "product_name", "") or "Unnamed Product",
        "problem": getattr(idea_result, "problem_statement", ""),
        "users": getattr(idea_result, "target_users", ""),
        "revenue_model": getattr(idea_result, "revenue_model", ""),
    }


def _trim_market(market_result):
    return {
        "trends": _top_n(getattr(market_result, "industry_trends", []), 3),
        "opportunities": _top_n(getattr(market_result, "market_opportunities", []), 3),
        "risks": _top_n(getattr(market_result, "threats_and_risks", []), 3),
    }


def _competitor_name(c):
    if isinstance(c, dict):
        return c.get("name") or c.get("competitor") or str(c)
    return getattr(c, "name", None) or str(c)


def _trim_competitor(competitor_result):
    competitors = getattr(competitor_result, "competitors", []) or []
    top = competitors[:3]

    gaps = getattr(competitor_result, "market_gap_analysis", []) or []
    gap = gaps[0] if isinstance(gaps, list) and gaps else (gaps if gaps else "")

    strengths, weaknesses = [], []
    for c in top:
        if isinstance(c, dict):
            strengths += (c.get("strengths") or [])[:2]
            weaknesses += (c.get("weaknesses") or [])[:2]

    return {
        "top_competitors": [_competitor_name(c) for c in top],
        "market_gap": gap,
        "key_strengths": strengths[:3],
        "key_weaknesses": weaknesses[:3],
    }


# =====================================================================
# PROMPT (compact -- no full JSON example, no repeated instructions)
# =====================================================================
ROADMAP_PROMPT = """You are a Senior Startup Product Manager. Write a startup
execution roadmap SPECIFIC to this product -- no generic filler, every task
must name a real feature or activity from the context below.

IDEA: {idea}
MARKET: {market}
COMPETITOR: {competitor}

Return ONLY valid JSON (no markdown, no prose) with EXACTLY these top-level
keys, nothing else:

executive_summary: {{product, estimated_duration, team_size, launch_strategy}}
development_phases: [>=3 items: {{phase, name, description, start_date, end_date, tasks:[3-6 specific tasks]}}]
sprints: [>=3 items: {{sprint, duration, goals:[]}}]
feature_dependencies: [{{feature, depends_on:[]}}]
milestones: [{{name, week}}]
resource_plan: {{...}}
risk_plan: [>=3 strings]
mvp_features: [>=3 strings]
post_mvp_features: [>=3 strings]
launch_checklist: [>=3 strings]
timeline: {{...}}
priority_matrix: [>=3 items: {{feature, priority, impact, complexity}}]

Rules:
- Every mvp_features item must also appear as a phase task worded "Build <feature>".
- Every post_mvp_features item must appear as a task in a later phase.
- No empty strings, arrays, or objects. No extra/renamed keys.
"""

RETRY_SUFFIX = (
    "\nYour previous reply was invalid or incomplete JSON. "
    "Return corrected, complete JSON only, following the same spec."
)


# =====================================================================
# LOCAL JSON EXTRACTION / REPAIR (no LLM call)
# =====================================================================
def _local_json_repair(text: str):
    """Best-effort local recovery of a JSON object from noisy LLM
    output (stray markdown fences, leading/trailing prose, etc.).
    Never calls the LLM -- purely local string handling."""
    if not text:
        return {}

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    candidate = cleaned[start:end + 1]
    try:
        return json.loads(candidate)
    except Exception:
        return {}


def _parse_llm_json(raw_text: str):
    """Try the shared safe extractor first, then fall back to local
    repair. Never triggers a second LLM call."""
    try:
        data = extract_json_safe(raw_text)
        if isinstance(data, dict) and data:
            return data
    except Exception:
        pass
    return _local_json_repair(raw_text)


# =====================================================================
# NORMALIZER (unchanged shape guarantees, kept lightweight)
# =====================================================================
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
            phase["tasks"] = [str(t) for t in tasks] if isinstance(tasks, list) else []
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


# =====================================================================
# CONSISTENCY GUARANTEE (unchanged logic, no LLM involved)
# =====================================================================
def reconcile_mvp_with_phases(fixed: dict):
    """Ensures the roadmap and MVP plan describe one coherent execution
    plan even if the model didn't perfectly follow the prompt: any
    mvp/post-mvp feature not already named in a phase's tasks gets
    appended as a task to the most appropriate phase."""
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

    build_phase = find_phase(["develop", "build", "mvp"], phases[1] if len(phases) > 1 else phases[0])
    scale_phase = find_phase(["scale", "launch", "growth"], phases[-1])

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


# =====================================================================
# QUALITY CHECK (cheap, local, no LLM)
# =====================================================================
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
        if not isinstance(phase, dict) or len(phase.get("tasks", []) or []) < 2:
            return True

    checks = [
        (data.get("sprints", []), 2),
        (data.get("mvp_features", []), 3),
        (data.get("post_mvp_features", []), 2),
        (data.get("launch_checklist", []), 3),
        (data.get("risk_plan", []), 3),
        (data.get("priority_matrix", []), 3),
    ]
    if any(len(items) < minimum for items, minimum in checks):
        return True

    if not data.get("resource_plan") or not data.get("timeline"):
        return True

    return False


# =====================================================================
# FALLBACK (used only if the LLM call/parse fails entirely -- keeps
# the pipeline alive without ever making another network call)
# =====================================================================
def _fallback_roadmap(idea_context: dict):
    product = idea_context.get("product") or "the product"
    return {
        "executive_summary": {
            "product": product,
            "estimated_duration": "12 weeks",
            "team_size": "Small cross-functional team (3-5 people)",
            "launch_strategy": "Phased rollout starting with a limited beta",
        },
        "development_phases": [
            {
                "phase": 1, "name": "Discovery & Setup",
                "description": "Validate requirements and prepare infrastructure.",
                "start_date": "Week 1", "end_date": "Week 2",
                "tasks": ["Finalize requirements", "Set up project infrastructure", "Define success metrics"],
            },
            {
                "phase": 2, "name": "MVP Development",
                "description": "Build and integrate the core MVP feature set.",
                "start_date": "Week 3", "end_date": "Week 8",
                "tasks": ["Build core MVP features", "Integrate backend services", "Internal QA pass"],
            },
            {
                "phase": 3, "name": "Launch & Scale",
                "description": "Ship the beta and prepare post-MVP work.",
                "start_date": "Week 9", "end_date": "Week 12",
                "tasks": ["Run closed beta", "Collect user feedback", "Plan post-MVP features"],
            },
        ],
        "sprints": [
            {"sprint": 1, "duration": "2 weeks", "goals": ["Requirements & setup"]},
            {"sprint": 2, "duration": "2 weeks", "goals": ["Core feature build"]},
            {"sprint": 3, "duration": "2 weeks", "goals": ["QA and beta launch"]},
        ],
        "feature_dependencies": [],
        "milestones": [
            {"name": "MVP feature-complete", "week": 8},
            {"name": "Beta launch", "week": 9},
        ],
        "resource_plan": {"engineering": "2-3 engineers", "design": "1 designer", "product": "1 PM"},
        "risk_plan": ["Scope creep during MVP build", "Delayed third-party integrations", "Low beta signup rate"],
        "mvp_features": ["Core workflow", "User onboarding", "Basic analytics"],
        "post_mvp_features": ["Advanced analytics", "Integrations marketplace"],
        "launch_checklist": ["QA sign-off", "Beta users onboarded", "Monitoring/alerts live"],
        "timeline": {"start": "Week 1", "launch": "Week 9"},
        "priority_matrix": [
            {"feature": "Core workflow", "priority": "High", "impact": "High", "complexity": "Medium"},
            {"feature": "User onboarding", "priority": "High", "impact": "High", "complexity": "Low"},
            {"feature": "Basic analytics", "priority": "Medium", "impact": "Medium", "complexity": "Low"},
        ],
    }


# =====================================================================
# MAIN AGENT
# =====================================================================
def run_roadmap_agent(idea_result, market_result, competitor_result):
    idea_context = _trim_idea(idea_result)
    market_context = _trim_market(market_result)
    competitor_context = _trim_competitor(competitor_result)

    base_prompt = ROADMAP_PROMPT.format(
        idea=idea_context,
        market=market_context,
        competitor=competitor_context,
    )

    data = {}
    used_fallback = False

    for attempt in range(MAX_ATTEMPTS):
        prompt = base_prompt + (RETRY_SUFFIX if attempt > 0 else "")

        try:
            response = _invoke_with_timeout(prompt)
        except Exception as exc:
            # API failure, rate limit, or local timeout -- do NOT retry
            # the network call. Fall back locally so the pipeline stays up
            # and the Gunicorn worker never has to wait indefinitely.
            print(f"[roadmap_agent] LLM call failed on attempt {attempt + 1}: {exc}")
            data = {}
            used_fallback = True
            break

        data = _parse_llm_json(getattr(response, "content", "") or "")

        if not is_bad_output(data):
            break
    else:
        # Loop finished without a `break` from a good result.
        used_fallback = not data or is_bad_output(data)

    if used_fallback or not data or is_bad_output(data):
        print("[roadmap_agent] Using local fallback roadmap (no further LLM calls).")
        data = _fallback_roadmap(idea_context)

    fixed = normalize_roadmap(data)
    fixed = reconcile_mvp_with_phases(fixed)

    validated = safe_validate(RoadmapOutput, fixed)

    save_output(validated.model_dump(), "roadmap_output.json")

    return validated