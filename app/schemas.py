
from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


class CreateTicketRequest(BaseModel):
    title: str
    description: str
    user_id: int


class UpdateTicketRequest(BaseModel):
    title: str | None = None
    description: str | None = None


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    user_id: int


class TicketWithUserResponse(TicketResponse):
    user: UserResponse


class TicketListResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    data: list[TicketResponse]
