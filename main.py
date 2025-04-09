from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

DOLIBARR_API_URL = os.getenv("DOLIBARR_API_URL")
DOLIBARR_API_KEY = os.getenv("DOLIBARR_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
async def root():
    return {"mensaje": "Middleware BIM activo 🚀"}

prompt_template = PromptTemplate(
    input_variables=["user_prompt"],
    template="""
Eres un asistente que interpreta preguntas sobre obras y facturación. Si te preguntan:

"{user_prompt}"

Responde SOLO con una acción JSON. Ejemplos:
{"accion": "listar_obras"}
{"accion": "facturas_pendientes"}
{"accion": "facturas_pendientes_usuario", "usuario": "Juan Perez"}
    """
)

llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
chain: RunnableSequence = prompt_template | llm

@app.post("/prompt")
async def interpretar_prompt(request: PromptRequest):
    respuesta = chain.invoke({"user_prompt": request.prompt})
    try:
        result = eval(respuesta.content)  # cuidado con eval en producción
    except Exception as e:
        return {"error": str(e), "respuesta": respuesta.content}

    headers = {
        "Authorization": f"Bearer {DOLIBARR_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    if result.get("accion") == "listar_obras":
        response = requests.get(f"{DOLIBARR_API_URL}/obras", headers=headers)
        return response.json()

    elif result.get("accion") == "facturas_pendientes":
        params = {"limit": 100, "sqlfilters": "fk_statut=1"}
        response = requests.get(f"{DOLIBARR_API_URL}/invoices", headers=headers, params=params)
        return {
            "status_code": response.status_code,
            "respuesta": response.text,
            "json": response.json() if response.headers.get("Content-Type", "").startswith("application/json") else None
        }

    elif result.get("accion") == "facturas_pendientes_usuario":
        usuario_nombre = result.get("usuario")
        thirdparty_response = requests.get(f"{DOLIBARR_API_URL}/thirdparties", headers=headers)
        thirdparties = thirdparty_response.json()
        tercero = next((tp for tp in thirdparties if usuario_nombre.lower() in tp.get("name", "").lower()), None)

        if tercero:
            params = {"limit": 100, "sqlfilters": f"fk_soc={tercero['id']} AND fk_statut=1"}
            response = requests.get(f"{DOLIBARR_API_URL}/invoices", headers=headers, params=params)
            return {
                "status_code": response.status_code,
                "respuesta": response.text,
                "json": response.json() if response.headers.get("Content-Type", "").startswith("application/json") else None
            }
        else:
            return {"mensaje": f"No se encontró el cliente '{usuario_nombre}'"}

    return {"mensaje": "Acción aún no implementada", "accion": result.get("accion")}
