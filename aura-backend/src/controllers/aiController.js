const { runPythonAI } = require("../services/aiService");
const db = require("../config/db");

const runAI = async (req, res) => {
  try {

    const ideaId = req.body.ideaId || req.body.id;

    // 🔥 STEP 1 DEBUG
    console.log("REQ BODY:", req.body);

    if (!ideaId) {
      return res.status(400).json({
        success: false,
        error: "ideaId is required"
      });
    }

    // fetch idea from DB
    const [rows] = await db.execute(
      "SELECT * FROM ideas WHERE id = ?",
      [ideaId]
    );

    if (!rows.length) {
      return res.status(404).json({
        success: false,
        error: "Idea not found"
      });
    }

    const idea = rows[0];

    console.log("🟡 Running AI for:", idea.title);

    const result = await runPythonAI({
      title: idea.title,
      problem: idea.problem,
      industry: idea.industry,
      audience: idea.target_audience,
      vision: idea.vision,
      goal: idea.primary_goal
    });

    console.log("✅ AI complete");

    // 🔥 The Python process can exit with code 0 but still report an
    // internal failure (e.g. one of the agents threw an exception).
    // Check that explicitly instead of assuming success.
    if (!result || result.success === false) {
      console.error("❌ AI pipeline reported failure:", result?.error);
      return res.status(500).json({
        success: false,
        error: result?.error || "AI pipeline failed with no error message"
      });
    }

    // Save the AI results back to the idea row so the dashboard
    // reflects real data on reload (instead of null/0%)
    await db.execute(
      "UPDATE ideas SET ai_results = ? WHERE id = ?",
      [JSON.stringify(result), ideaId]
    );

    return res.json({
      success: true,
      data: result
    });

  } catch (err) {
    console.error("❌ AI Controller Error:", err);

    return res.status(500).json({
      success: false,
      error: err.toString()
    });
  }
};

module.exports = { runAI };