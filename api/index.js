const express = require("express");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json({ limit: "1mb" }));

const PYTHON_API_URL = (process.env.PYTHON_API_URL || "").replace(/\/$/, "");

function missingPythonApiUrl(res) {
  return res.status(500).json({
    status: "error",
    detail: "PYTHON_API_URL is not configured. Deploy the Python FastAPI service separately and set this environment variable in Vercel.",
  });
}

function proxyPost(pathname) {
  return async (req, res) => {
    if (!PYTHON_API_URL) return missingPythonApiUrl(res);

    try {
      const upstream = await fetch(`${PYTHON_API_URL}${pathname}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req.body),
      });

      const payload = await upstream.text();
      res
        .status(upstream.status)
        .type(upstream.headers.get("content-type") || "application/json")
        .send(payload);
    } catch (error) {
      console.error(`Python API proxy error for ${pathname}:`, error);
      res.status(502).json({
        status: "error",
        detail: "Unable to connect to Python API",
      });
    }
  };
}

app.get("/api/config", (req, res) => {
  res.json({
    clientId: process.env.GOOGLE_CLIENT_ID || "",
    supabaseUrl: process.env.SUPABASE_URL || "",
    supabaseKey: process.env.SUPABASE_ANON_KEY || "",
  });
});

app.get("/favicon.ico", (req, res) => {
  res.status(204).end();
});

app.post("/api/v1/horoscope", proxyPost("/api/v1/horoscope"));
app.post("/api/v1/numerology", proxyPost("/api/v1/numerology"));
app.post("/api/v1/lucky-color", proxyPost("/api/v1/lucky-color"));
app.post("/api/v1/thai-astrology", proxyPost("/api/v1/thai-astrology"));
app.post("/api/v1/tarot-reading", proxyPost("/api/v1/tarot-reading"));

module.exports = app;
