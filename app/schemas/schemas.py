from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from app.models import UserRole, TicketStatus, TicketPriority, AttachmentStatus


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password_hash: str = Field(..., min_length=12)
    confirm_password: str
    role: UserRole

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password_hash != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password_hash: str

class LoginResponseData(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type prefix")
    expires_in: int = Field(..., description="Token lifetime in seconds", examples=[3600])
    user: UserResponse


class LoginResponseSchema(BaseModel):
    success: bool = Field(default=True, description="Indicates api operation status")
    message: str = Field(default="Login successful", description="Human-readable response message")
    data: LoginResponseData


class MessageResponse(BaseModel):
    message: str


class TicketAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    comment_id: int | None = None
    uploaded_by: int
    file_name: str
    file_url: str
    file_type: str
    file_size: int
    status: AttachmentStatus
    created_at: datetime


class CreateTicketRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    status: TicketStatus = TicketStatus.open
    priority: TicketPriority = TicketPriority.medium
    customer_id: int
    assigned_agent_id: int | None = None
    sla_deadline: datetime | None = None

class AssignTicketRequest(BaseModel):
    assignee_id: int
   


class UpdateTicketRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TicketStatus | None = None
    priority: TicketPriority | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    customer_id: int
    assigned_agent_id: int | None = None
    sla_deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime
    attachments: list[TicketAttachmentResponse] = []


class TicketListResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    data: list[TicketResponse]


class BulkUpdateTicketRequest(BaseModel):
    id: int
    title: str | None = None
    description: str | None = None


class BulkDeleteTicketRequest(BaseModel):
    id: int

class TicketAssignedEvent(BaseModel):
    ticket_id: int
    ticket_title: str
    agent_id: int
    agent_name: str
    agent_email: EmailStr
    assigned_by_id: int | None = None
    assigned_at: datetime
    message_id: str = Field(..., min_length=1)


