const express = require("express");
const router = express.Router();

const { runAI } = require("../controllers/aiController");
const authMiddleware = require("../middleware/authMiddleware");

router.get("/test", (req, res) => {
    res.json({ message: "AI route working" });
});

router.post("/run", authMiddleware, runAI);

module.exports = router;