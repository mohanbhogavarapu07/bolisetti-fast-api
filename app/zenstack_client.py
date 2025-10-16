import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.config import settings
import json

class ZenStackClient:
    def __init__(self):
        self.base_url = settings.zenstack_service_url + "/api"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to ZenStack service"""
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=default_headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"ZenStack API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"ZenStack connection error: {str(e)}")
    
    # User operations
    async def get_users(self, skip: int = 0, take: int = 100, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get all users"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", "/User/findMany", params={"skip": skip, "take": take}, headers=headers)
    
    async def get_user_by_email(self, email: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            
            # Get all users and filter on our side since ZenStack filtering is broken
            all_users = await self._make_request("GET", "/User/findMany", params={"take": 100}, headers=headers)
            
            if all_users and 'data' in all_users:
                users = all_users['data']
                # Find user with matching email
                for user in users:
                    if user.get('email') == email:
                        return {'data': user, 'meta': all_users.get('meta', {})}
                return None
            else:
                return None
        except Exception:
            return None
    
    async def get_user(self, user_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get user by ID"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        
        # Get all users and filter (most reliable method)
        try:
            all_users = await self._make_request("GET", "/User/findMany", params={"take": 1000}, headers=headers)
            if all_users and 'data' in all_users:
                users = all_users['data']
                for user in users:
                    if user.get('id') == user_id:
                        return {'data': user, 'meta': all_users.get('meta', {})}
                raise Exception(f"User with ID {user_id} not found")
            else:
                raise Exception("No users found in response")
        except Exception as e:
            raise e

    async def get_user_by_phone_and_voter(self, phone_number: str, voter_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a user by matching both phoneNumber and voterId (client-side filter)."""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            all_users = await self._make_request("GET", "/User/findMany", params={"take": 1000}, headers=headers)
            users = all_users.get('data') if isinstance(all_users, dict) else (all_users if isinstance(all_users, list) else [])
            for u in users:
                if u.get('phoneNumber') == phone_number and u.get('voterId') == voter_id:
                    return u
            return None
        except Exception:
            return None

    async def get_user_by_phone(self, phone_number: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a user by phoneNumber (client-side filter)."""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            all_users = await self._make_request("GET", "/User/findMany", params={"take": 1000}, headers=headers)
            users = all_users.get('data') if isinstance(all_users, dict) else (all_users if isinstance(all_users, list) else [])
            for u in users:
                if u.get('phoneNumber') == phone_number:
                    return u
            return None
        except Exception:
            return None
    
    async def get_user_by_id(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get user by ID using ZenStack findFirst"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            result = await self._make_request("GET", "/User/findFirst", 
                data={"where": {"id": user_id}}, headers=headers)
            return result
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create new user"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        result = await self._make_request("POST", "/User/create", data={"data": user_data}, headers=headers)
        return result
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Update user"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("PUT", f"/User/update", data={"where": {"id": user_id}, "data": user_data}, headers=headers)
    
    async def delete_user(self, user_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Delete user"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("DELETE", f"/User/delete", data={"where": {"id": user_id}}, headers=headers)
    
    # Grievance operations
    async def get_grievances(self, skip: int = 0, take: int = 100, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get all grievances"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", "/Grievance/findMany", params={"skip": skip, "take": take}, headers=headers)
    
    async def get_grievance(self, grievance_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get grievance by ID"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", "/Grievance/findUnique", params={"where": {"id": grievance_id}}, headers=headers)
    
    async def create_grievance(self, grievance_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create new grievance"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/Grievance/create", data={"data": grievance_data}, headers=headers)
    
    async def update_grievance(self, grievance_id: str, grievance_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Update grievance"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("PUT", "/Grievance/update", data={"where": {"id": grievance_id}, "data": grievance_data}, headers=headers)
    
    async def delete_grievance(self, grievance_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Delete grievance"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("DELETE", "/Grievance/delete", data={"where": {"id": grievance_id}}, headers=headers)
    
    async def create_grievance_comment(self, grievance_id: str, comment_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create grievance comment"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/GrievanceComment/create", data={"data": comment_data}, headers=headers)
    
    async def get_grievance_comments(self, grievance_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get grievance comments"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", f"/grievances/{grievance_id}/comments", headers=headers)
    
    # News operations
    async def get_news(self, skip: int = 0, take: int = 100, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get all news"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", "/News/findMany", params={"skip": skip, "take": take}, headers=headers)
    
    async def get_news_item(self, news_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get news by ID"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", f"/News/findFirst", params={"where": {"id": news_id}}, headers=headers)
    
    async def create_news(self, news_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create news (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/News/create", data={"data": news_data}, headers=headers)
    
    async def update_news(self, news_id: str, news_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Update news (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("PUT", f"/News/update", data={"where": {"id": news_id}, "data": news_data}, headers=headers)
    
    async def delete_news(self, news_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Delete news (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("DELETE", f"/News/delete", data={"where": {"id": news_id}}, headers=headers)
    
    # Project operations
    async def get_projects(self, skip: int = 0, take: int = 100, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get all projects"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", "/Project/findMany", params={"skip": skip, "take": take}, headers=headers)
    
    async def get_project(self, project_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get project by ID"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", f"/projects/{project_id}", headers=headers)
    
    async def create_project(self, project_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create project (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/Project/create", data={"data": project_data}, headers=headers)
    
    async def update_project(self, project_id: str, project_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Update project (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("PUT", f"/projects/{project_id}", data=project_data, headers=headers)
    
    async def delete_project(self, project_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Delete project (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("DELETE", f"/projects/{project_id}", headers=headers)
    
    # Schedule events operations
    async def get_schedule_events(self, skip: int = 0, take: int = 100, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get all schedule events"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", "/scheduleEvents", params={"skip": skip, "take": take}, headers=headers)
    
    async def get_schedule_event(self, event_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get schedule event by ID"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", f"/scheduleEvents/{event_id}", headers=headers)
    
    async def create_schedule_event(self, event_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create schedule event (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/ScheduleEvent/create", data={"data": event_data}, headers=headers)
    
    async def update_schedule_event(self, event_id: str, event_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Update schedule event (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("PUT", f"/scheduleEvents/{event_id}", data=event_data, headers=headers)
    
    async def delete_schedule_event(self, event_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Delete schedule event (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("DELETE", f"/scheduleEvents/{event_id}", headers=headers)
    
    # Media operations
    async def get_media(self, skip: int = 0, take: int = 100, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get all media"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", "/Media/findMany", params={"skip": skip, "take": take}, headers=headers)
    
    async def get_media_item(self, media_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get media by ID"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", f"/Media/findUnique", params={"where": {"id": media_id}}, headers=headers)
    
    async def create_media(self, media_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create media (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/Media/create", data={"data": media_data}, headers=headers)
    
    async def update_media(self, media_id: str, media_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Update media (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("PUT", "/Media/update", data={"where": {"id": media_id}, "data": media_data}, headers=headers)
    
    async def delete_media(self, media_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Delete media (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("DELETE", "/Media/delete", data={"where": {"id": media_id}}, headers=headers)
    
    # Notification operations
    async def get_notifications(self, user_id: Optional[str] = None, skip: int = 0, take: int = 100, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get notifications"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        endpoint = f"/notifications/user/{user_id}" if user_id else "/notifications"
        return await self._make_request("GET", endpoint, params={"skip": skip, "take": take}, headers=headers)
    
    async def get_notification(self, notification_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Get notification by ID"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("GET", f"/notifications/{notification_id}", headers=headers)
    
    async def update_notification(self, notification_id: str, notification_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Update notification"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("PUT", f"/notifications/{notification_id}", data=notification_data, headers=headers)
    
    async def create_notification(self, notification_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create notification (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/Notification/create", data={"data": notification_data}, headers=headers)
    
    async def delete_notification(self, notification_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Delete notification (Admin only)"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("DELETE", f"/notifications/{notification_id}", headers=headers)
    
    # Voter ID operations
    async def get_voter_id(self, voter_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get voter ID by ID"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            
            # Get all voter IDs and filter
            all_voter_ids = await self._make_request("GET", "/VoterId/findMany", params={"take": 1000}, headers=headers)
            if all_voter_ids and 'data' in all_voter_ids:
                voter_ids = all_voter_ids['data']
                for vid in voter_ids:
                    if vid.get('voterId') == voter_id:
                        return {'data': vid, 'meta': all_voter_ids.get('meta', {})}
                return None
            return None
        except Exception:
            return None
    
    async def create_voter_id(self, voter_id_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create voter ID entry"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/VoterId/create", data={"data": voter_id_data}, headers=headers)
    
    # OTP operations
    async def create_otp(self, otp_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create OTP entry"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/OTP/create", data={"data": otp_data}, headers=headers)
    
    async def get_otp_by_phone(self, phone_number: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get LATEST OTP by phone number"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            
            # Get all OTPs and filter
            all_otps = await self._make_request("GET", "/OTP/findMany", params={"take": 1000}, headers=headers)
            if all_otps and 'data' in all_otps:
                otps = all_otps['data']
                # Filter OTPs for this phone number that are not used
                matching_otps = [otp for otp in otps if otp.get('phoneNumber') == phone_number and not otp.get('isUsed', False)]
                
                if matching_otps:
                    # Sort by createdAt (newest first) and return the latest
                    latest_otp = sorted(matching_otps, key=lambda x: x.get('createdAt', ''), reverse=True)[0]
                    return {'data': latest_otp, 'meta': all_otps.get('meta', {})}
                return None
            return None
        except Exception:
            return None
    
    async def mark_otp_used(self, otp_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Mark OTP as used"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("PUT", "/OTP/update", data={"where": {"id": otp_id}, "data": {"isUsed": True}}, headers=headers)
    
    async def cleanup_expired_otps(self, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Clean up expired OTPs"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("DELETE", "/OTP/deleteMany", data={"where": {"expiresAt": {"lt": datetime.utcnow().isoformat()}}}, headers=headers)
    
    # Session operations
    async def create_session(self, session_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """Create user session"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("POST", "/Session/create", data={"data": session_data}, headers=headers)
    
    async def get_session(self, session_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            
            # Get all sessions and filter
            all_sessions = await self._make_request("GET", "/Session/findMany", params={"take": 1000}, headers=headers)
            if all_sessions and 'data' in all_sessions:
                sessions = all_sessions['data']
                for session in sessions:
                    if session.get('id') == session_id and session.get('isActive', True):
                        return {'data': session, 'meta': all_sessions.get('meta', {})}
                return None
            return None
        except Exception:
            return None
    
    async def get_user_session(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get active session for user"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            
            # Get all sessions and filter
            all_sessions = await self._make_request("GET", "/Session/findMany", params={"take": 1000}, headers=headers)
            if all_sessions and 'data' in all_sessions:
                sessions = all_sessions['data']
                for session in sessions:
                    if (session.get('userId') == user_id and 
                        session.get('isActive', True)):
                        # Check if session is not expired (simplified comparison)
                        expires_at = datetime.fromisoformat(session['expiresAt'].replace('Z', ''))
                        current_time = datetime.utcnow()
                        if expires_at > current_time:
                            return {'data': session, 'meta': all_sessions.get('meta', {})}
                return None
            return None
        except Exception:
            return None
    
    async def invalidate_session(self, session_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Invalidate session"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("PUT", "/Session/update", data={"where": {"id": session_id}, "data": {"isActive": False}}, headers=headers)
    
    async def cleanup_expired_sessions(self, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Clean up expired sessions"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        return await self._make_request("DELETE", "/Session/deleteMany", data={"where": {"expiresAt": {"lt": datetime.utcnow().isoformat()}}}, headers=headers)

    async def invalidate_sessions_by_user(self, user_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """Invalidate all active sessions for a user."""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        # Use updateMany semantics via ZenStack: PUT /Session/updateMany is not standard; fallback to deleteMany+recreate is unsafe.
        # So fetch and individually invalidate.
        try:
            all_sessions = await self._make_request("GET", "/Session/findMany", params={"take": 1000}, headers=headers)
            sessions = all_sessions.get('data') if isinstance(all_sessions, dict) else (all_sessions if isinstance(all_sessions, list) else [])
            updated = 0
            for s in sessions:
                if s.get('userId') == user_id and s.get('isActive', True):
                    await self._make_request("PUT", "/Session/update", data={"where": {"id": s.get('id')}, "data": {"isActive": False}}, headers=headers)
                    updated += 1
            return {"updated": updated}
        except Exception as e:
            return {"updated": 0, "error": str(e)}

    # Constituency operations
    async def get_constituencies(self, user_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all constituencies"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        response = await self._make_request("GET", "/Constituency/findMany", headers=headers)
        
        # Extract data from ZenStack response format
        if isinstance(response, dict) and 'data' in response:
            return response['data']
        return response if isinstance(response, list) else []
    
    async def get_constituency_by_id(self, constituency_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get constituency by ID"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            return await self._make_request("GET", f"/Constituency/findUnique", params={"where": {"id": constituency_id}}, headers=headers)
        except Exception:
            return None

    # Grievance Department operations
    async def get_grievance_departments(self, user_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all grievance departments"""
        headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
        response = await self._make_request("GET", "/GrievanceDepartment/findMany", headers=headers)
        
        # Extract data from ZenStack response format
        if isinstance(response, dict) and 'data' in response:
            return response['data']
        return response if isinstance(response, list) else []
    
    async def get_grievance_department_by_id(self, department_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get grievance department by ID"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            return await self._make_request("GET", f"/GrievanceDepartment/findUnique", params={"where": {"id": department_id}}, headers=headers)
        except Exception:
            return None

    # Storage operations
    async def upload_file(self, file_data: bytes, filename: str, content_type: str, folder: str = "uploads", user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Upload file to Supabase Storage via ZenStack"""
        try:
            import base64
            
            print(f"🔍 ZenStack Client Debug - Upload Request:")
            print(f"  - Filename: {filename}")
            print(f"  - ContentType: {content_type}")
            print(f"  - Folder: {folder}")
            print(f"  - FileSize: {len(file_data)} bytes")
            print(f"  - UserToken: {'Present' if user_token else 'None'}")
            
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            print(f"  - Base64 length: {len(file_base64)} chars")
            
            data = {
                "file": file_base64,
                "filename": filename,
                "contentType": content_type,
                "folder": folder
            }
            
            print(f"🔍 Sending request to ZenStack service...")
            # Storage endpoints are at root level, not under /api
            url = f"http://localhost:3001/storage/upload"
            response = await self.client.request(
                method="POST",
                url=url,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            print(f"  - Response: {result}")
            return result
        except Exception as e:
            print(f"❌ Error uploading file: {e}")
            return None

    async def delete_file(self, file_path: str, user_token: Optional[str] = None) -> bool:
        """Delete file from Supabase Storage via ZenStack"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"} if user_token else {}
            data = {"filePath": file_path}
            response = await self._make_request("DELETE", "/storage/delete", data=data, headers=headers)
            return response.get("success", False)
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    # Admin operations (separate from User system)
    async def get_admins(self, skip: int = 0, take: int = 100) -> Dict[str, Any]:
        """Get all admins"""
        return await self._make_request("GET", "/Admin/findMany", params={"skip": skip, "take": take})
    
    async def get_admin(self, admin_id: str) -> Optional[Dict[str, Any]]:
        """Get admin by ID"""
        try:
            # Use GET with query parameters in the correct format
            return await self._make_request("GET", "/Admin/findUnique", params={"where": {"id": admin_id}})
        except Exception as e:
            print(f"❌ Error fetching admin: {e}")
            return None
    
    async def get_admin_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get admin by email"""
        try:
            return await self._make_request("GET", "/Admin/findUnique", params={"where": {"email": email}})
        except Exception:
            return None
    
    async def create_admin(self, admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new admin"""
        return await self._make_request("POST", "/Admin/create", data=admin_data)
    
    async def update_admin(self, admin_id: str, admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update admin"""
        return await self._make_request("PUT", f"/Admin/update", data={"where": {"id": admin_id}, "data": admin_data})
    
    async def delete_admin(self, admin_id: str) -> Dict[str, Any]:
        """Delete admin"""
        return await self._make_request("DELETE", f"/Admin/delete", data={"where": {"id": admin_id}})

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global ZenStack client instance
zenstack_client = ZenStackClient()
