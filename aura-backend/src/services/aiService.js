const axios = require("axios");

const runPythonAI = async (ideaData) => {
  try {
    const AI_URL = process.env.AI_SERVICE_URL;

    if (!AI_URL) {
      throw new Error("AI_SERVICE_URL is not configured.");
    }

    const response = await axios.post(`${AI_URL}/run`, {
      title: ideaData.title,
      industry: ideaData.industry,
      audience: ideaData.audience,
      problem: ideaData.problem,
      vision: ideaData.vision,
      goal: ideaData.goal,
    });

    return response.data;
  } catch (err) {
    console.error("AI Service Error:", err.response?.data || err.message);

    throw new Error(
      err.response?.data?.error || err.message || "Failed to contact AI service"
    );
  }
};

module.exports = { runPythonAI };