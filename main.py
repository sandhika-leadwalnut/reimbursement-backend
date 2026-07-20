import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, reimbursements, admin
from api import oauth
from core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Reimbursement Management API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL.rstrip('/')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )

app.include_router(auth.router)
app.include_router(reimbursements.router)
app.include_router(admin.router)
app.include_router(oauth.router, prefix="/oauth", tags=["oauth"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
