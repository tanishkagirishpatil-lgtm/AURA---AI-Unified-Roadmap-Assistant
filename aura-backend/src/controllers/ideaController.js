const db = require("../config/db");

// GET ALL IDEAS OF LOGGED IN USER
const getIdeas = async (req, res) => {
    try {

        const [results] = await db.query(
            "SELECT * FROM ideas WHERE user_id = ?",
            [req.user.id]
        );

        res.json(results);

    } catch (err) {
        res.status(500).json({
            error: err.message
        });
    }
};

// CREATE IDEA
const createIdea = async (req, res) => {
    try {
        const { title, problem, solution, industry, target_audience, product_idea, vision, primary_goal } = req.body;
        const user_id = req.user.id;

        const [result] = await db.query(
            `INSERT INTO ideas 
             (user_id, title, problem, solution, industry, target_audience, product_idea, vision, primary_goal) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [user_id, title, problem, solution, industry, target_audience, product_idea, vision, primary_goal]
        );

        res.json({
            message: "Idea created successfully",
            ideaId: result.insertId
        });

    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// GET IDEA BY ID (ONLY IF IT BELONGS TO USER)
const getIdeaById = async (req, res) => {
    try {

        const [results] = await db.query(
            "SELECT * FROM ideas WHERE id = ? AND user_id = ?",
            [req.params.id, req.user.id]
        );

        if (results.length === 0) {
            return res.status(404).json({
                message: "Idea not found"
            });
        }

        res.json(results[0]);

    } catch (err) {
        res.status(500).json({
            error: err.message
        });
    }
};

// DELETE IDEA (ONLY IF IT BELONGS TO USER)
const deleteIdea = async (req, res) => {
    try {

        const [result] = await db.query(
            "DELETE FROM ideas WHERE id = ? AND user_id = ?",
            [req.params.id, req.user.id]
        );

        if (result.affectedRows === 0) {
            return res.status(404).json({
                message: "Idea not found"
            });
        }

        res.json({
            message: "Idea deleted successfully"
        });

    } catch (err) {
        res.status(500).json({
            error: err.message
        });
    }
};

// UPDATE IDEA
const updateIdea = async (req, res) => {
    try {

        const { title, problem, solution } = req.body;

        const [result] = await db.query(
            `UPDATE ideas
             SET title = ?, problem = ?, solution = ?
             WHERE id = ? AND user_id = ?`,
            [
                title,
                problem,
                solution,
                req.params.id,
                req.user.id
            ]
        );

        if (result.affectedRows === 0) {
            return res.status(404).json({
                message: "Idea not found"
            });
        }

        res.json({
            message: "Idea updated successfully"
        });

    } catch (err) {
        res.status(500).json({
            error: err.message
        });
    }
};

module.exports = {
    getIdeas,
    createIdea,
    getIdeaById,
    deleteIdea,
    updateIdea
};
