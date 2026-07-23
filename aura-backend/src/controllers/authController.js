const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const db = require("../config/db");

// =====================
// REGISTER
// =====================
exports.register = async (req, res) => {
  try {
    const { name, email, password } = req.body;

    if (!name || !email || !password) {
      return res.status(400).json({
        error: "Name, email and password are required"
      });
    }

    // Check existing user
    const [existingUsers] = await db.query(
      "SELECT * FROM users WHERE email = ?",
      [email]
    );

    if (existingUsers.length > 0) {
      return res.status(400).json({
        error: "User already exists"
      });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Insert user
    const [result] = await db.query(
      "INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
      [name, email, hashedPassword]
    );

    res.status(201).json({
      message: "User registered successfully",
      userId: result.insertId
    });

  } catch (error) {
    console.error(error);

    res.status(500).json({
      error: error.message
    });
  }
};

// =====================
// GOOGLE LOGIN
// =====================
exports.googleAuth = async (req, res) => {
  try {
    const { access_token } = req.body;

    if (!access_token) {
      return res.status(400).json({
        error: "access_token is required"
      });
    }

    // Verify the token by asking Google directly who it belongs to.
    // This is the real verification step — we never trust the
    // frontend's claim about who the user is.
    const profileRes = await fetch(
      `https://www.googleapis.com/oauth2/v3/userinfo?access_token=${access_token}`
    );

    if (!profileRes.ok) {
      return res.status(401).json({
        error: "Invalid or expired Google access token"
      });
    }

    const profile = await profileRes.json();
    const { email, name } = profile;

    if (!email) {
      return res.status(400).json({
        error: "Google account did not return an email address"
      });
    }

    // Find or create the user
    const [existingUsers] = await db.query(
      "SELECT * FROM users WHERE email = ?",
      [email]
    );

    let user;

    if (existingUsers.length > 0) {
      user = existingUsers[0];
    } else {
      // New Google-only account — set a random, never-used password
      // hash since the column is NOT NULL and this user will only
      // ever log in via Google.
      const crypto = require("crypto");
      const randomPassword = crypto.randomBytes(32).toString("hex");
      const hashedPassword = await bcrypt.hash(randomPassword, 10);

      const [result] = await db.query(
        "INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
        [name || email.split("@")[0], email, hashedPassword]
      );

      user = {
        id: result.insertId,
        name: name || email.split("@")[0],
        email
      };
    }

    const token = jwt.sign(
      { id: user.id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: "7d" }
    );

    res.status(200).json({
      message: "Google login successful",
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email
      }
    });

  } catch (error) {
    console.error(error);

    res.status(500).json({
      error: error.message
    });
  }
};
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        error: "Email and password are required"
      });
    }

    // Find user
    const [users] = await db.query(
      "SELECT * FROM users WHERE email = ?",
      [email]
    );

    if (users.length === 0) {
      return res.status(401).json({
        error: "Invalid credentials"
      });
    }

    const user = users[0];

    // Compare password
    const isMatch = await bcrypt.compare(
      password,
      user.hashed_password
    );

    if (!isMatch) {
      return res.status(401).json({
        error: "Invalid credentials"
      });
    }

    // Generate token
    const token = jwt.sign(
      {
        id: user.id,
        email: user.email
      },
      process.env.JWT_SECRET,
      {
        expiresIn: "7d"
      }
    );

    res.status(200).json({
      message: "Login successful",
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email
      }
    });

  } catch (error) {
    console.error(error);

    res.status(500).json({
      error: error.message
    });
  }
};