from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.schemas import (
    BulkDeleteTicketRequest,
    BulkUpdateTicketRequest,
    CreateTicketRequest,
    MessageResponse,
    TicketListResponse,
    TicketResponse,
    UpdateTicketRequest,
)
from app.services.ticket_service import (
    bulk_create_tickets,
    bulk_delete_tickets,
    bulk_update_tickets,
    create_ticket,
    delete_ticket,
    get_all_ticket,
    update_ticket,
)

router = APIRouter()


@router.post("/tickets", response_model=TicketResponse)
def create_ticket_api(ticket: CreateTicketRequest, db: Session = Depends(get_db)):
    return create_ticket(ticket, db)


@router.post("/tickets/bulk")
def bulk_create_tickets_api(
    tickets: list[CreateTicketRequest],
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return bulk_create_tickets(tickets, current_user, db)


@router.delete("/tickets/bulk")
def bulk_delete_tickets_api(
    tickets: list[BulkDeleteTicketRequest],
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return bulk_delete_tickets(tickets, current_user, db)


@router.patch("/tickets/bulk")
def bulk_update_ticket_api(
    tickets: list[BulkUpdateTicketRequest],
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return bulk_update_tickets(tickets, current_user, db)


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
