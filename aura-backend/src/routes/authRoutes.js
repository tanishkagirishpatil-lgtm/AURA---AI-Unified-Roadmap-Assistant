const express = require("express");
const router = express.Router();

const { register, login } = require("../controllers/authController");
const authMiddleware = require("../middleware/authMiddleware"); // ✅ ADD THIS

router.post("/register", register);
router.post("/login", login);

// VERIFY ROUTE
router.get("/verify", authMiddleware, (req, res) => {
  res.json({ user: req.user });
});

module.exports = router;