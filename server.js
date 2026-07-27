import express from "express";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(express.json());

// Serve index.html
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "index.html"));
});

// Python call
app.post("/play", (req, res) => {
    const message = req.body.message || "";

    const py = spawn("python", ["play.py", message]);

    let output = "";
    py.stdout.on("data", data => output += data.toString());

    py.on("close", () => {
        res.json({ reply: output.trim() });
    });
});

app.listen(3000, () => {
    console.log("Server running on http://localhost:3000");
});
