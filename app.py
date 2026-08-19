from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from rag.generation import generate_answer  # noqa: E402
from rag.retrieval import search  # noqa: E402

app = FastAPI()

RETRIEVAL_K = 15


class Pergunta(BaseModel):
    pergunta: str


class Resposta(BaseModel):
    resposta: str


@app.post("/perguntar", response_model=Resposta)
def perguntar(payload: Pergunta) -> Resposta:
    chunks = search(payload.pergunta, k=RETRIEVAL_K)
    resposta = generate_answer(payload.pergunta, chunks)
    return Resposta(resposta=resposta)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
