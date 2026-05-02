from sqlalchemy import Column, Integer, String, UniqueConstraint
from .database import Base


class User(Base):
    __tablename__="users"

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Email 
    email = Column(
        String(255),
        index=True,
        nullable=False,
        unique=True

    )

    # username
    username = Column(
        String(50),
        index=True,
        nullable=False,
        unique=True

    )

    # Table-level constraints
    __table_args__=(
        UniqueConstraint('email', name='uq_user_email'),
        UniqueConstraint('username', name='uq_user_username'),
    )

    def __repr__(self):
        return f"<User (id={self.id}, email={self.email}, username={self.username})>"