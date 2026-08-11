import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers.ticket_router import router as ticket_router
from app.routers.user_router import router as user_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(ticket_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"

    print(
        f"[{request_id}]"
        f"{request.method}  {request.url.path} "
        f"Completed in {process_time:.4f}s"
    )

    return response


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):

    try:
        response = await call_next(request)
        return response

    except Exception as exc:
        print(f"Unexpected error: {exc}")

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
