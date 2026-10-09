import asyncio
import logging

from app.infrastructure.rabbitmq.client import close_connection
from app.workers.notifications.consumer import consume_ticket_notifications

logging.basicConfig(level=logging.INFO)


async def _run() -> None:
    try:
        await consume_ticket_notifications()
    finally:
        await close_connection()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
