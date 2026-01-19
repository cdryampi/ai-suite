# AI Suite - Backend Virtual Environment Setup

## ⚠️ IMPORTANTE: ENTORNO VIRTUAL DE PYTHON

Este proyecto usa un entorno virtual de Python para el backend.

### Ubicación del Entorno Virtual
```
backend/venv/
```

### ✅ Entorno Virtual YA ESTÁ CREADO

El entorno virtual está configurado con las dependencias básicas:
- Flask 3.1.2
- PyYAML 6.0.3  
- python-dotenv 1.2.1

### 🚨 RECORDATORIO PARA AGENTES/PRUEBAS DEL BACKEND

**SIEMPRE** que necesites ejecutar código Python del backend:

1. **Usa el intérprete del venv:**
   ```bash
   # Windows
   backend/venv/Scripts/python.exe <comando>
   
   # Unix/Mac
   backend/venv/bin/python <comando>
   ```

2. **O activa el venv primero:**
   ```bash
   # Windows PowerShell
   cd backend
   .\venv\Scripts\Activate.ps1
   
   # Windows CMD
   cd backend
   venv\Scripts\activate.bat
   
   # Unix/Mac
   cd backend
   source venv/bin/activate
   ```

### Ejemplos de Uso Correcto

**❌ INCORRECTO:**
```bash
cd backend
python run.py  # Usará Python del sistema (sin dependencias)
```

**✅ CORRECTO:**
```bash
cd backend
venv/Scripts/python.exe run.py  # Windows
# o
source venv/bin/activate && python run.py  # Unix/Mac
```

**✅ CORRECTO para pruebas:**
```bash
backend/venv/Scripts/python.exe -c "import flask; print('OK')"
```

### Para Instalar Más Dependencias

```bash
# Windows
backend/venv/Scripts/pip.exe install nombre-paquete

# Unix/Mac  
backend/venv/bin/pip install nombre-paquete
```

### Verificar Estado del Venv

```bash
backend/venv/Scripts/python.exe --version
backend/venv/Scripts/pip.exe list
```

### Recrear el Venv (si es necesario)

```bash
cd backend
rm -rf venv  # Unix/Mac
# o
rmdir /s venv  # Windows CMD

python -m venv venv
venv/Scripts/pip.exe install -r requirements.txt
```

---

**Documentación completa:** `backend/VENV_README.md`
