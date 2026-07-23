require("dotenv").config();
const db = require("./src/config/db");

(async () => {
  try {
    console.log("Checking if ai_results column already exists...");

    const [cols] = await db.query(
      `SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
       WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'ideas' AND COLUMN_NAME = 'ai_results'`,
      [process.env.DB_NAME || "aura_db"]
    );

    if (cols.length > 0) {
      console.log("✅ Column ai_results already exists, nothing to do.");
      process.exit(0);
    }

    console.log("Adding ai_results column to ideas table...");
    await db.query("ALTER TABLE ideas ADD COLUMN ai_results JSON NULL");
    console.log("✅ Done! ai_results column added.");
    process.exit(0);

  } catch (err) {
    console.error("❌ Migration failed:", err.message);
    process.exit(1);
  }
})();