require("dotenv").config();
const db = require("./src/config/db");

(async () => {
  try {
    const columnsToAdd = [
      { name: "default_industry", def: "VARCHAR(50) NULL" },
      { name: "default_currency", def: "VARCHAR(10) NULL DEFAULT 'INR'" },
      { name: "language", def: "VARCHAR(10) NULL DEFAULT 'English'" },
    ];

    for (const col of columnsToAdd) {
      const [existing] = await db.query(
        `SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
         WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'users' AND COLUMN_NAME = ?`,
        [process.env.DB_NAME, col.name]
      );

      if (existing.length > 0) {
        console.log(`✅ Column ${col.name} already exists, skipping.`);
        continue;
      }

      console.log(`Adding column ${col.name}...`);
      await db.query(`ALTER TABLE users ADD COLUMN ${col.name} ${col.def}`);
      console.log(`✅ Added ${col.name}.`);
    }

    console.log("\n✅ Migration complete.");
    process.exit(0);

  } catch (err) {
    console.error("❌ Migration failed:", err.message);
    process.exit(1);
  }
})();