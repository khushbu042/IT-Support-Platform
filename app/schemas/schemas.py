from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from app.models import UserRole, UserStatus


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=12)
    confirm_password: str
    role: UserRole
    department: str | None = Field(default=None, min_length=1)
    team: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole
    department: str | None = None
    team: str | None = None
    status: UserStatus

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

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



# class CreateTicketRequest(BaseModel):
#     title: str
#     description: str
#
#
# class UpdateTicketRequest(BaseModel):
#     title: str | None = None
#     description: str | None = None
#
#
# class TicketResponse(BaseModel):
#     id: int
#     title: str
#     description: str
#     user_id: int
#
#
# class TicketWithEmployeeResponse(TicketResponse):
#     employee: EmployeeResponse
#
#
# class TicketListResponse(BaseModel):
#     page: int
#     limit: int
#     total: int
#     total_pages: int
#     data: list[TicketResponse]
#
#
# class BulkUpdateTicketRequest(BaseModel):
#     id: int
#     title: Optional[str] = None
#     description: Optional[str] = None
#
#
# class BulkDeleteTicketRequest(BaseModel):
#     id: int
