from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class GrievanceStatus(str, Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class MediaType(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

# Base Models
class UserBase(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    phoneNumber: Optional[str] = None
    voterId: Optional[str] = None
    profilePictureUrl: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    roleId: Optional[str] = None
    constituencyId: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phoneNumber: Optional[str] = None
    voterId: Optional[str] = None
    profilePictureUrl: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    roleId: Optional[str] = None
    constituencyId: Optional[str] = None

class User(UserBase):
    id: str
    isActive: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Role Models
class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Constituency Models
class ConstituencyBase(BaseModel):
    name: str

class ConstituencyCreate(ConstituencyBase):
    pass

class Constituency(ConstituencyBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Grievance Models
class GrievanceBase(BaseModel):
    title: str
    description: str
    address: str
    area: Optional[str] = None
    priority: Priority = Priority.MEDIUM

class GrievanceCreate(GrievanceBase):
    constituencyId: Optional[str] = None
    departmentId: Optional[str] = None
    statusId: Optional[str] = None
    mediaId: Optional[str] = None

class GrievanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    area: Optional[str] = None
    status: Optional[GrievanceStatus] = None
    priority: Optional[Priority] = None
    constituencyId: Optional[str] = None
    departmentId: Optional[str] = None
    statusId: Optional[str] = None

class Grievance(GrievanceBase):
    id: str
    status: GrievanceStatus
    createdAt: datetime
    lastUpdated: datetime
    userId: str
    constituencyId: Optional[str] = None
    departmentId: Optional[str] = None
    statusId: Optional[str] = None
    mediaId: Optional[str] = None

    class Config:
        from_attributes = True

# Grievance Department Models
class GrievanceDepartmentBase(BaseModel):
    name: str

class GrievanceDepartmentCreate(GrievanceDepartmentBase):
    pass

class GrievanceDepartment(GrievanceDepartmentBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Grievance Status Models
class GrievanceStatusEnumBase(BaseModel):
    name: str

class GrievanceStatusEnumCreate(GrievanceStatusEnumBase):
    pass

class GrievanceStatusEnum(GrievanceStatusEnumBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Grievance Photo Models
class GrievancePhotoBase(BaseModel):
    photoUrl: str

class GrievancePhotoCreate(GrievancePhotoBase):
    grievanceId: str

class GrievancePhoto(GrievancePhotoBase):
    id: str
    grievanceId: str
    createdAt: datetime

    class Config:
        from_attributes = True

# Grievance Comment Models
class GrievanceCommentBase(BaseModel):
    content: str

class GrievanceCommentCreate(GrievanceCommentBase):
    grievanceId: str

class GrievanceComment(GrievanceCommentBase):
    id: str
    grievanceId: str
    userId: str
    createdAt: datetime

    class Config:
        from_attributes = True

# News Models
class NewsBase(BaseModel):
    title: str
    content: str
    imageUrl: Optional[str] = None

class NewsCreate(NewsBase):
    pass

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    imageUrl: Optional[str] = None

class News(NewsBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Project Models
class ProjectBase(BaseModel):
    title: str
    description: str
    location: Optional[str] = None
    projectStatus: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    projectStatus: Optional[str] = None

class Project(ProjectBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Schedule Event Models
class ScheduleEventBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    eventDatetime: datetime

class ScheduleEventCreate(ScheduleEventBase):
    pass

class ScheduleEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    eventDatetime: Optional[datetime] = None

class ScheduleEvent(ScheduleEventBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Media Models
class MediaBase(BaseModel):
    title: str
    mediaUrl: str
    type: MediaType

class MediaCreate(MediaBase):
    pass

class MediaUpdate(BaseModel):
    title: Optional[str] = None
    mediaUrl: Optional[str] = None
    type: Optional[MediaType] = None

class Media(MediaBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Notification Models
class NotificationBase(BaseModel):
    title: str
    description: Optional[str] = None
    isRead: bool = False

class NotificationCreate(NotificationBase):
    userId: Optional[str] = None

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    isRead: Optional[bool] = None

class Notification(NotificationBase):
    id: str
    userId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int  # seconds until expiration

class TokenData(BaseModel):
    userId: Optional[str] = None
    phoneNumber: Optional[str] = None

# Voter ID Models
class VoterIdBase(BaseModel):
    voterId: str
    isActive: bool = True

class VoterIdCreate(VoterIdBase):
    pass

class VoterId(VoterIdBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# OTP Models
class OTPBase(BaseModel):
    phoneNumber: str
    otp: str
    expiresAt: datetime
    isUsed: bool = False

class OTPCreate(OTPBase):
    pass

class OTP(OTPBase):
    id: str
    createdAt: datetime

    class Config:
        from_attributes = True

# Session Models
class SessionBase(BaseModel):
    userId: str
    phoneNumber: str
    expiresAt: datetime
    isActive: bool = True

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# New Authentication Models
class PhoneLoginRequest(BaseModel):
    phoneNumber: str
    voterId: str

class OTPVerificationRequest(BaseModel):
    phoneNumber: str
    otp: str
    voterId: str

class UserProfileUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    description: Optional[str] = None
    profilePictureUrl: Optional[str] = None
    constituencyId: Optional[str] = None

# Admin System Models (Separate from User system)
class AdminBase(BaseModel):
    firstName: str
    lastName: str
    email: str
    isActive: bool = True

class AdminCreate(AdminBase):
    password: str

class AdminUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    isActive: Optional[bool] = None

class Admin(AdminBase):
    id: str
    lastLogin: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class AdminLoginRequest(BaseModel):
    email: str
    password: str

class AdminToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_type: str = "admin"

# Legacy password-based models removed - using OTP authentication instead