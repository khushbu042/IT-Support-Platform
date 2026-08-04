from app.schemas import CreateTicketRequest, TicketWithUserResponse, TicketResponse
from app.database import get_db
from app.services.ticket_service import create_ticket, get_all_ticket
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
 
router = APIRouter()

@router.post("/tickets", response_model=TicketResponse)
def create_ticket_api(ticket: CreateTicketRequest, db: Session = Depends(get_db)):
    return create_ticket(ticket, db)

@router.get("/tickets", response_model=list[TicketWithUserResponse])
def get_ticket_api(db: Session = Depends(get_db)):
    return get_all_ticket(db)
