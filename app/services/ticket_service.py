from app.schemas import CreateTicketRequest
from sqlalchemy.orm import Session, joinedload
from app.models import User, Ticket
from fastapi import HTTPException

def create_ticket(ticket: CreateTicketRequest, db: Session):
  
    existing_user = db.query(User).filter(
          User.id == ticket.user_id
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    new_ticket = Ticket(
        title = ticket.title,
        description = ticket.description,
        user_id = ticket.user_id
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket

def get_all_ticket(db: Session):
    existing_tickets = db.query(Ticket).options(joinedload(Ticket.user)).all()
    return existing_tickets




    

