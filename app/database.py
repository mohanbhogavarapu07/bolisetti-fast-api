"""
Direct database client using Prisma Python
Replaces ZenStack service calls with direct database access
"""
from prisma import Prisma
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

class DatabaseClient:
    def __init__(self):
        self.prisma = Prisma()
        self._connected = False
    
    async def connect(self):
        """Connect to database"""
        if not self._connected:
            await self.prisma.connect()
            self._connected = True
    
    async def disconnect(self):
        """Disconnect from database"""
        if self._connected:
            await self.prisma.disconnect()
            self._connected = False
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    # User operations
    async def get_users(self, skip: int = 0, take: int = 100) -> List[Dict[str, Any]]:
        """Get all users"""
        await self.connect()
        users = await self.prisma.user.find_many(
            skip=skip,
            take=take,
            include={
                'role': True,
                'constituency': True
            }
        )
        return [self._serialize_user(user) for user in users]
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        await self.connect()
        user = await self.prisma.user.find_unique(
            where={'id': user_id},
            include={
                'role': True,
                'constituency': True
            }
        )
        return self._serialize_user(user) if user else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        await self.connect()
        user = await self.prisma.user.find_unique(
            where={'email': email},
            include={
                'role': True,
                'constituency': True
            }
        )
        return self._serialize_user(user) if user else None
    
    async def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number"""
        await self.connect()
        user = await self.prisma.user.find_unique(
            where={'phoneNumber': phone_number},
            include={
                'role': True,
                'constituency': True
            }
        )
        return self._serialize_user(user) if user else None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        await self.connect()
        user = await self.prisma.user.create(
            data=user_data,
            include={
                'role': True,
                'constituency': True
            }
        )
        return self._serialize_user(user)
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        await self.connect()
        user = await self.prisma.user.update(
            where={'id': user_id},
            data=user_data,
            include={
                'role': True,
                'constituency': True
            }
        )
        return self._serialize_user(user)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        await self.connect()
        await self.prisma.user.delete(where={'id': user_id})
        return True
    
    # Voter ID operations
    async def get_voter_id(self, voter_id: str) -> Optional[Dict[str, Any]]:
        """Get voter ID by voter ID string"""
        await self.connect()
        voter_record = await self.prisma.voterid.find_unique(where={'voterId': voter_id})
        return self._serialize_voter_id(voter_record) if voter_record else None
    
    def _serialize_voter_id(self, voter_id) -> Dict[str, Any]:
        """Serialize voter ID object"""
        if not voter_id:
            return None
        return {
            'id': voter_id.id,
            'voterId': voter_id.voterId,
            'isActive': voter_id.isActive,
            'createdAt': voter_id.createdAt.isoformat() if voter_id.createdAt else None,
            'updatedAt': voter_id.updatedAt.isoformat() if voter_id.updatedAt else None
        }
    
    # OTP operations
    async def create_otp(self, otp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new OTP record"""
        await self.connect()
        otp = await self.prisma.otp.create(data=otp_data)
        return self._serialize_otp(otp)
    
    async def get_otp_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get OTP by phone number"""
        await self.connect()
        # Get all OTPs for the phone number and sort them manually
        otps = await self.prisma.otp.find_many(
            where={'phoneNumber': phone_number}
        )
        if not otps:
            return None
        
        # Sort by createdAt descending and get the first one
        otps.sort(key=lambda x: x.createdAt, reverse=True)
        return self._serialize_otp(otps[0])
    
    async def mark_otp_used(self, otp_id: str) -> bool:
        """Mark OTP as used"""
        await self.connect()
        await self.prisma.otp.update(
            where={'id': otp_id},
            data={'isUsed': True}
        )
        return True
    
    async def cleanup_expired_otps(self) -> int:
        """Clean up expired OTPs"""
        await self.connect()
        from datetime import datetime
        now = datetime.utcnow()
        result = await self.prisma.otp.delete_many(
            where={'expiresAt': {'lt': now}}
        )
        return result
    
    def _serialize_otp(self, otp) -> Dict[str, Any]:
        """Serialize OTP object"""
        if not otp:
            return None
        return {
            'id': otp.id,
            'phoneNumber': otp.phoneNumber,
            'otp': otp.otp,
            'expiresAt': otp.expiresAt.isoformat() if otp.expiresAt else None,
            'isUsed': otp.isUsed,
            'createdAt': otp.createdAt.isoformat() if otp.createdAt else None
        }
    
    # Session operations
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new session"""
        await self.connect()
        session = await self.prisma.session.create(data=session_data)
        return self._serialize_session(session)
    
    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session by user ID"""
        await self.connect()
        session = await self.prisma.session.find_first(
            where={'userId': user_id, 'isActive': True}
        )
        return self._serialize_session(session) if session else None
    
    def _serialize_session(self, session) -> Dict[str, Any]:
        """Serialize session object"""
        if not session:
            return None
        return {
            'id': session.id,
            'userId': session.userId,
            'phoneNumber': session.phoneNumber,
            'expiresAt': session.expiresAt.isoformat() if session.expiresAt else None,
            'isActive': session.isActive,
            'createdAt': session.createdAt.isoformat() if session.createdAt else None,
            'updatedAt': session.updatedAt.isoformat() if session.updatedAt else None
        }
    
    # User operations (additional methods)
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        await self.connect()
        user = await self.prisma.user.find_unique(where={'id': user_id})
        return self._serialize_user(user) if user else None
    
    async def get_users(self, skip: int = 0, take: int = 100) -> List[Dict[str, Any]]:
        """Get all users"""
        await self.connect()
        users = await self.prisma.user.find_many(skip=skip, take=take)
        return [self._serialize_user(user) for user in users]
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        await self.connect()
        user = await self.prisma.user.update(
            where={'id': user_id},
            data=user_data
        )
        return self._serialize_user(user)
    
    def _serialize_user(self, user) -> Dict[str, Any]:
        """Serialize user object"""
        if not user:
            return None
        return {
            'id': user.id,
            'firstName': user.firstName,
            'lastName': user.lastName,
            'email': user.email,
            'phoneNumber': user.phoneNumber,
            'voterId': user.voterId,
            'profilePictureUrl': user.profilePictureUrl,
            'address': user.address,
            'description': user.description,
            'isActive': user.isActive,
            'roleId': user.roleId,
            'constituencyId': user.constituencyId,
            'createdAt': user.createdAt.isoformat() if user.createdAt else None,
            'updatedAt': user.updatedAt.isoformat() if user.updatedAt else None
        }

    # Grievance operations
    async def get_grievances(self, skip: int = 0, take: int = 100) -> List[Dict[str, Any]]:
        """Get all grievances with related data"""
        await self.connect()
        grievances = await self.prisma.grievance.find_many(
            skip=skip,
            take=take,
            include={
                'user': True,
                'constituency': True,
                'department': True
            }
        )
        return [self._serialize_grievance(grievance) for grievance in grievances]
    
    async def get_grievance(self, grievance_id: str) -> Optional[Dict[str, Any]]:
        """Get grievance by ID with related data"""
        await self.connect()
        grievance = await self.prisma.grievance.find_unique(
            where={'id': grievance_id},
            include={
                'user': True,
                'constituency': True,
                'department': True
            }
        )
        return self._serialize_grievance(grievance) if grievance else None
    
    async def create_grievance(self, grievance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new grievance"""
        await self.connect()
        grievance = await self.prisma.grievance.create(
            data=grievance_data,
            include={
                'user': True,
                'constituency': True,
                'department': True
            }
        )
        return self._serialize_grievance(grievance)
    
    async def update_grievance(self, grievance_id: str, grievance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update grievance"""
        await self.connect()
        grievance = await self.prisma.grievance.update(
            where={'id': grievance_id},
            data=grievance_data,
            include={
                'user': True,
                'constituency': True,
                'department': True
            }
        )
        return self._serialize_grievance(grievance)
    
    async def delete_grievance(self, grievance_id: str) -> bool:
        """Delete grievance"""
        await self.connect()
        await self.prisma.grievance.delete(where={'id': grievance_id})
        return True
    
    # Constituency operations
    async def get_constituencies(self) -> List[Dict[str, Any]]:
        """Get all constituencies"""
        await self.connect()
        constituencies = await self.prisma.constituency.find_many()
        return [self._serialize_constituency(constituency) for constituency in constituencies]
    
    async def get_constituency_by_id(self, constituency_id: str) -> Optional[Dict[str, Any]]:
        """Get constituency by ID"""
        await self.connect()
        constituency = await self.prisma.constituency.find_unique(where={'id': constituency_id})
        return self._serialize_constituency(constituency) if constituency else None
    
    # Department operations
    async def get_grievance_departments(self) -> List[Dict[str, Any]]:
        """Get all grievance departments"""
        await self.connect()
        departments = await self.prisma.grievancedepartment.find_many()
        return [self._serialize_grievance_department(dept) for dept in departments]
    
    async def get_grievance_department_by_id(self, department_id: str) -> Optional[Dict[str, Any]]:
        """Get grievance department by ID"""
        await self.connect()
        department = await self.prisma.grievancedepartment.find_unique(where={'id': department_id})
        return self._serialize_grievance_department(department) if department else None
    
    # Admin operations
    async def get_admins(self, skip: int = 0, take: int = 100) -> List[Dict[str, Any]]:
        """Get all admins"""
        await self.connect()
        admins = await self.prisma.admin.find_many(skip=skip, take=take)
        return [self._serialize_admin(admin) for admin in admins]
    
    async def get_admin_by_id(self, admin_id: str) -> Optional[Dict[str, Any]]:
        """Get admin by ID"""
        await self.connect()
        admin = await self.prisma.admin.find_unique(where={'id': admin_id})
        return self._serialize_admin(admin) if admin else None
    
    async def get_admin_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get admin by email"""
        await self.connect()
        admin = await self.prisma.admin.find_unique(where={'email': email})
        return self._serialize_admin(admin) if admin else None
    
    async def create_admin(self, admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new admin"""
        await self.connect()
        admin = await self.prisma.admin.create(data=admin_data)
        return self._serialize_admin(admin)
    
    async def update_admin(self, admin_id: str, admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update admin"""
        await self.connect()
        admin = await self.prisma.admin.update(
            where={'id': admin_id},
            data=admin_data
        )
        return self._serialize_admin(admin)
    
    async def delete_admin(self, admin_id: str) -> bool:
        """Delete admin"""
        await self.connect()
        await self.prisma.admin.delete(where={'id': admin_id})
        return True
    
    # News operations
    async def get_news(self, skip: int = 0, take: int = 100) -> List[Dict[str, Any]]:
        """Get all news"""
        await self.connect()
        news = await self.prisma.news.find_many(skip=skip, take=take)
        return [self._serialize_news(item) for item in news]
    
    async def get_news_by_id(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Get news by ID"""
        await self.connect()
        news = await self.prisma.news.find_unique(where={'id': news_id})
        return self._serialize_news(news) if news else None
    
    async def create_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create news"""
        await self.connect()
        news = await self.prisma.news.create(data=news_data)
        return self._serialize_news(news)
    
    async def update_news(self, news_id: str, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update news"""
        await self.connect()
        news = await self.prisma.news.update(
            where={'id': news_id},
            data=news_data
        )
        return self._serialize_news(news)
    
    async def delete_news(self, news_id: str) -> bool:
        """Delete news"""
        await self.connect()
        await self.prisma.news.delete(where={'id': news_id})
        return True
    
    # Schedule Events operations
    async def get_schedule_events(self, skip: int = 0, take: int = 100) -> List[Dict[str, Any]]:
        """Get all schedule events"""
        await self.connect()
        events = await self.prisma.scheduleevent.find_many(skip=skip, take=take)
        return [self._serialize_schedule_event(event) for event in events]
    
    async def get_schedule_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule event by ID"""
        await self.connect()
        event = await self.prisma.scheduleevent.find_unique(where={'id': event_id})
        return self._serialize_schedule_event(event) if event else None
    
    async def create_schedule_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create schedule event"""
        await self.connect()
        event = await self.prisma.scheduleevent.create(data=event_data)
        return self._serialize_schedule_event(event)
    
    async def update_schedule_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update schedule event"""
        await self.connect()
        event = await self.prisma.scheduleevent.update(
            where={'id': event_id},
            data=event_data
        )
        return self._serialize_schedule_event(event)
    
    async def delete_schedule_event(self, event_id: str) -> bool:
        """Delete schedule event"""
        await self.connect()
        await self.prisma.scheduleevent.delete(where={'id': event_id})
        return True
    
    # Serialization helpers
    def _serialize_user(self, user) -> Dict[str, Any]:
        """Serialize user object"""
        if not user:
            return None
        return {
            'id': user.id,
            'firstName': user.firstName,
            'lastName': user.lastName,
            'email': user.email,
            'phoneNumber': user.phoneNumber,
            'voterId': user.voterId,
            'profilePictureUrl': user.profilePictureUrl,
            'address': user.address,
            'description': user.description,
            'isActive': user.isActive,
            'createdAt': user.createdAt.isoformat() if user.createdAt else None,
            'updatedAt': user.updatedAt.isoformat() if user.updatedAt else None,
            'roleId': user.roleId,
            'constituencyId': user.constituencyId,
            'role': self._serialize_role(user.role) if hasattr(user, 'role') and user.role else None,
            'constituency': self._serialize_constituency(user.constituency) if hasattr(user, 'constituency') and user.constituency else None
        }
    
    def _serialize_grievance(self, grievance) -> Dict[str, Any]:
        """Serialize grievance object"""
        if not grievance:
            return None
        return {
            'id': grievance.id,
            'title': grievance.title,
            'description': grievance.description,
            'address': grievance.address,
            'area': grievance.area,
            'status': grievance.status.value if hasattr(grievance.status, 'value') else str(grievance.status),
            'priority': grievance.priority.value if hasattr(grievance.priority, 'value') else str(grievance.priority),
            'imageUrl': grievance.imageUrl,
            'createdAt': grievance.createdAt.isoformat() if grievance.createdAt else None,
            'lastUpdated': grievance.lastUpdated.isoformat() if grievance.lastUpdated else None,
            'userId': grievance.userId,
            'constituencyId': grievance.constituencyId,
            'departmentId': grievance.departmentId,
            'statusId': grievance.statusId,
            'user': self._serialize_user(grievance.user) if hasattr(grievance, 'user') and grievance.user else None,
            'constituency': self._serialize_constituency(grievance.constituency) if hasattr(grievance, 'constituency') and grievance.constituency else None,
            'department': self._serialize_department(grievance.department) if hasattr(grievance, 'department') and grievance.department else None
        }
    
    def _serialize_constituency(self, constituency) -> Dict[str, Any]:
        """Serialize constituency object"""
        if not constituency:
            return None
        return {
            'id': constituency.id,
            'name': constituency.name,
            'createdAt': constituency.createdAt.isoformat() if constituency.createdAt else None,
            'updatedAt': constituency.updatedAt.isoformat() if constituency.updatedAt else None
        }
    
    def _serialize_department(self, department) -> Dict[str, Any]:
        """Serialize department object"""
        if not department:
            return None
        return {
            'id': department.id,
            'name': department.name,
            'createdAt': department.createdAt.isoformat() if department.createdAt else None,
            'updatedAt': department.updatedAt.isoformat() if department.updatedAt else None
        }
    
    def _serialize_grievance_department(self, department) -> Dict[str, Any]:
        """Serialize grievance department object"""
        if not department:
            return None
        return {
            'id': department.id,
            'name': department.name,
            'createdAt': department.createdAt.isoformat() if department.createdAt else None,
            'updatedAt': department.updatedAt.isoformat() if department.updatedAt else None
        }
    
    def _serialize_admin(self, admin) -> Dict[str, Any]:
        """Serialize admin object"""
        if not admin:
            return None
        return {
            'id': admin.id,
            'firstName': admin.firstName,
            'lastName': admin.lastName,
            'email': admin.email,
            'password': admin.password,  # Include password field
            'isActive': admin.isActive,
            'lastLogin': admin.lastLogin.isoformat() if admin.lastLogin else None,
            'createdAt': admin.createdAt.isoformat() if admin.createdAt else None,
            'updatedAt': admin.updatedAt.isoformat() if admin.updatedAt else None
        }
    
    def _serialize_news(self, news) -> Dict[str, Any]:
        """Serialize news object"""
        if not news:
            return None
        return {
            'id': news.id,
            'title': news.title,
            'content': news.content,
            'imageUrl': news.imageUrl,
            'createdAt': news.createdAt.isoformat() if news.createdAt else None,
            'updatedAt': news.updatedAt.isoformat() if news.updatedAt else None
        }
    
    def _serialize_schedule_event(self, event) -> Dict[str, Any]:
        """Serialize schedule event object"""
        if not event:
            return None
        return {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'location': event.location,
            'eventDatetime': event.eventDatetime.isoformat() if event.eventDatetime else None,
            'createdAt': event.createdAt.isoformat() if event.createdAt else None,
            'updatedAt': event.updatedAt.isoformat() if event.updatedAt else None
        }
    
    def _serialize_role(self, role) -> Dict[str, Any]:
        """Serialize role object"""
        if not role:
            return None
        return {
            'id': role.id,
            'name': role.name,
            'createdAt': role.createdAt.isoformat() if role.createdAt else None,
            'updatedAt': role.updatedAt.isoformat() if role.updatedAt else None
        }
    
    # Schedule Event operations
    async def get_schedule_events(self, skip: int = 0, take: int = 100) -> List[Dict[str, Any]]:
        """Get all schedule events"""
        await self.connect()
        events = await self.prisma.scheduleevent.find_many(skip=skip, take=take)
        return [self._serialize_schedule_event(event) for event in events]
    
    async def get_schedule_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule event by ID"""
        await self.connect()
        event = await self.prisma.scheduleevent.find_unique(where={'id': event_id})
        return self._serialize_schedule_event(event) if event else None
    
    async def create_schedule_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new schedule event"""
        await self.connect()
        event = await self.prisma.scheduleevent.create(data=event_data)
        return self._serialize_schedule_event(event)
    
    async def update_schedule_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update schedule event"""
        await self.connect()
        event = await self.prisma.scheduleevent.update(
            where={'id': event_id},
            data=event_data
        )
        return self._serialize_schedule_event(event)
    
    async def delete_schedule_event(self, event_id: str) -> bool:
        """Delete schedule event"""
        await self.connect()
        await self.prisma.scheduleevent.delete(where={'id': event_id})
        return True
    
    def _serialize_schedule_event(self, event) -> Dict[str, Any]:
        """Serialize schedule event object"""
        if not event:
            return None
        return {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'location': event.location,
            'eventDatetime': event.eventDatetime.isoformat() if event.eventDatetime else None,
            'createdAt': event.createdAt.isoformat() if event.createdAt else None,
            'updatedAt': event.updatedAt.isoformat() if event.updatedAt else None
        }

    # Project operations
    async def get_projects(self, skip: int = 0, take: int = 100) -> List[Dict[str, Any]]:
        """Get all projects"""
        await self.connect()
        projects = await self.prisma.project.find_many(skip=skip, take=take)
        return [self._serialize_project(project) for project in projects]
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        await self.connect()
        project = await self.prisma.project.find_unique(where={'id': project_id})
        return self._serialize_project(project) if project else None
    
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new project"""
        await self.connect()
        project = await self.prisma.project.create(data=project_data)
        return self._serialize_project(project)
    
    async def update_project(self, project_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update project"""
        await self.connect()
        project = await self.prisma.project.update(
            where={'id': project_id},
            data=project_data
        )
        return self._serialize_project(project)
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete project"""
        await self.connect()
        await self.prisma.project.delete(where={'id': project_id})
        return True
    
    def _serialize_project(self, project) -> Dict[str, Any]:
        """Serialize project object"""
        if not project:
            return None
        return {
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'location': project.location,
            'projectStatus': project.projectStatus,
            'imageUrl': project.imageUrl,
            'createdAt': project.createdAt.isoformat() if project.createdAt else None,
            'updatedAt': project.updatedAt.isoformat() if project.updatedAt else None
        }
    
    # News operations
    async def get_news(self, skip: int = 0, take: int = 100) -> List[Dict[str, Any]]:
        """Get all news"""
        await self.connect()
        news = await self.prisma.news.find_many(skip=skip, take=take)
        return [self._serialize_news(item) for item in news]
    
    async def get_news_by_id(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Get news by ID"""
        await self.connect()
        news = await self.prisma.news.find_unique(where={'id': news_id})
        return self._serialize_news(news) if news else None
    
    async def create_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new news"""
        await self.connect()
        news = await self.prisma.news.create(data=news_data)
        return self._serialize_news(news)
    
    async def update_news(self, news_id: str, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update news"""
        await self.connect()
        news = await self.prisma.news.update(
            where={'id': news_id},
            data=news_data
        )
        return self._serialize_news(news)
    
    async def delete_news(self, news_id: str) -> bool:
        """Delete news"""
        await self.connect()
        await self.prisma.news.delete(where={'id': news_id})
        return True
    
    def _serialize_news(self, news) -> Dict[str, Any]:
        """Serialize news object"""
        if not news:
            return None
        return {
            'id': news.id,
            'title': news.title,
            'content': news.content,
            'imageUrl': news.imageUrl,
            'createdAt': news.createdAt.isoformat() if news.createdAt else None,
            'updatedAt': news.updatedAt.isoformat() if news.updatedAt else None
        }
    
    # Media operations
    async def create_media(self, media_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new media"""
        await self.connect()
        media = await self.prisma.media.create(data=media_data)
        return self._serialize_media(media)
    
    async def get_media_by_entity(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        """Get media by entity type and ID"""
        await self.connect()
        media = await self.prisma.media.find_many(
            where={'entityType': entity_type, 'entityId': entity_id}
        )
        return [self._serialize_media(item) for item in media]
    
    async def get_media(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Get media by ID"""
        await self.connect()
        media = await self.prisma.media.find_unique(where={'id': media_id})
        return self._serialize_media(media) if media else None
    
    async def delete_media(self, media_id: str) -> bool:
        """Delete media"""
        await self.connect()
        await self.prisma.media.delete(where={'id': media_id})
        return True
    
    def _serialize_media(self, media) -> Dict[str, Any]:
        """Serialize media object"""
        if not media:
            return None
        return {
            'id': media.id,
            'entityType': media.entityType,
            'entityId': media.entityId,
            'fileUrl': media.fileUrl,
            'fileType': media.fileType,
            'createdAt': media.createdAt.isoformat() if media.createdAt else None,
            'updatedAt': media.updatedAt.isoformat() if media.updatedAt else None
        }

# Global database client instance
db_client = DatabaseClient()