# 🔮 MuteGPT - AI-Powered Personalized Horoscope Chatbot

MuteGPT is a personalized horoscope web application that integrates the intelligence of **Gemini AI** with Thai and International astrological sciences. The system features real-time planetary position calculations powered by a Dual-Backend architecture (Node.js + Python).

## 🏗️ Project Structure

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

## 🚀 Quick Start

### 1. Prepare API Keys
Create a `.env` file in the `backend/node/` directory by copying from `.envEXAMPLE` and provide the following information:
- `GOOGLE_CLIENT_ID`: Required for Google Login system.
- `SUPABASE_URL` & `SUPABASE_ANON_KEY`: For member database management.
- `GEMINI_API_KEY`: For the AI divination engine.

### 2. Install and Run Node.js Backend (Frontend Server)
Serves web pages and handles basic connectivity and authentication.
```bash
cd backend/node
npm install
node server.js
```
*Server running at: [http://localhost:3000](http://localhost:3000)*

### 3. Install and Run Python Backend (AI Brain)
Handles astronomical calculations via `flatlib` and processes predictions through the `Gemini API`.
```bash
cd backend/python
pip install -r requirements.txt
python main.py
```
or

```bash
cd backend/python
pip install -r requirements.txt
uvicorn main:app --reload
```

*API running at: [http://localhost:8000](http://localhost:8000)*

---

## 🛠️ Tech Stack

- **Frontend:** HTML5, CSS3 (Tailwind CSS), Vanilla JavaScript
- **Backend 1:** Node.js + Express (Gateway & Auth)
- **Backend 2:** Python + FastAPI (AI Logic & Astrology)
- **AI Model:** Google Gemini 2.5 Flash
- **Database:** Supabase (PostgreSQL + Auth)
- **Astronomy Library:** Flatlib (Swiss Ephemeris)
- **Formatting:** Marked.js (Markdown support in chat)

## ✨ Key Features
- **Real-time Transits:** Calculates actual planetary positions at the moment of interaction for professional astrological accuracy.
- **Markdown Chat:** A sleek chat interface that supports bold text, headers, and list formatting.
- **Dynamic Theme:** The chat interface automatically changes themes based on the user's relationship status (Single, Talking, Taken, or Recently Broken Up).
- **Dual Logic:** Separates UI rendering from AI processing for optimal performance and scalability.

---
**Developed by:** GameNoiAutomation Group (FRA502 Web Programming)
