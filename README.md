# Middleware LangChain para ERP

Este proyecto es un middleware en FastAPI con LangChain que interpreta prompts en lenguaje natural y llama a la API REST de Dolibarr.

## Instalación

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Variables de entorno

Crear archivo `.env` basado en `.env.example`.