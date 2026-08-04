from pydantic import BaseModel

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

class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    user_id: int

class TicketWithUserResponse(TicketResponse):
    user: UserResponse

    

