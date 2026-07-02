from .auth import router as auth_router
from .schools import router as schools_router
from .students import router as students_router
from .grades import router as grades_router
from .attendance import router as attendance_router
from .fees import router as fees_router
from .dashboard import router as dashboard_router
from .reports import router as reports_router
from .announcements import router as announcements_router
from .staff import router as staff_router

__all__ = [
    "auth_router",
    "schools_router",
    "students_router",
    "grades_router",
    "attendance_router",
    "fees_router",
    "dashboard_router",
    "reports_router",
    "announcements_router",
    "staff_router",
]