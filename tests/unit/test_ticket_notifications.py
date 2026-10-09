from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.infrastructure.rabbitmq.publisher import build_ticket_assigned_event
from app.infrastructure.rabbitmq.serializer import dumps, loads
from app.schemas.events import TicketAssignedEvent
from app.workers.notifications.handlers import handle_ticket_assigned


def test_ticket_assigned_event_round_trip():
    event = TicketAssignedEvent(
        ticket_id=12,
        ticket_title="Printer is down",
        agent_id=4,
        agent_name="Alex Agent",
        agent_email="agent@example.com",
        assigned_by_id=1,
        assigned_at=datetime.now(timezone.utc),
        message_id="msg-1",
    )

    loaded = loads(dumps(event), TicketAssignedEvent)

    assert loaded.ticket_id == 12
    assert loaded.agent_email == "agent@example.com"


def test_build_ticket_assigned_event_uses_agent_email():
    ticket = SimpleNamespace(id=9, title="Login issue")
    agent = SimpleNamespace(id=3, name="Jamie", email="jamie@example.com")

    event = build_ticket_assigned_event(ticket, agent, assigned_by_id=1)

    assert event.agent_email == "jamie@example.com"
    assert event.ticket_title == "Login issue"
    assert event.message_id


@patch("app.workers.notifications.handlers.send_email")
def test_handler_emails_the_assigned_agent(send_email):
    event = TicketAssignedEvent(
        ticket_id=12,
        ticket_title="Printer is down",
        agent_id=4,
        agent_name="Alex Agent",
        agent_email="agent@example.com",
        assigned_by_id=1,
        assigned_at=datetime.now(timezone.utc),
        message_id="msg-1",
    )

    handle_ticket_assigned(event)

    send_email.assert_called_once()
    kwargs = send_email.call_args.kwargs
    assert kwargs["to_email"] == "agent@example.com"
    assert "Ticket #12" in kwargs["subject"]
