# backend/models/__init__.py

from .school import School
from .user import User, UserRole
from .student import Student, Gender
from .attendance import Attendance
from .grade import Grade
from .fee import Fee, FeeStatus
from .payment import Payment, PaymentMethod
from .parent_student_link import ParentStudentLink
from .announcement import Announcement
from .staff import Staff, StaffStatus, StaffAttendance, StaffSalaryPayment

__all__ = [
    'School',
    'User',
    'UserRole',
    'Student',
    'Gender',
    'Attendance',
    'Grade',
    'Fee',
    'FeeStatus',
    'Payment',
    'PaymentMethod',
    'ParentStudentLink',
    'Announcement',
    'Staff',
    'StaffStatus',
    'StaffAttendance',
    'StaffSalaryPayment',
]