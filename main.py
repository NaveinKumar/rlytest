from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, auth
import base64, json, os


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Init Firebase Admin once
firebase_app = None

def init_firebase():
    global firebase_app
    if firebase_app:
        return

    b64 = os.environ.get("FIREBASE_ADMIN_KEY_B64")
    if not b64:
        raise RuntimeError("Missing FIREBASE_ADMIN_KEY_B64")

    key_json = base64.b64decode(b64).decode("utf-8")
    cred = credentials.Certificate(json.loads(key_json))
    firebase_app = firebase_admin.initialize_app(cred)

def verify_user(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")

    token = auth_header.split(" ")[1]
    decoded = auth.verify_id_token(token)
    return decoded  # contains email, uid

class WalletRequest(BaseModel):
    wallet: str

@app.post("/airdrop")
async def airdrop(req: WalletRequest, request: Request):
    init_firebase()
    user = verify_user(request)

    email = user.get("email")
    if not email:
        raise HTTPException(400, "Email not found")
    return {
    "message": "User verified",
    "email": email
}


@app.get("/health")
async def health():
    return {"status": "ok"}
