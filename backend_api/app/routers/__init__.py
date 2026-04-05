from .auth import router as auth_router
from .users import router as users_router
from .patients import router as patients_router
from .professionals import router as professionals_router
from .agreements import router as agreements_router
from .admin import router as admin_router
from .access_control import router as access_control_router
from .files import router as files_router
from .public import router as public_router
from .professional_self import router as professional_self_router
from .patient_appointments import router as patient_appointments_router
from .admin_appointments import router as admin_appointments_router
from .patient_payments import router as patient_payments_router
from .professional_prices import router as professional_prices_router
from .admin_payments import router as admin_payments_router
from .professional_teleconsultation import router as professional_teleconsultation_router
from .patient_teleconsultation import router as patient_teleconsultation_router
from .professional_clinical import router as professional_clinical_router
from .patient_clinical import router as patient_clinical_router
from .admin_clinical import router as admin_clinical_router
from .public_reviews import router as public_reviews_router
from .patient_reviews import router as patient_reviews_router
from .professional_reviews import router as professional_reviews_router
from .laboratory_reports import router as laboratory_reports_router
from .admin_moderation import router as admin_moderation_router

__all__ = [
    "auth_router", "users_router", "patients_router", "professionals_router",
    "agreements_router", "admin_router", "access_control_router", "files_router",
    "public_router", "professional_self_router", "patient_appointments_router",
    "admin_appointments_router", "patient_payments_router", "professional_prices_router",
    "admin_payments_router", "professional_teleconsultation_router",
    "patient_teleconsultation_router", "professional_clinical_router",
    "patient_clinical_router", "admin_clinical_router",
    "public_reviews_router", "patient_reviews_router",
    "professional_reviews_router", "laboratory_reports_router",
    "admin_moderation_router"
]