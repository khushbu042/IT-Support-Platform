from aio_pika import ExchangeType
from aio_pika.abc import AbstractChannel, AbstractExchange, AbstractQueue

TICKETS_EVENTS_EXCHANGE = "tickets.events"
TICKETS_RETRY_EXCHANGE = "tickets.retry"
TICKETS_DLX_EXCHANGE = "tickets.dlx"

TICKET_ASSIGNED_ROUTING_KEY = "ticket.assigned"
TICKET_ASSIGNED_RETRY_ROUTING_KEY = "ticket.assigned.retry"

NOTIFICATIONS_TICKET_ASSIGNED_QUEUE = "notifications.ticket.assigned"
NOTIFICATIONS_TICKET_ASSIGNED_RETRY_QUEUE = "notifications.ticket.assigned.retry"
NOTIFICATIONS_TICKET_ASSIGNED_DLQ = "notifications.ticket.assigned.dlq"

RETRY_TTL_MS = 10_000


async def declare_topology(channel: AbstractChannel) -> AbstractQueue:
    events_exchange = await channel.declare_exchange(
        TICKETS_EVENTS_EXCHANGE,
        ExchangeType.TOPIC, 
        durable=True,
    )
    retry_exchange = await channel.declare_exchange(
        TICKETS_RETRY_EXCHANGE,
        ExchangeType.DIRECT,
        durable=True,
    )
    dlx_exchange = await channel.declare_exchange(
        TICKETS_DLX_EXCHANGE,
        ExchangeType.FANOUT,
        durable=True,
    )

    queue = await channel.declare_queue(
        NOTIFICATIONS_TICKET_ASSIGNED_QUEUE,
        durable=True,
        arguments={"x-dead-letter-exchange": TICKETS_DLX_EXCHANGE},
    )
    await queue.bind(events_exchange, routing_key=TICKET_ASSIGNED_ROUTING_KEY)

    retry_queue = await channel.declare_queue(
        NOTIFICATIONS_TICKET_ASSIGNED_RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": RETRY_TTL_MS,
            "x-dead-letter-exchange": TICKETS_EVENTS_EXCHANGE,
            "x-dead-letter-routing-key": TICKET_ASSIGNED_ROUTING_KEY,
        },
    )
    await retry_queue.bind(retry_exchange, routing_key=TICKET_ASSIGNED_RETRY_ROUTING_KEY)

    dlq = await channel.declare_queue(NOTIFICATIONS_TICKET_ASSIGNED_DLQ, durable=True)
    await dlq.bind(dlx_exchange)

    return queue


async def get_events_exchange(channel: AbstractChannel) -> AbstractExchange:
    return await channel.declare_exchange(
        TICKETS_EVENTS_EXCHANGE,
        ExchangeType.TOPIC,
        durable=True,
    )


async def get_retry_exchange(channel: AbstractChannel) -> AbstractExchange:
    return await channel.declare_exchange(
        TICKETS_RETRY_EXCHANGE,
        ExchangeType.DIRECT,
        durable=True,
    )
