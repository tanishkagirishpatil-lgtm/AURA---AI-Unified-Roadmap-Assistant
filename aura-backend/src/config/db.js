require("dotenv").config();
const mysql = require("mysql2/promise");

const db = mysql.createPool({
  host: process.env.DB_HOST || "localhost",
  port: process.env.DB_PORT || 3306,
  user: process.env.DB_USER || "root",
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME || "aura_db",
  waitForConnections: true,
  connectionLimit: 10,
  ssl: process.env.DB_SSL === "true" ? { rejectUnauthorized: true } : undefined,

  // Keeps idle connections alive with periodic TCP keepalive packets so
  // they don't get silently dropped by antivirus/firewall/NAT while
  // sitting unused in the pool — this is the most common cause of
  // ECONNRESET errors that only show up after the app has been idle
  // for a while.
  enableKeepAlive: true,
  keepAliveInitialDelay: 10000,
});

// Without this listener, any connection-level error (like a stale
// connection finally being reset) is treated by Node as an unhandled
// error and crashes the ENTIRE process instead of just failing the
// one request that happened to be using it. This keeps the server
// alive and just logs the issue instead.
db.on("error", (err) => {
  console.error("⚠️  MySQL pool error (server stayed up):", err.code || err.message);
});

module.exports = db;