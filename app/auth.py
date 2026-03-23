import os
import hashlib
import secrets
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.models import User
from app.database import get_db

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# We removed pwd_context completely!
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_password_hash(password: str) -> str:
    # 1. Generate a random 16-byte salt
    salt = os.urandom(16)
    
    # 2. Hash the password using PBKDF2 (600,000 iterations is highly secure)
    hashed = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt, 
        600_000
    )
    
    # 3. Combine the salt and the hash into one string to save in the DB
    return f"{salt.hex()}:{hashed.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # 1. Split the saved string back into the salt and the hash
        salt_hex, original_hash_hex = hashed_password.split(':')
        salt = bytes.fromhex(salt_hex)
        
        # 2. Hash the user's login attempt using the EXACT SAME salt
        new_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            plain_password.encode('utf-8'), 
            salt, 
            600_000
        )
        
        # 3. Compare them safely to prevent timing attacks
        return secrets.compare_digest(new_hash.hex(), original_hash_hex)
    except ValueError:
        # If the database hash is somehow formatted wrong, fail safely
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user