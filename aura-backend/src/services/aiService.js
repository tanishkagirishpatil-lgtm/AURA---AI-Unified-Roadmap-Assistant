const { spawn } = require("child_process");
const path = require("path");

const runPythonAI = (ideaData) => {
  return new Promise((resolve, reject) => {

    const pythonProjectPath =
      process.env.AI_PROJECT_PATH ||
      path.join(__dirname, "..", "..", "..");

    const pythonBin =
      process.env.PYTHON_BIN ||
      (process.platform === "win32" ? "python" : "python3");

    const ideaText = typeof ideaData === 'string'
      ? ideaData
      : `Project: ${ideaData.title}. Industry: ${ideaData.industry}. Audience: ${ideaData.audience}. Problem: ${ideaData.problem}. Vision: ${ideaData.vision}. Goal: ${ideaData.goal}`;

    console.log("🐍 Spawning Python at:", pythonProjectPath);
    console.log("🐍 Using interpreter:", pythonBin);

    const pythonProcess = spawn(
      pythonBin,
      ["-m", "ai_agents.main", ideaText],
      { cwd: pythonProjectPath }
    );

    let output = "";
    let errorOutput = "";
    let settled = false;

    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      pythonProcess.kill();
      reject("Timeout after 240s");
    }, 240000);

    pythonProcess.stdout.on("data", (data) => { output += data.toString(); });
    pythonProcess.stderr.on("data", (data) => {
      errorOutput += data.toString();
      console.log("🐍 Python log:", data.toString());
    });

    pythonProcess.on("error", (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(err.message);
    });

    pythonProcess.on("close", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);

      if (code !== 0) return reject(errorOutput || "Python process failed");

      try {
        const lines = output.split('\n').map(l => l.trim()).filter(Boolean);
        const jsonLine = lines.reverse().find(l => l.startsWith('{') && l.endsWith('}'));
        if (!jsonLine) return reject("No JSON line found in Python output");
        return resolve(JSON.parse(jsonLine));
      } catch (err) {
        reject("JSON Parse Failed: " + err.message);
      }
    });

  });
};

module.exports = { runPythonAI };