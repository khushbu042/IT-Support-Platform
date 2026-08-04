from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="user")

    

class Ticket(Base):
    __tablename__ = "tickets" 
    id: Mapped[int] = mapped_column(primary_key=True) 
    title: Mapped[str] = mapped_column(String(255)) 
    description: Mapped[str] = mapped_column(String) 
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(back_populates="tickets")
