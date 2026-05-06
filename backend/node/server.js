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

// API: Serve configuration to the Frontend
app.get('/api/config', (req, res) => {
    res.json({
        clientId: GOOGLE_CLIENT_ID,
        supabaseUrl: SUPABASE_URL,
        supabaseKey: SUPABASE_ANON_KEY
    });
});

app.post('/api/v1/horoscope', async (req, res) => {
    try {
        const upstream = await fetch(`${PYTHON_API_URL}/api/v1/horoscope`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        });

        const payload = await upstream.text();
        res.status(upstream.status).type(upstream.headers.get('content-type') || 'application/json').send(payload);
    } catch (error) {
        console.error('Python API proxy error:', error);
        res.status(502).json({
            status: 'error',
            detail: 'Unable to connect to Python horoscope API'
        });
    }
});

app.post('/api/v1/numerology', async (req, res) => {
    try {
        const upstream = await fetch(`${PYTHON_API_URL}/api/v1/numerology`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        });

        const payload = await upstream.text();
        res.status(upstream.status).type(upstream.headers.get('content-type') || 'application/json').send(payload);
    } catch (error) {
        console.error('Python numerology API proxy error:', error);
        res.status(502).json({
            status: 'error',
            detail: 'Unable to connect to Python numerology API'
        });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
    console.log(`Supabase & Google Config is ready for Frontend.`);
});
