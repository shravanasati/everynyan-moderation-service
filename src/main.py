from contextlib import asynccontextmanager
from fastapi import FastAPI

# from src.engines.bert import BertModerationEngine
# from src.engines.textblob import TextBlobModerationEngine
from pydantic import BaseModel

from src.engines.ibm_max import IBMMaxModerationEngine

engine: IBMMaxModerationEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = IBMMaxModerationEngine()
    yield
    await engine.close()


app = FastAPI(lifespan=lifespan)


class ModerationRequest(BaseModel):
    content: str


class ModerationResponse(BaseModel):
    purge: bool


@app.post("/moderate")
async def moderate(req: ModerationRequest) -> ModerationResponse:
    # engine = TextBlobModerationEngine(-0.3)
    # engine = BertModerationEngine()
    return ModerationResponse(purge=await engine.should_purge(req.content))
