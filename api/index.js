const express = require("express");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json({ limit: "1mb" }));

const PYTHON_API_URL = (process.env.PYTHON_API_URL || "").replace(/\/$/, "");
const SUPABASE_URL = (process.env.SUPABASE_URL || "").replace(/\/$/, "");
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || "";
const DAILY_READING_LIMIT = Number(process.env.DAILY_READING_LIMIT || 5);

const LIMITED_ENDPOINTS = {
  "/api/v1/horoscope": "love",
  "/api/v1/numerology": "numerology",
  "/api/v1/lucky-color": "color",
  "/api/v1/thai-astrology": "hora",
  "/api/v1/tarot-reading": "tarot",
};

function missingPythonApiUrl(res) {
  return res.status(500).json({
    status: "error",
    detail: "PYTHON_API_URL is not configured. Deploy the Python FastAPI service separately and set this environment variable in Vercel.",
  });
}

function getBearerToken(req) {
  const auth = req.headers.authorization || "";
  const match = auth.match(/^Bearer\s+(.+)$/i);
  return match ? match[1] : "";
}

function getBangkokDayWindow() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Bangkok",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const start = new Date(Date.UTC(Number(values.year), Number(values.month) - 1, Number(values.day), -7, 0, 0));
  const end = new Date(start.getTime() + 24 * 60 * 60 * 1000);
  return { start: start.toISOString(), end: end.toISOString() };
}

async function getSupabaseUser(accessToken) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!res.ok) return null;
  return res.json();
}

function parseContentRangeCount(headerValue) {
  const match = String(headerValue || "").match(/\/(\d+)$/);
  return match ? Number(match[1]) : 0;
}

async function countUsageEvents(accessToken, userId) {
  const { start, end } = getBangkokDayWindow();
  const params = new URLSearchParams({
    select: "id",
    user_id: `eq.${userId}`,
    used_at: `gte.${start}`,
  });
  params.append("used_at", `lt.${end}`);

  const res = await fetch(`${SUPABASE_URL}/rest/v1/reading_usage_events?${params.toString()}`, {
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${accessToken}`,
      Prefer: "count=exact",
      Range: "0-0",
    },
  });
  if (!res.ok) throw new Error(`Usage count failed: ${res.status}`);
  return parseContentRangeCount(res.headers.get("content-range"));
}

async function insertUsageEvent(accessToken, userId, moduleName, pathname) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/reading_usage_events`, {
    method: "POST",
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      Prefer: "return=minimal",
    },
    body: JSON.stringify({
      user_id: userId,
      module: moduleName,
      endpoint: pathname,
    }),
  });
  if (!res.ok) throw new Error(`Usage insert failed: ${res.status}`);
}

async function enforceReadingLimit(req, pathname) {
  const moduleName = LIMITED_ENDPOINTS[pathname];
  if (!moduleName || DAILY_READING_LIMIT <= 0) return { ok: true };
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return { ok: true };

  const accessToken = getBearerToken(req);
  if (!accessToken) {
    return {
      ok: false,
      status: 401,
      payload: { status: "error", detail: "Please sign in before requesting an AI reading." },
    };
  }

  const user = await getSupabaseUser(accessToken);
  if (!user?.id) {
    return {
      ok: false,
      status: 401,
      payload: { status: "error", detail: "Your login session is invalid or expired. Please sign in again." },
    };
  }

  let used = 0;
  try {
    used = await countUsageEvents(accessToken, user.id);
    if (used >= DAILY_READING_LIMIT) {
      return {
        ok: false,
        status: 429,
        payload: {
          status: "error",
          detail: `วันนี้คุณใช้สิทธิ์ดูดวงครบ ${DAILY_READING_LIMIT} ครั้งแล้ว กลับมาใหม่พรุ่งนี้นะคะ`,
          limit: DAILY_READING_LIMIT,
          used,
        },
      };
    }
    await insertUsageEvent(accessToken, user.id, moduleName, pathname);
  } catch (error) {
    console.error("Reading usage limit error:", error);
    return {
      ok: false,
      status: 500,
      payload: {
        status: "error",
        detail: "Reading quota is not configured. Please run supabase/reading_usage_schema.sql in Supabase.",
      },
    };
  }

  return { ok: true };
}

async function getReadingUsageStatus(req) {
  if (DAILY_READING_LIMIT <= 0) {
    return { ok: true, status: 200, payload: { limit: 0, used: 0, remaining: null, reset_timezone: "Asia/Bangkok" } };
  }

  const accessToken = getBearerToken(req);
  if (!accessToken) {
    return {
      ok: false,
      status: 401,
      payload: { status: "error", detail: "Please sign in to view your reading quota." },
    };
  }

  const user = await getSupabaseUser(accessToken);
  if (!user?.id) {
    return {
      ok: false,
      status: 401,
      payload: { status: "error", detail: "Your login session is invalid or expired. Please sign in again." },
    };
  }

  try {
    const used = await countUsageEvents(accessToken, user.id);
    return {
      ok: true,
      status: 200,
      payload: {
        limit: DAILY_READING_LIMIT,
        used,
        remaining: Math.max(DAILY_READING_LIMIT - used, 0),
        reset_timezone: "Asia/Bangkok",
      },
    };
  } catch (error) {
    console.error("Reading usage status error:", error);
    return {
      ok: false,
      status: 500,
      payload: {
        status: "error",
        detail: "Reading quota is not configured. Please run supabase/reading_usage_schema.sql in Supabase.",
      },
    };
  }
}

function proxyPost(pathname) {
  return async (req, res) => {
    if (!PYTHON_API_URL) return missingPythonApiUrl(res);

    try {
      const limitResult = await enforceReadingLimit(req, pathname);
      if (!limitResult.ok) {
        return res.status(limitResult.status).json(limitResult.payload);
      }

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

app.get("/api/v1/reading-usage", async (req, res) => {
  const result = await getReadingUsageStatus(req);
  res.status(result.status).json(result.payload);
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
