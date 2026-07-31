import express from "express";
import fetch from "node-fetch";   // ⭐ REQUIRED for Node to use fetch
import path from "path";
import { fileURLToPath } from "url";


const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(express.json());
app.use("/resources", express.static(path.join(__dirname, "resources")));
app.use("/images", express.static(path.join(__dirname, "images")));   // ⭐ Add this

// ⭐ Serve your front-end
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "index.html"));
});

// ⭐ Chat → Python API
app.post("/play", async (req, res) => {
    const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: req.body.message })
    });

    const data = await response.json();
    res.json({ reply: data.reply });
});

// ⭐ History → Python API
app.get("/history", async (req, res) => {
    const response = await fetch("http://127.0.0.1:8000/history");
    const data = await response.json();
    res.json(data);
});

// ⭐ Image prompt → Python API
app.get("/image", async (req, res) => {
    const response = await fetch("http://127.0.0.1:8000/image");
    const data = await response.json();
    res.json(data);
});



app.get("/character", async (req, res) => {
    const response = await fetch("http://127.0.0.1:8000/character");
    const data = await response.json();
    res.json(data);
});


app.post("/character/select", async (req, res) => {
    const response = await fetch("http://127.0.0.1:8000/character/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: req.body.name })
    });

    const data = await response.json();
    res.json(data);
});


// ⭐ Start Node server
app.listen(3000, () => {
    console.log("Server running on http://localhost:3000");
});
