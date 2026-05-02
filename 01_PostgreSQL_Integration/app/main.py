import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .database import SessionLocal
from .models import User
from .schemas import UserCreate, UserOut, UserUpdate

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "User Management System"),
    description="A CRUD API for User Management with PostgreSQL",
    version="1.0.0"
)

# Dependency: Database Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/ping")
def ping():
    return {'status': 'OK', 'message':'pong'}

# CREATE: add an user
@app.post('/users', response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session=Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.email == payload.email) | (User.username == payload.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email or Username already exists."
        )
    
    # Creating new user and 
    user = User(email=payload.email, username=payload.username)
    db.add(user)     # add to db-session
    db.commit()      # save to database
    db.refresh(user) # Reload from database (get the ID)

    return user

# READ: get all users
@app.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()
    return users

# READ: Get single user by ID
@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


# UPDATE: Modify existing user
@app.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    # Get existing user
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Update email if provided and different
    if payload.email and payload.email != user.email:
        # Check if email already taken
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(
                status_code=400,
                detail="Email already in use"
            )
        user.email = payload.email

    # Update username if provided and different
    if payload.username and payload.username != user.username:
        # Check if username already taken
        if db.query(User).filter(User.username == payload.username).first():
            raise HTTPException(
                status_code=400,
                detail="Username already in use"
            )
        user.username = payload.username

    db.add(user)        # Mark as modified
    db.commit()         # Save changes
    db.refresh(user)    # Reload from database

    return user


# DELETE: Remove a user
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db.delete(user)     # Mark for deletion
    db.commit()         # Execute deletion

    return None         # 204 responses have no body
