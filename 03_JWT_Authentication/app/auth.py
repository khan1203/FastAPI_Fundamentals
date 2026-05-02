import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from datetime import timedelta, datetime
from typing import Optional
from jose import jwt, JWTError

load_dotenv()

# JWT config
SECRET_KEY= os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(hashed_password:str, plain_password:str)->bool:
    return pwd_context.verify(hashed_password, plain_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta]=None)->str:
    to_encode = data.copy()

    if expires_delta:
        expire =  datetime.utcnow() +  expires_delta
    else:
        expire = datetime.utcnow()+ timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def decode_access_token(token: str)->Optional[str]:
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str =payload.get("sub")
        return email
    except:
        return JWTError

