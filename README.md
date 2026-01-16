# AI Suite

A **local-first AI Suite** composed of multiple "mini apps" (AI-powered tools),
each behaving almost like an independent application but sharing a common backend,
orchestration layer, and UI shell.

## 🎯 Project Goals

- **Local-first**: All processing happens on your machine
- **Deterministic workflows**: Reproducible, auditable AI operations
- **Strong conventions**: Clear patterns for extending the system
- **Modular mini apps**: Each tool is self-contained with its own prompts and logic
- **LLM orchestrated**: A "Planner" LLM coordinates workflows within strict boundaries

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Astro)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Dashboard  │  │  Mini App   │  │  Settings   │             │
│  │             │  │   Runner    │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │ REST API
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND (Flask)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Job Runner                             │  │
│  │  ┌─────────┐  ┌─────────────┐  ┌─────────────────────┐   │  │
│  │  │ Planner │─▶│ Tool Registry│─▶│ Tool Execution      │   │  │
│  │  │  (LLM)  │  │             │  │ (scrape/img/video)  │   │  │
│  │  └─────────┘  └─────────────┘  └─────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Mini Apps                              │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────┐    │  │
│  │  │ realestate_ads │  │    (future)    │  │ (future) │    │  │
│  │  └────────────────┘  └────────────────┘  └──────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Ollama    │  │  LM Studio  │  │  Other LLM  │             │
│  │  (local)    │  │  (local)    │  │  providers  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
ai-suite/
├── backend/          # Python Flask API
│   ├── app/          # Application code
│   │   ├── core/     # Job runner, LLM client, planner
│   │   ├── tools/    # Available tool implementations
│   │   ├── miniapps/ # Individual mini applications
│   │   └── routes/   # API endpoints
│   └── config/       # Configuration files
├── frontend/         # Astro web application
│   └── src/
│       ├── pages/    # Route pages
│       ├── components/
│       └── lib/      # API client, utilities
├── docs/             # Architecture and API documentation
├── outputs/          # Generated artifacts storage
└── scripts/          # Development scripts
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Ollama or LM Studio running locally (for LLM features)

### Setup (Windows)

```powershell
# Clone and enter directory
cd ai-suite

# Run setup script
.\scripts\setup.ps1

# Start development servers
.\scripts\dev.ps1
```

### Setup (Unix/Mac)

```bash
# Clone and enter directory
cd ai-suite

# Run setup script
chmod +x scripts/setup.sh scripts/dev.sh
./scripts/setup.sh

# Start development servers
./scripts/dev.sh
```

### Manual Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend
cd frontend
npm install

# Run (in separate terminals)
# Terminal 1:
cd backend && python run.py

# Terminal 2:
cd frontend && npm run dev
```

## 🔌 API Overview

All mini apps follow a uniform API pattern:

```
POST /api/miniapps/<app_id>/run

Request:
{
  "input": "string",
  "variant": 1,
  "options": {}
}

Response:
{
  "status": "ok|error",
  "job_id": "string",
  "logs": ["string"],
  "artifacts": [
    {"type": "text|image|video|json", "label": "string", "path": "string"}
  ],
  "result": {}
}
```

See [docs/API.md](docs/API.md) for complete API reference.

## 📖 Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and patterns
- [API.md](docs/API.md) - Complete API reference
- [WORKFLOWS.md](docs/WORKFLOWS.md) - Workflow system documentation
- [EXTENDING.md](docs/EXTENDING.md) - Guide for adding new mini apps

## 🔧 Configuration

Copy `backend/config/default.yaml` to `backend/config/local.yaml` and modify:

```yaml
llm:
  provider: ollama  # or lmstudio
  base_url: http://localhost:11434
  model: llama3.2

output:
  base_path: ./outputs
  max_size_mb: 100
```

## 📝 Mini Apps

### Available

| App | Description | Status |
|-----|-------------|--------|
| `realestate_ads` | Generate real estate advertisements | ✅ Complete |

### Planned

- `social_media_posts` - Generate social media content
- `product_descriptions` - E-commerce product copy
- `email_campaigns` - Marketing email generator

## 🧪 Development

### Running Tests

```bash
cd backend
pytest tests/ -v
```

### Code Style

- Backend: Black + isort
- Frontend: Prettier + ESLint

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

This project is designed for extension via vibecode/Codex. See [docs/EXTENDING.md](docs/EXTENDING.md) for contribution guidelines.
