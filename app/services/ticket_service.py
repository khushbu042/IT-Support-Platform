import math

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models import Ticket, User
from app.schemas import (
    BulkDeleteTicketRequest,
    BulkUpdateTicketRequest,
    CreateTicketRequest,
    UpdateTicketRequest,
)


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


def bulk_create_tickets(
    tickets: list[CreateTicketRequest],
    current_user: User,
    db: Session,
):
    if not tickets:
        raise HTTPException(status_code=400, detail=" At least one ticket is required.")

    ticket_objects = []

    for ticket in tickets:
        new_ticket = Ticket(
            title=ticket.title, description=ticket.description, user_id=current_user.id
        )
        ticket_objects.append(new_ticket)

    try:
        db.add_all(ticket_objects)
        db.commit()
    except:
        db.rollback()
        raise

    return ticket_objects


def bulk_update_tickets(
    update_tickets: list[BulkUpdateTicketRequest],
    current_user: User,
    db: Session,
):
    if not update_tickets:
        raise HTTPException(
            status_code=400, detail=" At least one ticket is required to update"
        )

    requested_ticket_ids = {update.id for update in update_tickets}

    tickets = db.query(Ticket).filter(Ticket.id.in_(requested_ticket_ids)).all()

    db_ticket_ids = {ticket.id for ticket in tickets}

    missing_ids = requested_ticket_ids - db_ticket_ids

    if missing_ids:
        raise HTTPException(
            status_code=404, detail=f"Tickets not found: {list(missing_ids)}"
        )

    for ticket in tickets:
        if ticket.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to update one or more tickets"
            )

    ticket_map = {ticket.id: ticket for ticket in tickets}

    for update in update_tickets:
        ticket = ticket_map[update.id]

        update_data = update.model_dump(exclude_unset=True, exclude={"id"})

        for key, value in update_data.items():
            setattr(ticket, key, value)

    try:
        db.commit()
        db.refresh(tickets)
    except:
        db.rollback()
        raise

    return tickets


def bulk_delete_tickets(
    delete_tickets: list[BulkDeleteTicketRequest],
    current_user: User,
    db: Session,
):
    if not delete_tickets:
        raise HTTPException(
            status_code=400, detail=" At least one ticket is required to delete"
        )

    unique_delete_ids = {ticket.id for ticket in delete_tickets}

    db_tickets = db.query(Ticket).filter(Ticket.id.in_(unique_delete_ids)).all()

    db_ticket_ids = {ticket.id for ticket in db_tickets}

    missing_ids = unique_delete_ids - db_ticket_ids

    if missing_ids:
        raise HTTPException(
            status_code=404, detail=f"Tickets not found: {list(missing_ids)}"
        )

    for ticket in db_tickets:
        if ticket.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to delete one or more tickets",
            )

    deleted_count = (
        db.query(Ticket)
        .filter(Ticket.id.in_(unique_delete_ids))
        .delete(synchronize_session=False)
    )

    try:
        db.commit()
    except:
        db.rollback()
        raise

    return {"message": f"{deleted_count} tickets deleted successfully"}
