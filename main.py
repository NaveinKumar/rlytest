from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WalletRequest(BaseModel):
    wallet: str

@app.post("/airdrop")
async def airdrop(req: WalletRequest):
    raise HTTPException(
        status_code=403,
        detail="Airdrop temporarily disabled"
    )

@app.get("/health")
async def health():
    return {"status": "ok"}
