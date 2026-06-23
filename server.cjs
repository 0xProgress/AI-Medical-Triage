var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// server.ts
var import_express = __toESM(require("express"), 1);
var import_path = __toESM(require("path"), 1);
var import_vite = require("vite");
var import_dotenv = __toESM(require("dotenv"), 1);
import_dotenv.default.config();
var app = (0, import_express.default)();
var PORT = process.env.PORT || 3001;
app.use(import_express.default.json());
var API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://Robob208/medtriage-frontend.hf.space/api/v1";
app.get("/api/v1/health", (req, res) => {
  res.json({ status: "ok", backend_endpoint: API_BASE_URL });
});
app.post("/api/v1/chat", async (req, res) => {
  const { session_id, message, history = [] } = req.body;
  if (!message || message.trim() === "") {
    return res.status(400).json({ error: "Patient message cannot be blank." });
  }
  const conversation_history = history.map((h) => ({
    role: h.role,
    content: h.content
  }));
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        session_id,
        message,
        conversation_history
      })
    });
    if (!response.ok) {
      const errText = await response.text();
      return res.status(response.status).json({ error: `FastAPI responded with error: ${errText}` });
    }
    const data = await response.json();
    return res.json(data);
  } catch (err) {
    console.error("FastAPI connection lost:", err.message);
    return res.status(502).json({ error: `FastAPI backend unreachable: ${err.message}` });
  }
});
app.post("/api/v1/report", async (req, res) => {
  const { session_id } = req.body;
  if (!session_id) {
    return res.status(400).json({ error: "session_id is required to compile report stats." });
  }
  try {
    const response = await fetch(`${API_BASE_URL}/report`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        session_id
      })
    });
    if (!response.ok) {
      const errText = await response.text();
      return res.status(response.status).json({ error: `FastAPI report responded with error: ${errText}` });
    }
    const data = await response.json();
    if (data.download_url) {
      try {
        const fileRes = await fetch(data.download_url);
        if (fileRes.ok) {
          const text = await fileRes.text();
          res.setHeader("Content-Type", "text/markdown");
          res.setHeader("Content-Disposition", `attachment; filename="medical_triage_report_${session_id}.md"`);
          return res.send(text);
        }
      } catch (dlErr) {
        console.error("Failed to download from download_url:", dlErr.message);
      }
    }
    return res.json(data);
  } catch (err) {
    console.error("FastAPI backend down:", err.message);
    return res.status(502).json({ error: `FastAPI backend report generation unreachable: ${err.message}` });
  }
});
app.get("/api/v1/session/:id", async (req, res) => {
  try {
    const response = await fetch(`${API_BASE_URL}/session/${req.params.id}`);
    if (response.ok) {
      const data = await response.json();
      return res.json(data);
    }
    const errText = await response.text();
    return res.status(response.status).json({ error: `FastAPI session responded with: ${errText}` });
  } catch (err) {
    console.error("FastAPI session fetch down:", err.message);
    return res.status(502).json({ error: `FastAPI session fetch unreachable: ${err.message}` });
  }
});
async function initServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await (0, import_vite.createServer)({
      server: { middlewareMode: true },
      appType: "spa"
    });
    app.use(vite.middlewares);
  } else {
    const distPath = import_path.default.join(process.cwd(), "dist");
    app.use(import_express.default.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(import_path.default.join(distPath, "index.html"));
    });
  }
  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}
initServer();
//# sourceMappingURL=server.cjs.map
