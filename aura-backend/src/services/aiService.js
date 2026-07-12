const { spawn } = require("child_process");
const path = require("path");

const runPythonAI = (ideaData) => {
  return new Promise((resolve, reject) => {

    const pythonProjectPath = path.join(
      "C:", "Users", "vedan", "Desktop", "Python", "AURA"
    );

    // Build a single text string for Python from the object
    const ideaText = typeof ideaData === 'string'
      ? ideaData
      : `Project: ${ideaData.title}. Industry: ${ideaData.industry}. Audience: ${ideaData.audience}. Problem: ${ideaData.problem}. Vision: ${ideaData.vision}. Goal: ${ideaData.goal}`;

    console.log("🐍 Spawning Python at:", pythonProjectPath);
    console.log("🐍 Idea text:", ideaText);

    const pythonProcess = spawn(
      "python",
      ["-m", "ai_agents.main", ideaText],
      { cwd: pythonProjectPath }
    );

    let output = "";
    let errorOutput = "";

    pythonProcess.stdout.on("data", (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      errorOutput += data.toString();
      console.log("🐍 Python log:", data.toString());
    });

    pythonProcess.on("error", (err) => {
      console.error("❌ Spawn error:", err);
      return reject(err.message);
    });

    pythonProcess.on("close", (code) => {
      console.log("🐍 Python exited with code:", code);
      console.log("📤 Raw output:", output);

      if (code !== 0) {
        return reject(errorOutput || "Python process failed");
      }

      try {
        const lines = output.split('\n').map(l => l.trim()).filter(Boolean);
        const jsonLine = lines.reverse().find(l => l.startsWith('{') && l.endsWith('}'));

        if (!jsonLine) {
          return reject("No JSON line found in Python output");
        }

        const parsed = JSON.parse(jsonLine);
        return resolve(parsed);

      } catch (err) {
        console.error("❌ JSON Parse error:", err);
        return reject("JSON Parse Failed: " + err.message);
      }
    });

    // Kill after 90 seconds
    setTimeout(() => {
      pythonProcess.kill();
      reject("Timeout after 90s");
    }, 90000);

  });
};

module.exports = { runPythonAI };