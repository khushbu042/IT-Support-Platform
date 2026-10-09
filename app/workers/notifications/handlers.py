from app.schemas.schemas import TicketAssignedEvent
from app.services.email_service import send_email


def handle_ticket_assigned(event: TicketAssignedEvent) -> None:
    send_email(
        to_email=event.agent_email,
        subject=f"Ticket #{event.ticket_id} assigned to you",
        body=(
            f"Hello {event.agent_name},\n\n"
            f"You have been assigned ticket #{event.ticket_id}: {event.ticket_title}.\n"
        ),
    )
