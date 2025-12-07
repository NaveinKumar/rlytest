from fastapi import FastAPI
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
    print("Airdrop request received:", req.wallet)
    return {"message": "Airdrop successful!", "wallet": req.wallet}
