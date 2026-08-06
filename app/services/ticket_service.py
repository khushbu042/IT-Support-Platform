import math

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models import Ticket, User
from app.schemas import CreateTicketRequest, UpdateTicketRequest


def create_ticket(ticket: CreateTicketRequest, db: Session):

    existing_user = db.query(User).filter(User.id == ticket.user_id).first()

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    new_ticket = Ticket(
        title=ticket.title, description=ticket.description, user_id=ticket.user_id
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket


def update_ticket(
    ticket_id: int, ticket_update: UpdateTicketRequest, current_user: User, db: Session
):
    existing_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    # ticket = db.get(Ticket, ticket_id)

    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if existing_ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You don't have permission to update this ticket."
        )

    update_data = ticket_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, details="No fields provided for update")

    for key, value in update_data.items():
        setattr(existing_ticket, key, value)

    try:
        db.commit()
        db.refresh(existing_ticket)
    except Exception:
        db.rollback()
        raise

    return existing_ticket


def delete_ticket(ticket_id: int, current_user: User, db: Session):
    # existing_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    ticket = db.get(Ticket, ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You don't have permission to delete this ticket."
        )

    db.delete(ticket)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Ticket deleted successfully"}


def get_all_ticket(page, limit, user_id, title, sort_by, order, db: Session):

    allowed_sort_fields = {
        "id": Ticket.id,
        "title": Ticket.title,
        "user_id": Ticket.user_id,
    }

    allowed_orders = {"asc", "desc"}

    offset = (page - 1) * limit

    query = db.query(Ticket)

    if user_id is not None:
        query = query.filter(Ticket.user_id == user_id)

    if title:
        query = query.filter(Ticket.title.ilike(f"%{title}%"))

    total = query.count()

    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if order not in allowed_orders:
        raise HTTPException(status_code=400, detail="Invalid order field")

    column = allowed_sort_fields[sort_by]

    query = query.order_by(column.asc() if order == "asc" else column.desc())

    existing_tickets = (
        query.options(joinedload(Ticket.user)).offset(offset).limit(limit).all()
    )

    total_pages = math.ceil(total / limit)

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "data": existing_tickets,
    }
