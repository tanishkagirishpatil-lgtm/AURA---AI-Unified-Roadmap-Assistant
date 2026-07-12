const db = require("../config/db");

const getStats = (req, res) => {
    const queries = {
        ideas: "SELECT COUNT(*) AS count FROM ideas",
        users: "SELECT COUNT(*) AS count FROM users",
        competitors: "SELECT COUNT(*) AS count FROM competitors",
        roadmaps: "SELECT COUNT(*) AS count FROM roadmaps"
    };

    let stats = {};
    let completed = 0;

    Object.keys(queries).forEach((key) => {
        db.query(queries[key], (err, result) => {
            if (err) {
                return res.status(500).json({ error: err.message });
            }

            stats[key] = result[0].count;
            completed++;

            if (completed === Object.keys(queries).length) {
                res.json({
                    success: true,
                    data: stats
                });
            }
        });
    });
};

module.exports = { getStats };
