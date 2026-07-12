from ai_agents.llm import llm
from ai_agents.models.market_schema import MarketOutput
from ai_agents.utils.file_writer import save_output
from ai_agents.utils.safe_llm import extract_json_safe, safe_validate

MARKET_PROMPT = """
You are a Senior Market Research Analyst.

Analyze the startup idea.

Return ONLY valid JSON.

{{
  "tam": "",
  "sam": "",
  "som": "",

  "growth_rate_by_segment": [
    {{
      "segment": "",
      "growth_rate": ""
    }}
  ],

  "industry_trends": [],

  "market_opportunities": [
    {{
      "title": "",
      "description": ""
    }}
  ],

  "threats_and_risks": [
    {{
      "title": "",
      "description": ""
    }}
  ],

  "market_intelligence_summary": ""
}}

Requirements:

- Estimate realistic TAM, SAM and SOM.
- Provide at least 4 growth segments.
- Provide at least 4 industry trends.
- Provide at least 3 market opportunities.
- Provide at least 3 threats and risks.
- Summary should be concise.

Guidelines:

- Use realistic market estimates.
- TAM, SAM and SOM should be short values like:
  "$8.2B", "$2.1B", "$180M"

- Growth rates should be percentages like:
  "39% CAGR", "22% CAGR", "15% YoY"

- Provide 4–6 industry trends.

- Provide 3–5 market opportunities.

- Provide 3–5 threats and risks.

- Keep every opportunity and threat concise.

Only include competitors that satisfy ALL of the following:

• Solve the same core problem.
• Target similar users.
• Operate in the same product category.
• Are real companies or products.
• Have publicly known websites or products.

If a company is not real or you are unsure, DO NOT include it.

Prefer:
- Market leaders
- Fast-growing startups
- Popular SaaS products

Avoid unrelated productivity tools unless they directly compete.

Startup Idea:
{idea}

Return ONLY JSON.
"""

def run_market_agent(idea: str):

    prompt = MARKET_PROMPT.format(idea=idea)

    response = llm.invoke(prompt)

    try:
        data = extract_json_safe(response.content)

    except Exception:

        repair_prompt = f"""
Convert the following into VALID JSON only.

Return JSON only.
No explanation.
No markdown.

{response.content}
"""

        repaired = llm.invoke(repair_prompt)

        data = extract_json_safe(repaired.content)

    print("\n===== RAW MARKET DATA =====")
    print(data)
    print("==========================\n")

    validated = safe_validate(MarketOutput, data)

    save_output(
        validated.model_dump(),
        "market_output.json"
    )

    return validated