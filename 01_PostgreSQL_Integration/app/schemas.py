from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=50
    )

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(
        default = None,
        min_length=3,
        max_length=50
    )

class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str

    class Config:
        from_attributes=True