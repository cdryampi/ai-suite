# AI Suite

**A local-first AI application platform.**

AI Suite allows you to run powerful AI workflows securely on your own machine. It combines a robust Python backend with a modern, accessible frontend.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Astro](https://img.shields.io/badge/astro-5.0-orange.svg)

## 🚀 Features

- **Local-First**: All processing happens on your machine. Connects to local LLMs (Ollama, LM Studio).
- **Mini Apps**: Modular, task-specific applications.
    - 🏠 **Real Estate Ad Generator**: Scrapes listings and writes ads.
    - 📊 **Market Research**: (Coming Soon)
- **Job System**: Robust job tracking with real-time logs and artifact management.
- **Modern UI**: Accessible, high-contrast dashboard built with Astro and React.

## 🛠️ Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Ollama or LM Studio (running locally)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Unix
source venv/bin/activate

pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your LLM settings
```

Start the server:
```bash
python run.py
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:4321` to access the dashboard.

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [How to Create a Mini App](docs/CREATE_MINIAPP.md)
- [API Reference](docs/API.md)

## 🏗️ Project Structure

```
/
├── backend/            # Flask API & Core Logic
│   ├── app/
│   │   ├── core/       # Planner, JobStore, ToolRegistry
│   │   ├── miniapps/   # Mini App Implementations
│   │   └── tools/      # Reusable Tools (LLM, Scrape)
│   └── run.py
├── frontend/           # Astro/React UI
│   ├── src/
│   │   ├── components/ # React Components (Runner, Sidebar)
│   │   └── pages/      # Astro Routes
└── docs/               # Documentation
```

## 🤝 Contributing

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current progress and active tasks.
