require('dotenv').config();
const express = require('express');
const { OAuth2Client } = require('google-auth-library');
const cors = require('cors');

const app = express();

// 1. ตั้งค่า CORS เพื่อให้ Frontend (localhost:5500) คุยกับ Backend (localhost:3000) ได้
app.use(cors());
app.use(express.json());

// 2. ดึงข้อมูลจาก .env
const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const REDIRECT_URI = process.env.REDIRECT_URI;

const client = new OAuth2Client(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);

app.get('/api/config', (req, res) => {
    res.json({ clientId: CLIENT_ID });
});

app.post('/api/google-login', async (req, res) => {
    const { code } = req.body; // รับ authCode มาจาก Frontend

    try {
        // 3. นำ Code ไปแลกเป็น Tokens (Access Token, ID Token)
        const { tokens } = await client.getToken(code);
        client.setCredentials(tokens);

        // 4. ตรวจสอบและดึงข้อมูล Profile จาก ID Token
        const ticket = await client.verifyIdToken({
            idToken: tokens.id_token,
            audience: CLIENT_ID,
        });
        
        const payload = ticket.getPayload();
        
        // ข้อมูล User ที่เราจะได้
        const user = {
            googleId: payload['sub'],
            email: payload['email'],
            name: payload['name'],
            picture: payload['picture']
        };

        console.log('Login Success:', user.name);

        // 5. ส่งข้อมูลกลับไปที่ Frontend
        res.status(200).json({
            message: 'Login successful',
            user: user
        });

    } catch (error) {
        console.error('Google Auth Error:', error);
        res.status(401).json({ message: 'Authentication failed', error: error.message });
    }
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});