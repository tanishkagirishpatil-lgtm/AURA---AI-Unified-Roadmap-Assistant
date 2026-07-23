const express = require("express");
const router = express.Router();

const { register, login, googleAuth } = require("../controllers/authController");
const authMiddleware = require("../middleware/authMiddleware"); // ✅ ADD THIS

router.post("/register", register);
router.post("/login", login);
router.post("/google", googleAuth);

// VERIFY ROUTE
router.get("/verify", authMiddleware, (req, res) => {
  res.json({ user: req.user });
});

module.exports = router;