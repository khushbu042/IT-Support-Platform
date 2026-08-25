from sqlalchemy import (
    Column, Integer, String, Text, Boolean, 
    ForeignKey, DateTime, Enum, BigInteger
)
from datetime import datetime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base
import enum


# ---------- ENUMS ----------
class UserRole(str, enum.Enum):
    customer = "customer"
    agent = "agent"
    admin = "admin"

class TicketStatus(str, enum.Enum):
    open = "open"
    pending = "pending"
    resolved = "resolved"
    closed = "closed"

class TicketPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class AttachmentStatus(str, enum.Enum):
    uploading = "uploading"
    scanning = "scanning"
    ready = "ready"
    rejected = "rejected"


# ---------- USER ----------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    # tickets this user CREATED (as customer)
    tickets_created = relationship(
        "Ticket",
        foreign_keys="Ticket.customer_id",
        back_populates="customer"
    )

    # tickets this user is ASSIGNED to (as agent)
    tickets_assigned = relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_agent_id",
        back_populates="assigned_agent"
    )

    comments = relationship("TicketComment", back_populates="sender")
    attachments = relationship("TicketAttachment", back_populates="uploader")

# ---------- TICKET ---------- 
class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus),
        default=TicketStatus.open,
        nullable=False,
        index=True,
    )

    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority),
        default=TicketPriority.medium,
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    sla_deadline: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    customer: Mapped["User"] = relationship(
        "User", foreign_keys=[customer_id], back_populates="tickets_created"
    )

    assigned_agent: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assigned_agent_id], back_populates="tickets_assigned"
    )

    comments = relationship(
        "TicketComment", back_populates="ticket", cascade="all, delete-orphan"
    )

    attachments = relationship(
        "TicketAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )

# ---------- TICKET COMMENT ----------
class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    ticket: Mapped["Ticket"] = relationship(
        "Ticket",
        back_populates="comments"
    )

    sender = relationship(
        "User",
        back_populates="comments"
    )

    attachments = relationship(
        "TicketAttachment",
        back_populates="comment",
        cascade="all, delete-orphan"
    )


# ---------- TICKET ATTACHMENT ----------
class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Nullable because the file can be attached
    # directly to the ticket or to a specific comment.
    comment_id: Mapped[int | None] = mapped_column(
        ForeignKey("ticket_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    file_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    
    file_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[AttachmentStatus] = mapped_column(
        Enum(AttachmentStatus),
        default=AttachmentStatus.uploading,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    ticket = relationship("Ticket", back_populates="attachments")
    comment = relationship("TicketComment", back_populates="attachments")
    uploader = relationship("User", back_populates="attachments")

