# ScholAR: Research Decision Engine

AI-powered research intelligence that analyzes, critiques, simulates, and makes research decisions.

## 🚀 Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up API key

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama3-70b-8192
```

### 3. Run the application

```bash
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000`

## 🏗️ Architecture

```
├── main.py                    # FastAPI entry point
├── requirements.txt           # Python dependencies
├── .env                       # API keys (create from .env.example)
├── prompts/
│   └── system_prompt.py       # Core AI identity + output formats
├── services/
│   ├── llm.py                 # Groq API client (httpx)
│   ├── prompt_builder.py      # Mode-specific prompt construction
│   └── simulation_engine.py   # Deterministic heuristic engine
├── routes/
│   ├── analyze.py             # /api/analyze endpoint
│   ├── simulate.py            # /api/simulate endpoint
│   └── decision.py            # /api/decision endpoint
├── utils/
│   └── response_formatter.py  # JSON validation + defaults
├── templates/
│   └── index.html             # Frontend template
└── static/
    ├── style.css              # Design system
    └── app.js                 # Frontend logic
```

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Frontend UI |
| `/api/health` | GET | Health check |
| `/api/analyze` | POST | Full analysis + critique + simulation |
| `/api/simulate` | POST | Heuristic + AI simulation |
| `/api/decision` | POST | Quick READ/SKIP |

## 🎯 Core Features

- **Full Analysis**: Summary, insights, critique, failure scenarios
- **Break This Paper**: Find failure points and edge cases
- **Simulation Engine**: Deterministic heuristic + AI simulation
- **Trust Score**: High/Medium/Low confidence assessment
- **Visual Impact Bars**: See noise/data/bias effects at a glance

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, httpx
- **Frontend**: Jinja2 templates, Vanilla CSS/JS
- **AI**: Groq API (llama3-70b-8192)
