from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.schemas import (
    BulkDeleteTicketRequest,
    BulkUpdateTicketRequest,
    CreateTicketRequest,
    MessageResponse,
    TicketListResponse,
    TicketResponse,
    UpdateTicketRequest,
    AssignTicketRequest,
)
from app.services.ticket_service import (
    bulk_create_tickets,
    bulk_delete_tickets,
    bulk_update_tickets,
    create_ticket,
    delete_ticket,
    download_attachment,
    get_all_ticket,
    get_ticket_attachments,
    update_ticket,
    upload_attachment,
    assign_ticket,
)

router = APIRouter()


@router.post("/tickets", response_model=TicketResponse)
def create_ticket_api(ticket: CreateTicketRequest, db: Session = Depends(get_db)):
    return create_ticket(ticket, db)

@router.patch("/tickets/{ticket_id}/assign", response_model= TicketResponse)
def assign_ticket_route(
    ticket_id: int,
    assignee_id: AssignTicketRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("agent", "admin")) 
):
    return assign_ticket(ticket_id, assignee_id , db)

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


@router.post("/tickets/{ticket_id}/attachments")
def upload_attachment_api(
    ticket_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return upload_attachment(ticket_id, file, current_user, db)


@router.get("/tickets/{ticket_id}/attachments")
def get_ticket_attachments_api(
    ticket_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_ticket_attachments(
        ticket_id,
        current_user,
        db,
    )


@router.get("/attachments/{attachment_id}/download", response_class=FileResponse)
def download_attachment_api(
    attachment_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return download_attachment(
        attachment_id,
        current_user,
        db,
    )
