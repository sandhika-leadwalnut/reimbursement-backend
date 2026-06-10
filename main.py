from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, reimbursements, admin
from core.config import settings

app = FastAPI(title="Reimbursement Management API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log exception here
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)},
    )

app.include_router(auth.router)
app.include_router(reimbursements.router)
app.include_router(admin.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
