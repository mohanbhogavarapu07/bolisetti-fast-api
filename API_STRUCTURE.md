# Bollisetti API Structure - Unified Entity-Based Routes

## Overview
The API has been refactored to use a unified, entity-based structure with role-based access control. This eliminates duplication and provides a cleaner, more maintainable codebase.

## Route Structure

### 1. Users (`/api/users`)
- **POST** `/send-otp` - Send OTP to phone number
- **POST** `/verify-otp` - Verify OTP and authenticate user
- **GET** `/me` - Get current user info
- **POST** `/logout` - User logout
- **GET** `/validate` - Validate user access
- **PUT** `/profile` - Update user profile
- **POST** `/register` - Register new user (alternative to OTP flow)
- **GET** `/admin/all` - Get all users (Admin only)
- **DELETE** `/admin/{user_id}` - Delete user (Admin only)

### 2. Grievances (`/api/grievances`)
- **GET** `/` - Get all grievances (User/Admin)
- **GET** `/user/{user_id}` - Get user's grievances
- **GET** `/my` - Get current user's grievances
- **GET** `/{grievance_id}` - Get grievance by ID
- **POST** `/` - Create grievance (User)
- **PUT** `/{grievance_id}` - Update grievance (Owner or Admin)
- **DELETE** `/{grievance_id}` - Delete grievance (Owner or Admin)

#### Admin-only Grievance Endpoints:
- **GET** `/admin/all` - Get all grievances (Admin only)
- **GET** `/admin/ongoing` - Get ongoing grievances (Admin only)
- **PUT** `/admin/{grievance_id}/status` - Update grievance status (Admin only)

### 3. News (`/api/news`)
- **GET** `/` - Get all news articles (Public)
- **GET** `/{news_id}` - Get news by ID (Public)
- **POST** `/` - Create news article (Admin only)
- **PUT** `/{news_id}` - Update news article (Admin only)
- **DELETE** `/{news_id}` - Delete news article (Admin only)

### 4. Projects (`/api/projects`)
- **GET** `/` - Get all projects (Public)
- **GET** `/{project_id}` - Get project by ID (Public)
- **POST** `/` - Create project (Admin only)
- **PUT** `/{project_id}` - Update project (Admin only)
- **DELETE** `/{project_id}` - Delete project (Admin only)

### 5. Schedule Events (`/api/schedule_events`)
- **GET** `/` - Get all events (Public)
- **GET** `/{event_id}` - Get event by ID (Public)
- **POST** `/` - Create event (Admin only)
- **PUT** `/{event_id}` - Update event (Admin only)
- **DELETE** `/{event_id}` - Delete event (Admin only)

### 6. Media (`/api/media`)
- **GET** `/` - Get all media (User/Admin)
- **POST** `/` - Upload media (User/Admin)
- **DELETE** `/{media_id}` - Delete media (Owner or Admin)

### 7. Notifications (`/api/notifications`)
- **GET** `/` - Get user notifications
- **PUT** `/{notification_id}/read` - Mark notification as read
- **DELETE** `/{notification_id}` - Delete notification

### 8. Constituencies (`/api/constituencies`)
- **GET** `/` - Get all constituencies (Public)
- **GET** `/{constituency_id}` - Get constituency by ID (Public)

### 9. Departments (`/api/departments`)
- **GET** `/` - Get all departments (Public)
- **GET** `/{department_id}` - Get department by ID (Public)

### 10. Admin Authentication (`/api/admin/auth`)
- **POST** `/login` - Admin login
- **GET** `/me` - Get current admin info
- **POST** `/logout` - Admin logout
- **GET** `/validate` - Validate admin access
- **POST** `/create` - Create admin (Super admin only)
- **GET** `/list` - List all admins (Admin only)
- **PUT** `/update/{admin_id}` - Update admin (Admin only)
- **DELETE** `/delete/{admin_id}` - Delete admin (Super admin only)

## Role-Based Access Control

### Public Access
- Projects (read-only)
- News (read-only)
- Schedule Events (read-only)
- Constituencies (read-only)
- Departments (read-only)

### User Access
- Own profile management
- Own grievances (CRUD)
- Own notifications
- Media upload/management

### Admin Access
- All user management
- All grievance management
- News management (CRUD)
- Project management (CRUD)
- Event management (CRUD)
- Dashboard statistics
- Admin user management

## Key Features

1. **Unified Structure**: Each entity has its own router with all related operations
2. **Role-Based Access**: Clear separation between public, user, and admin access
3. **No Duplication**: Admin operations are integrated into entity routers
4. **Consistent Naming**: Clear, intuitive endpoint names
5. **Proper Authentication**: JWT-based authentication with role checking
6. **Resource Ownership**: Users can only access their own resources unless they're admin

## Benefits

1. **Maintainability**: Single source of truth for each entity
2. **Scalability**: Easy to add new endpoints to existing entities
3. **Security**: Clear role-based access control
4. **Developer Experience**: Intuitive API structure
5. **Documentation**: Self-documenting with clear role requirements
