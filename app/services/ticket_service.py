import math
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from app.services.s3_service import upload_file, delete_file, get_file, s3_client, generate_download_url
from fastapi.responses import StreamingResponse

from app.models import Attachment, Employee, Ticket
from app.schemas import (
    BulkDeleteTicketRequest,
    BulkUpdateTicketRequest,
    CreateTicketRequest,
    UpdateTicketRequest,
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


def create_ticket(ticket: CreateTicketRequest, db: Session):

    existing_user = db.query(Employee).filter(Employee.id == ticket.user_id).first()

    if not existing_user:
        raise HTTPException(status_code=404, detail="Employee not found")

    new_ticket = Ticket(
        title=ticket.title, description=ticket.description, user_id=ticket.user_id
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket


def update_ticket(
    ticket_id: int, ticket_update: UpdateTicketRequest, current_user: Employee, db: Session
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


def delete_ticket(ticket_id: int, current_user: Employee, db: Session):
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
        query.options(joinedload(Ticket.employee)).offset(offset).limit(limit).all()
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
    current_user: Employee,
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
    current_user: Employee,
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
    current_user: Employee,
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


def upload_attachment(
    ticket_id: int,
    file: UploadFile,
    current_user: Employee,
    db: Session,
):
    ticket = db.get(Ticket, ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket Not found",
        )

    if ticket.user_id != current_user.id:
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
        # Read file in chunks to validate size
        while True:
            chunk = file.file.read(CHUNK_SIZE)

            if not chunk:
                break

            file_size += len(chunk)

            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413, detail="File size exceeds 5 MB limit"
                )

        # Reset file pointer before uploading to S3
        file.file.seek(0)

        upload_file(
            file.file,
            object_key,
        )

    except Exception:
        # Remove S3 object if upload partially/fully succeeded
        delete_file(object_key)
        raise

    attachment = Attachment(
        ticket_id=ticket_id,
        filename=original_filename,
        file_path=object_key,
        content_type=file.content_type,
        file_size=file_size,
    )

    try:
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
    except:
        db.rollback()

        # DB failed, so remove S3 object
        delete_file(object_key)
        
        raise

    return attachment


def get_ticket_attachments(
    ticket_id: int,
    current_user: Employee,
    db: Session,
):
    ticket = db.get(Ticket, ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    if ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view attachments for this ticket",
        )

    attachments = db.query(Attachment).filter(Attachment.ticket_id == ticket_id).all()

    return attachments


def download_attachment(
    attachment_id: int,
    current_user: Employee,
    db: Session,
):
    attachment = db.get(Attachment, attachment_id)

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

    if ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to download this attachment",
        )

    
    download_url = generate_download_url(attachment.file_path)

    # except FileNotFoundError:
    #     raise HTTPException(
    #         status_code=404,
    #         detail="Attachment not found in S3",
    #     )
    
    # return StreamingResponse(
    #     s3_object["Body"],
    #     media_type=attachment.content_type,
    #     headers={
    #         "Content-Disposition": f'attachement; filename="{attachment.filename}"'
    #     },
    # )
    return {
        "filename": attachment.filename,
        "content_type": attachment.content_type,
        "file_size": attachment.file_size,
        "download_url": download_url,
    }
   


def delete_attachment(
    attachment_id: int,
    current_user: Employee,
    db: Session,
):
    attachment = db.get(Attachment, attachment_id)

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

    if ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this attachment",
        )

    file_path = Path(attachment.file_path)

    if file_path.exists():
        file_path.unlink()

    try:
        db.delete(attachment)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "Attachment deleted successfully"}
