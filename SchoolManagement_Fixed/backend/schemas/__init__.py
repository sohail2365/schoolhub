from .school import SchoolRegisterRequest, SchoolProfileOut, SchoolProfileUpdate
from .user import LoginRequest, RefreshRequest, AuthResponse, RefreshResponse
from .student import StudentCreate, StudentUpdate, StudentOut
from .grade import GradeCreate, GradeUpdate, GradeOut
from .attendance import AttendanceCreate, AttendanceOut
from .fee import FeeCreate, FeeUpdate, FeeOut
from .payment import PaymentCreate, PaymentOut
from .announcement import AnnouncementCreate, AnnouncementOut

__all__ = [
    "SchoolRegisterRequest",
    "SchoolProfileOut",
    "SchoolProfileUpdate",
    "LoginRequest",
    "RefreshRequest",
    "AuthResponse",
    "RefreshResponse",
    "StudentCreate",
    "StudentUpdate",
    "StudentOut",
    "GradeCreate",
    "GradeUpdate",
    "GradeOut",
    "AttendanceCreate",
    "AttendanceOut",
    "FeeCreate",
    "FeeUpdate",
    "FeeOut",
    "PaymentCreate",
    "PaymentOut",
    "AnnouncementCreate",
    "AnnouncementOut",
]
