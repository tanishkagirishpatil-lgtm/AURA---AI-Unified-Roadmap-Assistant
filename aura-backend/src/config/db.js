const mysql = require("mysql2/promise");

const db = mysql.createPool({
  host: "localhost",
  user: "root",
  password: "Vedant@99",
  database: "aura_db",
  waitForConnections: true,
  connectionLimit: 10,
});

module.exports = db;