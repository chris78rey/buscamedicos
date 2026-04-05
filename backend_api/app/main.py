from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
import json
import time
import logging
from datetime import datetime
from fastapi import Request

__version__ = "1.0.0"

structured_logger = logging.getLogger("buscamedicos.structured")
structured_logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "buscamedicos-api", "message": "%(message)s"}'
))
structured_logger.addHandler(_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="BuscaMedicos API",
    version=__version__,
    lifespan=lifespan,
)


@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)

    user_id = None
    if hasattr(request.state, "user_id"):
        user_id = str(request.state.user_id)

    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": "info" if response.status_code < 500 else "error",
        "service": "buscamedicos-api",
        "request_id": request_id,
        "user_id": user_id,
        "route": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
    }

    structured_logger.info(json.dumps(log_data))
    response.headers["x-request-id"] = request_id
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import (
    auth_router, users_router, patients_router, professionals_router,
    agreements_router, admin_router, access_control_router, files_router,
    public_router, professional_self_router, patient_appointments_router, admin_appointments_router,
    patient_payments_router, professional_prices_router, admin_payments_router,
    professional_teleconsultation_router, patient_teleconsultation_router,
    professional_clinical_router, patient_clinical_router, admin_clinical_router,
    public_reviews_router, patient_reviews_router, professional_reviews_router,
    laboratory_reports_router, admin_moderation_router,
    patient_privacy_router, professional_privacy_router,
    laboratory_privacy_router, admin_privacy_router,
    privacy_auditor_router, ops_router,
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(patients_router, prefix="/api/v1/patients", tags=["patients"])
app.include_router(professionals_router, prefix="/api/v1/professionals", tags=["professionals"])
app.include_router(agreements_router, prefix="/api/v1/agreements", tags=["agreements"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(access_control_router, prefix="/api/v1", tags=["access-control"])
app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
app.include_router(public_router, prefix="/api/v1/public", tags=["public"])
app.include_router(professional_self_router, prefix="/api/v1/professionals", tags=["professional-self"])
app.include_router(professional_teleconsultation_router, prefix="/api/v1/professionals", tags=["professional-teleconsultation"])
app.include_router(professional_clinical_router, prefix="/api/v1/professionals", tags=["professional-clinical"])
app.include_router(patient_appointments_router, prefix="/api/v1/patient", tags=["patient"])
app.include_router(patient_teleconsultation_router, prefix="/api/v1/patient", tags=["patient-teleconsultation"])
app.include_router(patient_clinical_router, prefix="/api/v1/patient", tags=["patient-clinical"])
app.include_router(admin_appointments_router, prefix="/api/v1/admin", tags=["admin-appointments"])
app.include_router(admin_clinical_router, prefix="/api/v1/admin", tags=["admin-clinical"])
app.include_router(patient_payments_router, prefix="/api/v1/patient", tags=["patient-payments"])
app.include_router(professional_prices_router, prefix="/api/v1/professionals", tags=["professional-prices"])
app.include_router(admin_payments_router, prefix="/api/v1/admin", tags=["admin-payments"])
app.include_router(public_reviews_router, prefix="/api/v1/public", tags=["public-reviews"])
app.include_router(patient_reviews_router, prefix="/api/v1/patient", tags=["patient-reviews"])
app.include_router(professional_reviews_router, prefix="/api/v1/professionals", tags=["professional-reviews"])
app.include_router(laboratory_reports_router, prefix="/api/v1/laboratories", tags=["laboratory-reports"])
app.include_router(admin_moderation_router, prefix="/api/v1/admin/moderation", tags=["admin-moderation"])
app.include_router(patient_privacy_router, prefix="/api/v1/patient", tags=["patient-privacy"])
app.include_router(professional_privacy_router, prefix="/api/v1/professionals", tags=["professional-privacy"])
app.include_router(laboratory_privacy_router, prefix="/api/v1/laboratories", tags=["laboratory-privacy"])
app.include_router(admin_privacy_router, prefix="/api/v1/admin", tags=["admin-privacy"])
app.include_router(privacy_auditor_router, prefix="/api/v1/privacy-auditor", tags=["privacy-auditor"])
app.include_router(ops_router)
