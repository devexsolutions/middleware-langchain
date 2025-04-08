from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

DOLIBARR_API_URL = os.getenv("DOLIBARR_API_URL")
DOLIBARR_API_KEY = os.getenv("DOLIBARR_API_KEY")

class PromptRequest(BaseModel):
    prompt: str

prompt_template = PromptTemplate(
    input_variables=["user_prompt"],
    template="""
Eres un asistente que interpreta preguntas sobre obras. Si te preguntan:

"{user_prompt}"

Responde SOLO con una acción JSON. Ejemplo:
{{"accion": "listar_obras"}}
    """
)

llm = OpenAI(temperature=0)
chain = LLMChain(llm=llm, prompt=prompt_template)

@app.post("/prompt")
async def interpretar_prompt(request: PromptRequest):
    respuesta = chain.run(user_prompt=request.prompt)
    try:
        result = eval(respuesta)
    except Exception as e:
        return {"error": str(e), "respuesta": respuesta}
    
    if result.get("accion") == "listar_obras":
        headers = {
            "DOLAPIKEY": DOLIBARR_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.get(f"{DOLIBARR_API_URL}/obras", headers=headers)
        return response.json()
    
    return {"mensaje": "Acción aún no implementada", "accion": result.get("accion")}