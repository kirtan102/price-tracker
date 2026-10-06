from datetime import timedelta
from hashlib import sha256
from jose import jwt
from pwdlib import PasswordHash
from .config import settings
from .db import now

password_hash=PasswordHash.recommended()
def hash_password(v): return password_hash.hash(v)
def verify_password(v,h): return password_hash.verify(v,h)
def make_access(user_id): return jwt.encode({"sub":str(user_id),"exp":now()+timedelta(minutes=settings.jwt_access_minutes)},settings.jwt_secret,algorithm="HS256")
def make_refresh():
    import secrets
    raw=secrets.token_urlsafe(48); return raw, sha256(raw.encode()).hexdigest()
def decode_access(token): return jwt.decode(token,settings.jwt_secret,algorithms=["HS256"])

