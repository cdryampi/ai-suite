# AI Suite Architecture

AI Suite is a local-first AI application platform designed to run LLM-powered workflows securely on your machine. It follows a client-server architecture with a clear separation of concerns.

## High-Level Overview

```mermaid
graph TD
    User[User / Browser] <--> Frontend[Astro Frontend :4321]
    Frontend <--> API[Flask Backend :5000]
    
    subgraph "Backend Core"
        API --> JobRunner[Job Runner]
        API --> Planner[LLM Planner]
        JobRunner --> JobStore[Job Store (In-Memory)]
        Planner --> LLM[LLM Client (Ollama/LM Studio)]
        Planner --> Tools[Tool Registry]
    end
    
    subgraph "Storage"
        JobStore --> Artifacts[Artifact Manager (File System)]
    end
```

## Backend (Flask)

Located in `backend/`, the core logic runs on Python/Flask.

### Key Components

1.  **Mini Apps (`app.miniapps`)**: Self-contained modules that define a specific workflow. Each mini app inherits from `BaseMiniApp`.
    *   *Example*: `realestate_ads`
2.  **Planner (`app.core.planner`)**: The orchestration engine. It uses an LLM to break down high-level goals into executable steps using registered tools.
3.  **Job System (`app.core.job_store`)**: Manages the lifecycle of long-running tasks. Jobs are tracked in memory, and their outputs are persisted as artifacts.
4.  **Tool Registry (`app.core.tool_registry`)**: A secure registry of allowed Python functions (Tools) that the LLM can invoke.
    *   *Tools*: `scrape_url`, `llm_generate`, etc.

### Data Flow

1.  **Request**: Frontend sends `POST /api/miniapps/{id}/run`.
2.  **Execution**: Backend creates a `Job` (PENDING) and submits it to the thread pool.
3.  **Processing**: The Mini App workflow executes (scraping, analyzing, generating).
4.  **Artifacts**: Results are saved to `outputs/jobs/{job_id}/artifacts/`.
5.  **Polling**: Frontend polls `/api/miniapps/{id}/status/{job_id}` for logs and completion.

## Frontend (Astro)

Located in `frontend/`, the UI is built with Astro 5.0, React 19, and TailwindCSS 4.0.

### Key Components

1.  **Layouts**: `Sidebar.astro` provides navigation and system status.
2.  **Dashboard**: `index.astro` lists available mini apps.
3.  **MiniAppRunner**: A React component (`MiniAppRunner.tsx`) that handles the execution lifecycle:
    *   Displays configuration form.
    *   Triggers execution.
    *   Polls for real-time logs.
    *   Displays and links to generated artifacts.

### Design System

*   **Theme**: High-contrast, accessible design using OKLCH color space.
*   **Typography**: Inter font family with large base size (18px) for readability.
*   **Framework**: shadcn/ui patterns for consistent components.

## Data Persistence

*   **Jobs**: Currently in-memory (reset on restart).
*   **Artifacts**: Persisted to disk in `outputs/`.
*   **Configuration**: `backend/config/settings.py` loads from `default.yaml`, `local.yaml`, and `.env`.
