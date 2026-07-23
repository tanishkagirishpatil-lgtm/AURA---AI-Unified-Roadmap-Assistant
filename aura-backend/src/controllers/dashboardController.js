const db = require("../config/db");

const getStats = async (req, res) => {
    try {
        const queries = {
            ideas: "SELECT COUNT(*) AS count FROM ideas",
            users: "SELECT COUNT(*) AS count FROM users",
            competitors: "SELECT COUNT(*) AS count FROM competitors",
            roadmaps: "SELECT COUNT(*) AS count FROM roadmaps"
        };

        const stats = {};
        const entries = Object.entries(queries);
        const results = await Promise.all(
            entries.map(([, sql]) => db.query(sql))
        );

        entries.forEach(([key], i) => {
            const [rows] = results[i];
            stats[key] = rows[0].count;
        });

        res.json({ success: true, data: stats });

    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
};

module.exports = { getStats };