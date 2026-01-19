# How to Create a Mini App

This guide walks you through the process of creating a new Mini App in AI Suite.

A Mini App consists of:
1.  **Backend Logic**: A Python class inheriting from `BaseMiniApp`.
2.  **API Routes**: A Flask Blueprint to expose the app.
3.  **Frontend**: A new entry in the dashboard (and potentially a custom UI).

## 1. Backend Implementation

Create a new directory in `backend/app/miniapps/{app_id}/`.

### Step 1: Create the Workflow Class

Create `workflow.py`:

```python
from typing import Any, Dict, Optional
from ...base import BaseMiniApp, MiniAppMetadata, MiniAppResult

class MyMiniApp(BaseMiniApp):
    def get_metadata(self) -> MiniAppMetadata:
        return MiniAppMetadata(
            id="my_app",
            name="My Awesome App",
            description="Does something amazing with AI.",
            version="1.0.0",
            tags=["productivity"]
        )
    
    def run(self, input_data: str, variant: int = 1, options: Optional[Dict] = None) -> MiniAppResult:
        # 1. Create Job
        job = self.job_store.create(f"{self.metadata.id}_v{variant}")
        
        # 2. Log progress
        self._log(job.id, "Starting workflow...")
        
        # 3. Use Tools
        # llm_tool = self.tool_registry.get_tool("llm_generate")
        # result = llm_tool.execute(...)
        
        # 4. Save Artifacts
        # self.artifact_manager.save_text(job.id, "output.txt", result)
        
        return self._create_result(
            status="ok",
            logs=["Done!"],
            artifacts=[],
            result={"data": "success"}
        )
```

### Step 2: Create API Routes

Create `routes.py`:

```python
from flask import Blueprint, request, jsonify
from .workflow import MyMiniApp

bp = Blueprint("my_app", __name__, url_prefix="/api/miniapps/my_app")

def init_miniapp(job_store, llm_client, tool_registry, artifact_manager):
    return MyMiniApp(job_store, llm_client, tool_registry, artifact_manager)

@bp.route("/run", methods=["POST"])
def run():
    # Implement run handler (copy pattern from realestate_ads)
    pass

# Implement /status and /artifact endpoints
```

### Step 3: Register the App

Update `backend/app/miniapps/registry.py`:

```python
def register_miniapps(app: Flask) -> None:
    # ... existing apps
    
    from app.miniapps.my_app import bp as my_app_bp, init_miniapp
    
    my_miniapp = init_miniapp(job_store, llm_client, tool_registry, artifact_manager)
    app.config["MY_MINIAPP"] = my_miniapp
    app.register_blueprint(my_app_bp)
```

## 2. Frontend Integration

### Step 1: Add to Dashboard

Update `frontend/src/pages/index.astro`:

```javascript
const miniApps = [
  // ... existing apps
  {
    id: 'my_app',
    title: 'My Awesome App',
    description: 'Does something amazing with AI.',
    icon: Sparkles, // Import icon from lucide-react
    status: 'ready',
    tags: ['productivity']
  }
];
```

### Step 2: Add Route Path

Update `frontend/src/pages/miniapps/[id].astro`:

```javascript
export function getStaticPaths() {
  return [
    // ... existing paths
    { params: { id: 'my_app' } },
  ];
}

const miniApps = {
  // ... existing apps
  my_app: {
    title: 'My Awesome App',
    description: '...',
    icon: Sparkles
  }
};
```

That's it! Your mini app is now live and executable via the generic runner.
