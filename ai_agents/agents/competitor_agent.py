from ai_agents.llm import llm
from ai_agents.models.competitor_schema import CompetitorOutput
from ai_agents.utils.file_writer import save_output
from ai_agents.utils.safe_llm import extract_json_safe, safe_validate


COMPETITOR_PROMPT = """
You are an expert startup consultant and market research analyst.

Analyze ONLY the startup described below.

Your task is to identify REAL competitors operating in the SAME industry and solving the SAME problem.

Do NOT invent unrelated companies.
Do NOT use competitors from different industries.
If a startup is niche, return the closest direct competitors.

Use the startup information and market intelligence below.

----------------------------------------
STARTUP INFORMATION
----------------------------------------

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

----------------------------------------
MARKET INTELLIGENCE
----------------------------------------

Market Summary:
{market_intelligence_summary}

Market Opportunities:
{market_opportunities}

Threats:
{threats_and_risks}

----------------------------------------
INSTRUCTIONS
----------------------------------------

• Return 5-6 direct competitors.
• Prefer well-known companies whenever possible.
• Pricing should reflect publicly known pricing where available.
• If pricing is enterprise-based, write:
  "Enterprise Pricing – Custom Quote"
• If pricing is subscription-based, include actual monthly pricing if commonly available.
• If pricing is usage-based, mention "Pay-as-you-go".
• Mention key strengths and weaknesses.
• Mention each competitor's market position.
• Identify EXACTLY 3 market gaps.
• Market gaps must describe opportunities NOT currently served well by competitors.

Return ONLY valid JSON.

{{
  "competitors": [
    {{
      "name": "",
      "region": "",
      "pricing": "",
      "strengths": [],
      "weaknesses": [],
      "market_position": ""
    }}
  ],
  "market_gap_analysis": [
    {{
      "title": "",
      "description": ""
    }}
  ]
}}

Do NOT include markdown.
Do NOT include explanations.
Do NOT include any text outside the JSON.
"""


def run_competitor_agent(idea_result, market_result):

    prompt = COMPETITOR_PROMPT.format(
        product_name=idea_result.product_name,
        category=idea_result.category,
        problem_statement=idea_result.problem_statement,
        recommended_solution=idea_result.recommended_solution,
        target_users=idea_result.target_users,

        market_intelligence_summary=market_result.market_intelligence_summary,
        market_opportunities=market_result.market_opportunities,
        threats_and_risks=market_result.threats_and_risks,
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

    print("\n===== RAW COMPETITOR DATA =====")
    print(data)
    print("===============================\n")

    validated = safe_validate(CompetitorOutput, data)

    save_output(
        validated.model_dump(),
        "competitor_output.json"
    )

    return validated