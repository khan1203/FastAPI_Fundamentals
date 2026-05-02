import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from bson import ObjectId

from .database import SessionLocal
from .mongodb import connect_to_mongodb, close_mongodb_connection, get_mongodb
from .models import User
from .schemas import UserCreate, UserOut, Token, ActivityLogCreate, ActivityLogOut
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME"),
    description="Hybrid SQL + NoSQL FastAPI Application with PostgreSQL and MongoDB",
    version="1.0.0"
)

security = HTTPBearer()


@app.on_event("startup")
async def startup_event():
    await connect_to_mongodb()


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongodb_connection()


# Dependency: PostgreSQL session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency: Get current authenticated user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"X-WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}


@app.post("/auth/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log the login-activity to MongoDB
    mongodb = get_mongodb()
    await mongodb.user_activity_logs.insert_one({
        "user_id": user.id,
        "action": "login",
        "timestamp": datetime.utcnow(),
        "metadata": {}
    })

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/profile", response_model=UserOut)
async def get_profile(current_user: User = Depends(get_current_user)):
    # Automatic logging: log profile view
    mongodb = get_mongodb()
    await mongodb.user_activity_logs.insert_one({
        "user_id": current_user.id,
        "action": "profile_view",
        "timestamp": datetime.utcnow(),
        "metadata": {}
    })

    return current_user


@app.get("/users", response_model=list[UserOut])
async def get_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Automatic logging: log users list view
    mongodb = get_mongodb()
    await mongodb.user_activity_logs.insert_one({
        "user_id": current_user.id,
        "action": "users_list_view",
        "timestamp": datetime.utcnow(),
        "metadata": {}
    })

    users = db.query(User).all()
    return users


@app.post("/logs", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_custom_log(
    log_data: ActivityLogCreate,
    current_user: User = Depends(get_current_user)
):
    mongodb = get_mongodb()

    log_document = {
        "user_id": current_user.id,
        "action": log_data.action,
        "timestamp": datetime.utcnow(),
        "metadata": log_data.metadata
    }

    result = await mongodb.user_activity_logs.insert_one(log_document)

    return {
        "message": "Custom activity log created",
        "log_id": str(result.inserted_id)
    }


@app.get("/logs", response_model=list[ActivityLogOut])
async def get_my_logs(
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    mongodb = get_mongodb()

    cursor = mongodb.user_activity_logs.find(
        {"user_id": current_user.id}
    ).sort("timestamp", -1).limit(limit)

    logs = await cursor.to_list(length=limit)

    # Convert ObjectId to string for JSON serialization
    for log in logs:
        log["_id"] = str(log["_id"])

    return logs


@app.get("/users/{user_id}/logs", response_model=list[ActivityLogOut])
async def get_user_logs(
    user_id: int,
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # Check if user exists in PostgreSQL
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    # Get logs from MongoDB
    mongodb = get_mongodb()
    cursor = mongodb.user_activity_logs.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(limit)

    logs = await cursor.to_list(length=limit)

    # Convert ObjectId to string
    for log in logs:
        log["_id"] = str(log["_id"])

    return logs
