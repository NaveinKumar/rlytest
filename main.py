import os
import base58
import struct

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta
from solana.rpc.api import Client

# ========================
# App setup
# ========================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# ENV VARS (LOAD ONCE)
# ========================
SOLANA_RPC = os.getenv("SOLANA_RPC")
TOKEN_MINT = os.getenv("TOKEN_MINT")
AIRDROP_PRIVATE_KEY_B58 = os.getenv("AIRDROP_PRIVATE_KEY_B58")

if not SOLANA_RPC or not TOKEN_MINT or not AIRDROP_PRIVATE_KEY_B58:
    raise RuntimeError(
        "Missing env vars: SOLANA_RPC / TOKEN_MINT / AIRDROP_PRIVATE_KEY_B58"
    )

# ========================
# Solana setup
# ========================
client = Client(SOLANA_RPC)

MINT_ADDRESS = Pubkey.from_string(TOKEN_MINT)

airdrop_keypair = Keypair.from_bytes(
    base58.b58decode(AIRDROP_PRIVATE_KEY_B58)
)
AIRDROP_PUBKEY = airdrop_keypair.pubkey()

TOKEN_2022_PROGRAM_ID = Pubkey.from_string(
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
)
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string(
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
)

# ========================
# Models
# ========================
class WalletRequest(BaseModel):
    wallet: str

# ========================
# Helpers
# ========================
def find_ata(owner: Pubkey, mint: Pubkey) -> Pubkey:
    return Pubkey.find_program_address(
        [bytes(owner), bytes(TOKEN_2022_PROGRAM_ID), bytes(mint)],
        ASSOCIATED_TOKEN_PROGRAM_ID
    )[0]

# ========================
# Airdrop Endpoint
# ========================
@app.post("/airdrop")
async def airdrop(req: WalletRequest):
    try:
        receiver_pubkey = Pubkey.from_string(req.wallet)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    sender_ata = find_ata(AIRDROP_PUBKEY, MINT_ADDRESS)
    receiver_ata = find_ata(receiver_pubkey, MINT_ADDRESS)

    # Sender ATA must exist
    if client.get_account_info(sender_ata).value is None:
        raise HTTPException(status_code=500, detail="Airdrop wallet ATA missing")

    # Fetch decimals
    mint_info = client.get_token_supply(MINT_ADDRESS).value
    decimals = mint_info.decimals
    raw_amount = 1 * (10 ** decimals)

    # Check balance
    sender_balance = int(
        client.get_token_account_balance(sender_ata).value.amount
    )
    if sender_balance < raw_amount:
        raise HTTPException(status_code=400, detail="Airdrop exhausted")

    instructions = []

    # Create receiver ATA if needed
    if client.get_account_info(receiver_ata).value is None:
        instructions.append(
            Instruction(
                program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
                accounts=[
                    AccountMeta(AIRDROP_PUBKEY, True, True),
                    AccountMeta(receiver_ata, False, True),
                    AccountMeta(receiver_pubkey, False, False),
                    AccountMeta(MINT_ADDRESS, False, False),
                    AccountMeta(Pubkey.from_string("11111111111111111111111111111111"), False, False),
                    AccountMeta(TOKEN_2022_PROGRAM_ID, False, False),
                    AccountMeta(Pubkey.from_string("SysvarRent111111111111111111111111111111111"), False, False),
                ],
                data=b""
            )
        )

    # TransferChecked
    instructions.append(
        Instruction(
            program_id=TOKEN_2022_PROGRAM_ID,
            accounts=[
                AccountMeta(sender_ata, False, True),
                AccountMeta(MINT_ADDRESS, False, False),
                AccountMeta(receiver_ata, False, True),
                AccountMeta(AIRDROP_PUBKEY, True, False),
            ],
            data=struct.pack("<BQB", 12, raw_amount, decimals)
        )
    )

    recent = client.get_latest_blockhash().value.blockhash

    tx = Transaction.new_signed_with_payer(
        instructions=instructions,
        payer=AIRDROP_PUBKEY,
        signing_keypairs=[airdrop_keypair],
        recent_blockhash=recent
    )

    sig = client.send_raw_transaction(bytes(tx)).value

    return {
        "message": "Airdrop successful",
        "wallet": req.wallet,
        "signature": sig,
        "explorer": f"https://explorer.solana.com/tx/{sig}",
    }
