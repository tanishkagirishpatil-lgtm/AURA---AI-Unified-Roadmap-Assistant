const express = require("express");
const router = express.Router();

const authMiddleware = require("../middleware/authMiddleware");

const {
    getIdeas,
    createIdea,
    getIdeaById,
    deleteIdea,
    updateIdea
} = require("../controllers/ideaController");
// Protected Routes
router.get("/", authMiddleware, getIdeas);
router.post("/", authMiddleware, createIdea);
router.get("/:id", authMiddleware, getIdeaById);
router.delete("/:id", authMiddleware, deleteIdea);
router.put("/:id", authMiddleware, updateIdea);
module.exports = router;