const db = require("../config/db");

// =====================
// GET MY PROFILE
// =====================
exports.getMe = async (req, res) => {
  try {
    const [users] = await db.query(
      "SELECT id, name, email, default_industry, default_currency, language FROM users WHERE id = ?",
      [req.user.id]
    );

    if (users.length === 0) {
      return res.status(404).json({ error: "User not found" });
    }

    res.status(200).json({ user: users[0] });

  } catch (error) {
    console.error(error);
    res.status(500).json({ error: error.message });
  }
};

// =====================
// UPDATE MY PROFILE / PREFERENCES
// =====================
exports.updateMe = async (req, res) => {
  try {
    const { name, default_industry, default_currency, language } = req.body;

    if (!name || !name.trim()) {
      return res.status(400).json({ error: "Name is required" });
    }

    await db.query(
      `UPDATE users
       SET name = ?, default_industry = ?, default_currency = ?, language = ?
       WHERE id = ?`,
      [
        name.trim(),
        default_industry || null,
        default_currency || "INR",
        language || "English",
        req.user.id
      ]
    );

    const [users] = await db.query(
      "SELECT id, name, email, default_industry, default_currency, language FROM users WHERE id = ?",
      [req.user.id]
    );

    res.status(200).json({
      message: "Profile updated",
      user: users[0]
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({ error: error.message });
  }
};