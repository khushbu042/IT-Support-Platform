import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    OPERATIONS_AGENT = "Operations Agent"
    TEAM_LEAD = "Team Lead"
    MANAGER = "Manager"
    SLA_ADMINISTRATOR = "SLA Administrator"
    SYSTEM_ADMINISTRATOR = "System Administrator"

class UserStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="userstatus"),
        default=UserStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


# class Ticket(Base):
#     __tablename__ = "tickets"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     title: Mapped[str] = mapped_column(String(255))
#     description: Mapped[str] = mapped_column(String)
#     user_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
#
#     employee: Mapped["Employee"] = relationship(back_populates="tickets")
#
#     attachments: Mapped[list["Attachment"]] = relationship(back_populates="ticket")
#
#
# class Attachment(Base):
#     __tablename__ = "attachments"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
#     filename: Mapped[str] = mapped_column(String(255))
#     file_path: Mapped[str] = mapped_column(String(255))
#     content_type: Mapped[str] = mapped_column(String(255))
#     file_size: Mapped[int] = mapped_column()
#     created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
#
#     ticket: Mapped["Ticket"] = relationship(back_populates="attachments")
