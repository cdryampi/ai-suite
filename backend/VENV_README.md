# Backend Development Environment

## Python Virtual Environment

Este proyecto utiliza un entorno virtual de Python ubicado en `backend/venv/`.

### Activación del Entorno Virtual

**Windows (PowerShell):**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
cd backend
venv\Scripts\activate.bat
```

**Unix/Mac:**
```bash
cd backend
source venv/bin/activate
```

### Verificación

Una vez activado, deberías ver `(venv)` al principio de tu prompt.

Verifica que las dependencias estén instaladas:
```bash
python -c "import flask; import yaml; print('OK')"
```

### Ejecución del Servidor

**IMPORTANTE:** Siempre activa el entorno virtual antes de ejecutar el servidor:

```bash
# Activar venv primero
cd backend
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Luego ejecutar
python run.py
```

### Instalación de Dependencias

Para instalar todas las dependencias del proyecto:

```bash
# Con el venv activado
pip install -r requirements.txt
```

### Dependencias Básicas Instaladas

- Flask 3.1.2
- PyYAML 6.0.3
- python-dotenv 1.2.1

### Notas para Desarrollo

1. **Siempre usa el entorno virtual** cuando trabajes con el backend
2. El venv está en `.gitignore` y NO se sube al repositorio
3. Otros desarrolladores deben crear su propio venv con `python -m venv venv`
4. Si agregas nuevas dependencias, actualiza `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   ```

### Troubleshooting

**Error: "Flask no encontrado"**
→ Activa el entorno virtual primero

**Error: "No module named 'yaml'"**
→ Instala dependencias: `pip install -r requirements.txt`

**Error de permisos en Windows**
→ Ejecuta PowerShell como administrador o usa: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
