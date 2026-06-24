import express from 'express';
import path from 'path';
import { createServer as createViteServer } from 'vite';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://ai-medical-triage-dab8.onrender.com/';

// -------------------------------------------------------------
// API ENDPOINTS (Proxy to FastAPI Backend)
// -------------------------------------------------------------

// 1. Health check
app.get('/api/v1/health', (req, res) => {
  res.json({ status: "ok", backend_endpoint: API_BASE_URL });
});

// 2. Chat API matching required FastAPI schema
app.post('/api/v1/chat', async (req, res) => {
  const { session_id, message, history = [] } = req.body;

  if (!message || message.trim() === '') {
    return res.status(400).json({ error: "Patient message cannot be blank." });
  }

  // Format conversation history for FastAPI format
  const conversation_history = history.map((h: any) => ({
    role: h.role,
    content: h.content
  }));

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id,
        message,
        conversation_history,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      return res.status(response.status).json({ error: `FastAPI responded with error: ${errText}` });
    }

    const data = await response.json();
    return res.json(data);
  } catch (err: any) {
    console.error("FastAPI connection lost:", err.message);
    return res.status(502).json({ error: `FastAPI backend unreachable: ${err.message}` });
  }
});

// 3. Report Generation
app.post('/api/v1/report', async (req, res) => {
  const { session_id } = req.body;

  if (!session_id) {
    return res.status(400).json({ error: "session_id is required to compile report stats." });
  }

  try {
    const response = await fetch(`${API_BASE_URL}/report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      return res.status(response.status).json({ error: `FastAPI report responded with error: ${errText}` });
    }

    const data = await response.json();
    
    // If FastAPI provides a download url, attempt to retrieve report content and stream as markdown attachment
    if (data.download_url) {
      try {
        const fileRes = await fetch(data.download_url);
        if (fileRes.ok) {
          const text = await fileRes.text();
          res.setHeader('Content-Type', 'text/markdown');
          res.setHeader('Content-Disposition', `attachment; filename="medical_triage_report_${session_id}.md"`);
          return res.send(text);
        }
      } catch (dlErr: any) {
        console.error("Failed to download from download_url:", dlErr.message);
      }
    }
    
    // Otherwise serve response directly as JSON matching the /report schema
    return res.json(data);

  } catch (err: any) {
    console.error("FastAPI backend down:", err.message);
    return res.status(502).json({ error: `FastAPI backend report generation unreachable: ${err.message}` });
  }
});

// 4. Session Status Fetch
app.get('/api/v1/session/:id', async (req, res) => {
  try {
    const response = await fetch(`${API_BASE_URL}/session/${req.params.id}`);
    if (response.ok) {
      const data = await response.json();
      return res.json(data);
    }
    const errText = await response.text();
    return res.status(response.status).json({ error: `FastAPI session responded with: ${errText}` });
  } catch (err: any) {
    console.error("FastAPI session fetch down:", err.message);
    return res.status(502).json({ error: `FastAPI session fetch unreachable: ${err.message}` });
  }
});

// -------------------------------------------------------------
// VITE DEV SERVER / STATIC SERVING HANDLERS
// -------------------------------------------------------------
async function initServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

initServer();
