from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="BuscaMedicos API", version="1.0.0", lifespan=lifespan)

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
    laboratory_reports_router, admin_moderation_router
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