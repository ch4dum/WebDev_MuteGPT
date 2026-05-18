const path = require('path');
const dotenv = require('dotenv');
const express = require('express');
const cors = require('cors');

dotenv.config({ path: path.join(__dirname, '../python/.env') });
dotenv.config({ path: path.join(__dirname, '.env'), override: true });

const app = express();

app.use(cors());
app.use(express.json());

// Serve static files (HTML, CSS, JS, images)
const frontendPath = path.join(__dirname, '../../frontend');
app.use(express.static(frontendPath));

app.get('/favicon.ico', (req, res) => {
    res.status(204).end();
});

// Explicitly serve index.html for the root route
app.get('/', (req, res) => {
    res.sendFile(path.join(frontendPath, 'index.html'));
});

// Load Environment Variables
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';
const DAILY_READING_LIMIT = Number(process.env.DAILY_READING_LIMIT || 5);

const LIMITED_ENDPOINTS = {
    '/api/v1/horoscope': 'love',
    '/api/v1/numerology': 'numerology',
    '/api/v1/lucky-color': 'color',
    '/api/v1/thai-astrology': 'hora',
    '/api/v1/tarot-reading': 'tarot'
};

// API: Serve configuration to the Frontend
app.get('/api/config', (req, res) => {
    res.json({
        clientId: GOOGLE_CLIENT_ID,
        supabaseUrl: SUPABASE_URL,
        supabaseKey: SUPABASE_ANON_KEY
    });
});

function getBearerToken(req) {
    const auth = req.headers.authorization || '';
    const match = auth.match(/^Bearer\s+(.+)$/i);
    return match ? match[1] : '';
}

function getBangkokDayWindow() {
    const parts = new Intl.DateTimeFormat('en-CA', {
        timeZone: 'Asia/Bangkok',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    }).formatToParts(new Date());
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    const start = new Date(Date.UTC(Number(values.year), Number(values.month) - 1, Number(values.day), -7, 0, 0));
    const end = new Date(start.getTime() + 24 * 60 * 60 * 1000);
    return { start: start.toISOString(), end: end.toISOString() };
}

async function getSupabaseUser(accessToken) {
    const response = await fetch(`${SUPABASE_URL.replace(/\/$/, '')}/auth/v1/user`, {
        headers: {
            apikey: SUPABASE_ANON_KEY,
            Authorization: `Bearer ${accessToken}`
        }
    });
    if (!response.ok) return null;
    return response.json();
}

function parseContentRangeCount(headerValue) {
    const match = String(headerValue || '').match(/\/(\d+)$/);
    return match ? Number(match[1]) : 0;
}

async function countUsageEvents(accessToken, userId) {
    const { start, end } = getBangkokDayWindow();
    const params = new URLSearchParams({
        select: 'id',
        user_id: `eq.${userId}`,
        used_at: `gte.${start}`
    });
    params.append('used_at', `lt.${end}`);

    const response = await fetch(`${SUPABASE_URL.replace(/\/$/, '')}/rest/v1/reading_usage_events?${params.toString()}`, {
        headers: {
            apikey: SUPABASE_ANON_KEY,
            Authorization: `Bearer ${accessToken}`,
            Prefer: 'count=exact',
            Range: '0-0'
        }
    });
    if (!response.ok) throw new Error(`Usage count failed: ${response.status}`);
    return parseContentRangeCount(response.headers.get('content-range'));
}

async function insertUsageEvent(accessToken, userId, moduleName, pathname) {
    const response = await fetch(`${SUPABASE_URL.replace(/\/$/, '')}/rest/v1/reading_usage_events`, {
        method: 'POST',
        headers: {
            apikey: SUPABASE_ANON_KEY,
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
            Prefer: 'return=minimal'
        },
        body: JSON.stringify({
            user_id: userId,
            module: moduleName,
            endpoint: pathname
        })
    });
    if (!response.ok) throw new Error(`Usage insert failed: ${response.status}`);
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
            payload: { status: 'error', detail: 'Please sign in before requesting an AI reading.' }
        };
    }

    const user = await getSupabaseUser(accessToken);
    if (!user?.id) {
        return {
            ok: false,
            status: 401,
            payload: { status: 'error', detail: 'Your login session is invalid or expired. Please sign in again.' }
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
                    status: 'error',
                    detail: `วันนี้คุณใช้สิทธิ์ดูดวงครบ ${DAILY_READING_LIMIT} ครั้งแล้ว กลับมาใหม่พรุ่งนี้นะคะ`,
                    limit: DAILY_READING_LIMIT,
                    used
                }
            };
        }
        await insertUsageEvent(accessToken, user.id, moduleName, pathname);
    } catch (error) {
        console.error('Reading usage limit error:', error);
        return {
            ok: false,
            status: 500,
            payload: {
                status: 'error',
                detail: 'Reading quota is not configured. Please run supabase/reading_usage_schema.sql in Supabase.'
            }
        };
    }

    return { ok: true };
}

async function proxyToPython(req, res, pathname, errorLabel) {
    try {
        const limitResult = await enforceReadingLimit(req, pathname);
        if (!limitResult.ok) {
            return res.status(limitResult.status).json(limitResult.payload);
        }

        const upstream = await fetch(`${PYTHON_API_URL}${pathname}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        });

        const payload = await upstream.text();
        res.status(upstream.status).type(upstream.headers.get('content-type') || 'application/json').send(payload);
    } catch (error) {
        console.error(errorLabel, error);
        res.status(502).json({
            status: 'error',
            detail: 'Unable to connect to Python API'
        });
    }
}

app.post('/api/v1/horoscope', async (req, res) => {
    await proxyToPython(req, res, '/api/v1/horoscope', 'Python API proxy error:');
});

app.post('/api/v1/numerology', async (req, res) => {
    await proxyToPython(req, res, '/api/v1/numerology', 'Python numerology API proxy error:');
});

app.post('/api/v1/lucky-color', async (req, res) => {
    await proxyToPython(req, res, '/api/v1/lucky-color', 'Python lucky color API proxy error:');
});

app.post('/api/v1/thai-astrology', async (req, res) => {
    await proxyToPython(req, res, '/api/v1/thai-astrology', 'Python thai astrology API proxy error:');
});

app.post('/api/v1/tarot-reading', async (req, res) => {
    await proxyToPython(req, res, '/api/v1/tarot-reading', 'Python tarot reading API proxy error:');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
    console.log(`Supabase & Google Config is ready for Frontend.`);
});
