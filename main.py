from fastapi import FastAPI

from app.routers.user_router import router as user_router
from app.routers.ticket_router import router as ticket_router

app = FastAPI()

app.include_router(user_router)
app.include_router(ticket_router)
