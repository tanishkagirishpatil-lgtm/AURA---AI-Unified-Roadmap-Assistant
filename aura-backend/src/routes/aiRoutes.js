const express = require("express");
const router = express.Router();

const { runAI } = require("../controllers/aiController");

// test route
router.get("/test", (req, res) => {
    res.json({ message: "AI route working" });
});

// main AI endpoint
router.post("/run", runAI);

module.exports = router;