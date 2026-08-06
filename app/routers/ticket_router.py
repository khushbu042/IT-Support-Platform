from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.schemas import (
    CreateTicketRequest,
    MessageResponse,
    TicketListResponse,
    TicketResponse,
    UpdateTicketRequest,
)
from app.services.ticket_service import (
    create_ticket,
    delete_ticket,
    get_all_ticket,
    update_ticket,
)

router = APIRouter()


@router.post("/tickets", response_model=TicketResponse)
def create_ticket_api(ticket: CreateTicketRequest, db: Session = Depends(get_db)):
    return create_ticket(ticket, db)


@router.get("/tickets", response_model=TicketListResponse)
def get_ticket_api(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user_id: int | None = Query(None),
    title: str | None = Query(None),
    sort_by: str = Query("id"),
    order: str = Query("asc"),
    db: Session = Depends(get_db),
):
    return get_all_ticket(page, limit, user_id, title, sort_by, order, db)


@router.patch("/tickets/{ticket_id}", response_model=TicketResponse)
def update_ticket_api(
    ticket_id: int,
    ticket: UpdateTicketRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_ticket(ticket_id, ticket, current_user, db)


@router.delete("/tickets/{ticket_id}", response_model=MessageResponse)
def delete_ticket_api(
    ticket_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_ticket(ticket_id, current_user, db)
