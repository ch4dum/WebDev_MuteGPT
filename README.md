# MuteGPT - AI-Powered Personalized Horoscope Chatbot

MuteGPT is a personalized horoscope web application that combines Gemini AI with Thai and international astrology concepts. The project is organized as a static frontend, a Node.js gateway, and a Python FastAPI astrology/AI service.

## Project Structure

```text
/WebDev_MuteGPT
├── /backend
│   ├── /node            # Gateway, Static Server & Auth Config (Port 3000)
│   │   └── server.js
│   └── /python          # AI Brain & Astrology Calculation (Port 8000)
│       └── .env         # API Keys Storage    
│       └── main.py
├── /frontend            # Client-side files
│   ├── /assets          # Images, Backgrounds, Icons
│   ├── /css             # Stylesheets
│   ├── /js              # Logic & Auth handling
│   └── *.html           # Web Pages
└── README.md
```

## Environment Variables

Create `backend/python/.env` and provide:

```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
GEMINI_API_KEY=your-gemini-api-key
```

The Node gateway loads `backend/python/.env` by default. You may also create `backend/node/.env` if you want Node-specific overrides such as `PORT` or `PYTHON_API_URL`.

## Quick Start

### 1. Run the Python Backend

```bash
cd backend/python
pip install -r requirements.txt
uvicorn main:app --reload
```

The FastAPI service runs at [http://localhost:8000](http://localhost:8000).

### 2. Run the Node Gateway

```bash
cd backend/node
npm install
node server.js
```

The web app runs at [http://localhost:3000](http://localhost:3000).

Open the app through the Node gateway. Do not open the HTML files directly, because the frontend depends on `/api/config` and `/api/v1/horoscope`.

## Runtime Flow

- Node serves files from `frontend/`
- Frontend loads Supabase and Google config from `/api/config`
- Frontend sends horoscope requests to `/api/v1/horoscope`
- Node proxies horoscope requests to the Python FastAPI service on port 8000
- Python calculates astrology context and calls Gemini

## Tech Stack

- Frontend: HTML5, CSS3, Tailwind CDN, Vanilla JavaScript
- Gateway: Node.js, Express
- AI Backend: Python, FastAPI
- AI Model: Gemini 2.5 Flash
- Auth/Database: Supabase
- Astrology Library: Flatlib
- Markdown Rendering: Marked.js

## Key Features

- Supabase authentication and profile storage
- AI-powered love horoscope chat
- Real-time planetary transit context
- Dynamic relationship-status theme in the chat page
- Markdown rendering for AI responses
- Node gateway that centralizes frontend hosting and API routing

## Notes

- `.env` files are ignored by git and should not be committed.
- If Gemini returns a quota error, check the Gemini API key, project quota, and billing settings.
- If port 8000 is already in use, stop the existing Python backend process before starting `uvicorn` again.


---
**Developed by:** GameNoiAutomation Group (FRA502 Web Programming)


---
**Developed by:** GameNoiAutomation Group (FRA502 Web Programming)
