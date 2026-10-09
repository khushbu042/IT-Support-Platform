import logging
import math
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from app.infrastructure.rabbitmq.publisher import publish_ticket_assigned
from app.services.s3_service import upload_file, delete_file, get_file, s3_client, generate_download_url
from fastapi.responses import StreamingResponse

from app.models import (
    AttachmentStatus,
    Ticket,
    TicketAttachment,
    TicketPriority,
    TicketStatus,
    User,
)
from app.schemas import (
    BulkDeleteTicketRequest,
    BulkUpdateTicketRequest,
    CreateTicketRequest,
    UpdateTicketRequest,
    AssignTicketRequest,
)

UPLOAD_DIR = Path("app/uploads/tickets")
ALLOWED_FILES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
CHUNK_SIZE = 1024 * 1024  # 1 MB
logger = logging.getLogger(__name__)

def create_ticket(ticket: CreateTicketRequest, db: Session):
    existing_customer = db.query(User).filter(User.id == ticket.customer_id).first()

    if not existing_customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    new_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        customer_id=ticket.customer_id,
        assigned_agent_id=ticket.assigned_agent_id,
        sla_deadline=ticket.sla_deadline,
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    # publish "ticket.created" event here later (for notifications)

    return new_ticket

def assign_ticket(
    ticket_id: int,
    assignee: AssignTicketRequest,
    db: Session,
    assigned_by_id: int | None = None,
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    assignee_id = assignee.assignee_id
    assignee_user = db.query(User).filter(User.id == assignee_id).first()
    if not assignee_user:
        raise HTTPException(status_code=404, detail="Assignee not found")

    # optional but recommended: only allow assigning to users with an "agent"/"admin" role
    if assignee_user.role not in ("agent", "admin"):
        raise HTTPException(status_code=400, detail="User is not eligible to be assigned tickets")

    ticket.assigned_agent_id = assignee_id

    if ticket.status == TicketStatus.open:
        ticket.status = TicketStatus.pending

    db.commit()
    db.refresh(ticket)

    try:
        publish_ticket_assigned(ticket, assignee_user, assigned_by_id=assigned_by_id)
    except Exception:
        logger.exception(
            "Ticket %s assigned but notification event was not published",
            ticket.id,
        )

    return ticket

def update_ticket(
    ticket_id: int,
    ticket_update: UpdateTicketRequest,
    current_user: User,
    db: Session,
):
    existing_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if existing_ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You don't have permission to update this ticket."
        )

    update_data = ticket_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

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
    ticket = db.get(Ticket, ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.customer_id != current_user.id:
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


def get_all_ticket(page, limit, customer_id, title, sort_by, order, db: Session):
    allowed_sort_fields = {
        "id": Ticket.id,
        "title": Ticket.title,
        "customer_id": Ticket.customer_id,
        "status": Ticket.status,
        "priority": Ticket.priority,
        "assigned_agent_id": Ticket.assigned_agent_id,
    }

    allowed_orders = {"asc", "desc"}

    offset = (page - 1) * limit

    query = db.query(Ticket)

    if customer_id is not None:
        query = query.filter(Ticket.customer_id == customer_id)

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
        query.options(
            joinedload(Ticket.customer),
            joinedload(Ticket.assigned_agent),
        )
        .offset(offset)
        .limit(limit)
        .all()
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
        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only create tickets for your own customer account.",
            )

        new_ticket = Ticket(
            title=ticket.title,
            description=ticket.description,
            status=ticket.status,
            priority=ticket.priority,
            customer_id=ticket.customer_id,
            assigned_agent_id=ticket.assigned_agent_id,
            sla_deadline=ticket.sla_deadline,
        )
        ticket_objects.append(new_ticket)

    try:
        db.add_all(ticket_objects)
        db.commit()
    except Exception:
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
        if ticket.customer_id != current_user.id:
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
    except Exception:
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
        if ticket.customer_id != current_user.id:
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
    except Exception:
        db.rollback()
        raise

    return {"message": f"{deleted_count} tickets deleted successfully"}


def upload_attachment(
    ticket_id: int,
    file: UploadFile,
    current_user: User,
    db: Session,
):
    ticket = db.get(Ticket, ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket Not found",
        )

    if ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to add attachment to this ticket",
        )

    original_filename = file.filename or ""

    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_FILES:
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    if file.content_type != ALLOWED_FILES[extension]:
        raise HTTPException(
            status_code=400, detail="File extension and content type do not match"
        )

    safe_filename = f"{uuid4()}{extension}"

    object_key = f"tickets/{ticket_id}/{safe_filename}"

    file_size = 0

    try:
        while True:
            chunk = file.file.read(CHUNK_SIZE)

            if not chunk:
                break

            file_size += len(chunk)

            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413, detail="File size exceeds 5 MB limit"
                )

        file.file.seek(0)

        upload_file(
            file.file,
            object_key,
        )

    except Exception:
        delete_file(object_key)
        raise

    attachment = TicketAttachment(
        ticket_id=ticket_id,
        uploaded_by=current_user.id,
        file_name=original_filename,
        file_url=object_key,
        file_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        status=AttachmentStatus.uploading,
    )

    try:
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
    except Exception:
        db.rollback()
        delete_file(object_key)
        raise

    return attachment


def get_ticket_attachments(
    ticket_id: int,
    current_user: User,
    db: Session,
):
    ticket = db.get(Ticket, ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    if ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view attachments for this ticket",
        )

    attachments = (
        db.query(TicketAttachment).filter(TicketAttachment.ticket_id == ticket_id).all()
    )

    return attachments


def download_attachment(
    attachment_id: int,
    current_user: User,
    db: Session,
):
    attachment = db.get(TicketAttachment, attachment_id)

    if not attachment:
        raise HTTPException(
            status_code=404,
            detail="Attachment not found",
        )

    ticket = db.get(Ticket, attachment.ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    if ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to download this attachment",
        )

    download_url = generate_download_url(attachment.file_url)

    return {
        "filename": attachment.file_name,
        "content_type": attachment.file_type,
        "file_size": attachment.file_size,
        "download_url": download_url,
    }


def delete_attachment(
    attachment_id: int,
    current_user: User,
    db: Session,
):
    attachment = db.get(TicketAttachment, attachment_id)

    if not attachment:
        raise HTTPException(
            status_code=404,
            detail="Attachment not found",
        )

    ticket = db.get(Ticket, attachment.ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    if ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this attachment",
        )

    file_path = Path(attachment.file_url)

    if file_path.exists():
        file_path.unlink()

    try:
        db.delete(attachment)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "Attachment deleted successfully"}
