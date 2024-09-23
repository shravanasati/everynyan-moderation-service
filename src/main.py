from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

# from src.engines.bert import BertModerationEngine
# from src.engines.textblob import TextBlobModerationEngine
from pydantic import BaseModel

from src.engines.ibm_max import IBMMaxModerationEngine

async_client: httpx.AsyncClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global async_client
    async_client = httpx.AsyncClient()
    yield
    await async_client.aclose()


app = FastAPI(lifespan=lifespan)


class ModerationRequest(BaseModel):
    content: str


class ModerationResponse(BaseModel):
    purge: bool


@app.post("/moderate")
async def moderate(req: ModerationRequest) -> ModerationResponse:
    # engine = TextBlobModerationEngine(-0.3)
    # engine = BertModerationEngine()
    engine = IBMMaxModerationEngine(async_client)
    return ModerationResponse(purge=await engine.should_purge(req.content))
