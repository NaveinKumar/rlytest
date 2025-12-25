import os
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/env-check")
def env_check():
    rpc = os.getenv("SOLANA_RPC")
    mint = os.getenv("TOKEN_MINT")
    key = os.getenv("AIRDROP_PRIVATE_KEY_B58")

    return {
        "SOLANA_RPC_present": rpc is not None,
        "TOKEN_MINT_present": mint is not None,
        "AIRDROP_PRIVATE_KEY_B58_present": key is not None,
        "SOLANA_RPC_value": rpc if rpc else None,
        "TOKEN_MINT_value": mint if mint else None,
        "PRIVATE_KEY_length": len(key) if key else None,
    }
