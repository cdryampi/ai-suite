# AI Suite - Archivo de Generación del Proyecto Completo

Este documento contiene instrucciones para generar TODOS los archivos del proyecto.

## Estado Actual

✅ **Archivos Creados:**
- README.md
- .gitignore  
- .editorconfig
- backend/requirements.txt
- backend/run.py
- backend/app/__init__.py
- backend/config/default.yaml
- backend/config/settings.py
- backend/config/__init__.py
- backend/app/core/__init__.py
- backend/app/routes/__init__.py
- backend/app/tools/__init__.py
- backend/app/miniapps/__init__.py
- backend/app/utils/__init__.py
- backend/tests/__init__.py

## ⚠️ Archivos Pendientes (Críticos para Funcionar)

Por limitaciones de token en esta sesión, los siguientes archivos DEBEN ser creados:

### Backend Core (Crítico - ~15 archivos)
1. `backend/app/core/llm_client.py` - Cliente LLM
2. `backend/app/core/job_store.py` - Almacenamiento de trabajos
3. `backend/app/core/job_runner.py` - Ejecutor de trabajos
4. `backend/app/core/tool_registry.py` - Registro de herramientas
5. `backend/app/core/planner.py` - Planificador LLM
6. `backend/app/core/artifacts.py` - Gestor de artefactos

### Backend Routes (~3 archivos)
7. `backend/app/routes/health.py` - Endpoints de salud
8. `backend/app/routes/api.py` - API principal
9. `backend/app/routes/miniapps.py` - Lista de mini apps

### Backend Tools (~5 archivos)
10. `backend/app/tools/base.py` - Clase base de herramientas
11. `backend/app/tools/llm_tool.py` - Herramienta de generación LLM
12. `backend/app/tools/scrape.py` - Herramienta de scraping
13. `backend/app/tools/image_gen.py` - Generación de imágenes (stub)
14. `backend/app/tools/video_gen.py` - Generación de videos (stub)

### Mini App: realestate_ads (~8 archivos)
15. `backend/app/miniapps/base.py` - Clase base workflows
16. `backend/app/miniapps/registry.py` - Registro de mini apps
17. `backend/app/miniapps/realestate_ads/routes.py` - Rutas API
18. `backend/app/miniapps/realestate_ads/workflow.py` - Lógica del workflow
19. `backend/app/miniapps/realestate_ads/steps.yaml` - Definición del workflow
20. `backend/app/miniapps/realestate_ads/README.md` - Documentación
21-24. `backend/app/miniapps/realestate_ads/prompts/*.txt` - 4 archivos de prompts

### Frontend (~30+ archivos)
25. `frontend/package.json`
26. `frontend/astro.config.mjs`
27. `frontend/tailwind.config.js`
28. `frontend/tsconfig.json`
29-50. Componentes, páginas, layouts, lib, etc.

### Documentación (~4 archivos)
51. `docs/ARCHITECTURE.md`
52. `docs/API.md`  
53. `docs/WORKFLOWS.md`
54. `docs/EXTENDING.md`

### Scripts (~4 archivos)
55. `scripts/setup.ps1` (Windows)
56. `scripts/setup.sh` (Unix)
57. `scripts/dev.ps1` (Windows)
58. `scripts/dev.sh` (Unix)

## 🚀 Opción 1: Generación Manual

Copia el código de cada archivo desde la respuesta anterior del asistente.

## 🤖 Opción 2: Usar el Generador Automático (RECOMENDADO)

Ejecuta el script de Python que creará TODOS los archivos:

```bash
python scripts/create_complete_project.py
```

Este script (por crear) contendrá todo el código embebido y generará la estructura completa.

## 📝 Próximos Pasos Después de la Generación

1. **Instalar dependencias del backend:**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Unix
   pip install -r requirements.txt
   ```

2. **Instalar dependencias del frontend:**
   ```bash
   cd frontend
   npm install
   ```

3. **Iniciar Ollama** (en otra terminal):
   ```bash
   ollama serve
   ollama run llama3.2
   ```

4. **Iniciar servidores de desarrollo:**
   ```bash
   # Windows
   .\scripts\dev.ps1
   
   # Unix
   ./scripts/dev.sh
   ```

5. **Acceder a la aplicación:**
   - Frontend: http://localhost:4321
   - Backend API: http://localhost:5000

## ⚠️ Nota Importante

Los errores de LSP (Language Server Protocol) que aparecen son NORMALES hasta que:
1. Se instalen las dependencias de Python (`pip install -r requirements.txt`)
2. Se instalen las dependencias de Node (`npm install`)

