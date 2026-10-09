import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

import aio_pika
from aio_pika import DeliveryMode, Message

from app.config import RABBITMQ_URL
from app.infrastructure.rabbitmq.serializer import dumps
from app.infrastructure.rabbitmq.topology import (
    TICKET_ASSIGNED_ROUTING_KEY,
    declare_topology,
    get_events_exchange,
)
from app.models import Ticket, User
from app.schemas.schemas import TicketAssignedEvent

logger = logging.getLogger(__name__)


def build_ticket_assigned_event(
    ticket: Ticket,
    agent: User,
    assigned_by_id: int | None = None,
) -> TicketAssignedEvent:
    return TicketAssignedEvent(
        ticket_id=ticket.id,
        ticket_title=ticket.title,
        agent_id=agent.id,
        agent_name=agent.name,
        agent_email=agent.email,
        assigned_by_id=assigned_by_id,
        assigned_at=datetime.now(timezone.utc),
        message_id=str(uuid4()),
    )


async def publish_ticket_assigned_async(event: TicketAssignedEvent) -> None:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await declare_topology(channel)
        exchange = await get_events_exchange(channel)
        await exchange.publish(
            Message(
                body=dumps(event),
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                message_id=event.message_id,
                headers={"x-retry": 0},
            ),
            routing_key=TICKET_ASSIGNED_ROUTING_KEY,
        )


def publish_ticket_assigned(
    ticket: Ticket,
    agent: User,
    assigned_by_id: int | None = None,
) -> None:
    event = build_ticket_assigned_event(ticket, agent, assigned_by_id)
    try:
        asyncio.run(publish_ticket_assigned_async(event))
    except RuntimeError:
        asyncio.get_event_loop().create_task(publish_ticket_assigned_async(event))
    except Exception:
        logger.exception(
            "Failed to publish ticket.assigned event for ticket_id=%s",
            ticket.id,
        )
