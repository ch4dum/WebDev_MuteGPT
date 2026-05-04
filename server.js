require('dotenv').config();
const path = require('path');
const express = require('express');
const cors = require('cors');
// const fetch = require('node-fetch');

const app = express();

app.use(cors());
app.use(express.json());

// Serve static files (HTML, CSS, JS, images)
app.use(express.static(path.join(__dirname)));

// Load Environment Variables
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;

// API: Serve configuration to the Frontend
app.get('/api/config', (req, res) => {
    res.json({
        clientId: GOOGLE_CLIENT_ID,
        supabaseUrl: SUPABASE_URL,
        supabaseKey: SUPABASE_ANON_KEY
    });
});

app.post('/api/chat', async (req, res) => {
    const { systemPrompt, userContextPrompt } = req.body;

    try {
       const response = await fetch(
  `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${process.env.GEMINI_API_KEY}`,
            {   
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [
                        {
                            parts: [
                                {
                                    text: systemPrompt + '\n' + userContextPrompt
                                }
                            ]
                        }
                    ]
                })
            }
        );

        // ✅ เช็ค status
        console.log('API Status:', response.status);

        const data = await response.json();

        // ✅ log response จริง
        console.log('API Response:', JSON.stringify(data, null, 2));

        // ❌ ถ้า API fail
        if (!response.ok) {
            return res.status(response.status).json({
                error: 'Gemini API error',
                detail: data
            });
        }

        const text =
            data?.candidates?.[0]?.content?.parts?.[0]?.text ||
            'แม่หมอเห็นพลังงานไม่ชัดเจน ลองใหม่อีกครั้งนะคะ';

        res.json({ text });

    } catch (err) {
        console.error('Fetch Error:', err);

        res.status(500).json({
            error: 'server error',
            detail: err.message
        });
    }
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
    console.log(`Supabase & Google Config is ready for Frontend.`);
});
