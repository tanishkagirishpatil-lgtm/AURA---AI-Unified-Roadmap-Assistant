const express = require("express");
const cors = require("cors");
require("dotenv").config();

require("./src/config/db");

const ideasRoutes = require("./src/routes/ideas");
const dashboardRoutes = require("./src/routes/dashboard");
const authRoutes = require("./src/routes/authRoutes");
const aiRoutes = require("./src/routes/aiRoutes"); // ✅ FIXED

const app = express();

app.use(cors({
  origin: "*",
  methods: ["GET", "POST", "PUT", "DELETE"],
  allowedHeaders: ["Content-Type", "Authorization"]
}));
app.use(express.json());

app.use("/api/ideas", ideasRoutes);
app.use("/api/dashboard", dashboardRoutes);
app.use("/api/auth", authRoutes);
app.use("/api/ai", require("./src/routes/aiRoutes"));

app.get("/", (req, res) => {
    res.send("AURA Backend Running");
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});