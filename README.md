# Bollisetti Backend API

A FastAPI-based backend service for the Bollisetti Government Services mobile and web applications, built with Supabase, Prisma, and ZenStack.

## Features

- **User Management**: Complete user registration, authentication, and profile management
- **Grievance System**: Submit, track, and manage citizen grievances with photo attachments
- **Content Management**: News articles, development projects, and scheduled events
- **Media Management**: Image and video uploads with Supabase storage
- **Notification System**: User-specific and public notifications
- **Role-based Access Control**: Admin and user permissions
- **Real-time Updates**: WebSocket support for live notifications

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Supabase**: Backend-as-a-Service for authentication and storage
- **Prisma**: Type-safe database ORM
- **ZenStack**: Authorization layer for Prisma
- **PostgreSQL**: Primary database
- **Python 3.9+**: Programming language

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - User logout
- `POST /api/auth/forgot-password` - Password reset

### User Management
- `GET /api/users` - Get all users (with pagination)
- `GET /api/users/{id}` - Get user by ID
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Deactivate user
- `GET /api/users/me/profile` - Get current user profile
- `PUT /api/users/me/profile` - Update current user profile

### Grievances
- `POST /api/grievances` - Submit new grievance
- `GET /api/grievances` - Get all grievances (with filters)
- `GET /api/grievances/{id}` - Get grievance by ID
- `PUT /api/grievances/{id}` - Update grievance
- `DELETE /api/grievances/{id}` - Delete grievance
- `GET /api/grievances/user/{userId}` - Get user's grievances
- `PUT /api/grievances/assign/{grievanceId}` - Assign grievance to department
- `GET /api/grievances/stats/summary` - Get grievance statistics

### Content Management (Public/Read-only)
- `GET /api/news` - Get all news articles
- `GET /api/news/{id}` - Get news article by ID
- `GET /api/projects` - Get all development projects
- `GET /api/projects/{id}` - Get project by ID
- `GET /api/schedule_events` - Get all scheduled events
- `GET /api/media` - Get all media files

### Admin Content Management
- `POST /api/news` - Create news article (Admin)
- `PUT /api/news/{id}` - Update news article (Admin)
- `DELETE /api/news/{id}` - Delete news article (Admin)
- `POST /api/projects` - Create project (Admin)
- `PUT /api/projects/{id}` - Update project (Admin)
- `DELETE /api/projects/{id}` - Delete project (Admin)
- `POST /api/schedule_events` - Create scheduled event (Admin)
- `PUT /api/schedule_events/{id}` - Update scheduled event (Admin)
- `DELETE /api/schedule_events/{id}` - Delete scheduled event (Admin)

### Notifications
- `GET /api/notifications/user/{userId}` - Get user notifications
- `GET /api/notifications/my` - Get current user notifications
- `GET /api/notifications/public` - Get public notifications
- `PUT /api/notifications/{id}/mark-read` - Mark notification as read
- `PUT /api/notifications/mark-all-read` - Mark all notifications as read

### File Upload
- `POST /api/upload/image` - Upload image file
- `POST /api/upload/video` - Upload video file
- `POST /api/upload/document` - Upload document file
- `POST /api/upload/multiple` - Upload multiple files

## Setup Instructions

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Supabase account
- Node.js (for Prisma CLI)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bolisetti-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Update `.env` with your configuration:
   ```env
   # Supabase Configuration
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_KEY=your_supabase_anon_key_here
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
   
   # Database Configuration
   DATABASE_URL=postgresql://username:password@localhost:5432/bolisetti_db
   
   # JWT Configuration
   SECRET_KEY=your_secret_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # App Configuration
   APP_NAME=Bollisetti Backend
   APP_VERSION=1.0.0
   DEBUG=True
   
   # CORS Configuration
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:19006
   
   # File Upload Configuration
   MAX_FILE_SIZE=10485760  # 10MB
   UPLOAD_DIR=uploads
   ```

5. **Set up Supabase**
   - Create a new Supabase project
   - Get your project URL and API keys
   - Create a storage bucket named "bolisetti-files"
   - Update your `.env` file with Supabase credentials

6. **Set up database**
   ```bash
   # Generate Prisma client
   npx prisma generate
   
   # Run database migrations
   npx prisma db push
   
   # (Optional) Seed the database
   npx prisma db seed
   ```

7. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, you can access:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

## Database Schema

The application uses the following main entities:

- **Users**: User accounts with roles and constituencies
- **Grievances**: Citizen complaints with status tracking
- **News**: Public news articles
- **Projects**: Development projects
- **Schedule Events**: Public events and meetings
- **Media**: File uploads (images, videos)
- **Notifications**: User and public notifications

## Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## File Upload

Files are uploaded to Supabase storage and URLs are returned for database storage.

Supported file types:
- **Images**: JPEG, PNG, GIF, WebP
- **Videos**: MP4, AVI, MOV, WMV
- **Documents**: PDF, DOC, DOCX

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### Database Migrations
```bash
# Create a new migration
npx prisma migrate dev --name your_migration_name

# Apply migrations
npx prisma migrate deploy
```

## Deployment

### Docker Deployment
```bash
# Build the image
docker build -t bolisetti-backend .

# Run the container
docker run -p 8000:8000 bolisetti-backend
```

### Environment Variables for Production
Make sure to set these environment variables in production:
- `DEBUG=False`
- `SECRET_KEY` (use a strong, random secret)
- `DATABASE_URL` (production database URL)
- `SUPABASE_URL` and `SUPABASE_KEY` (production Supabase credentials)
- `ALLOWED_ORIGINS` (your production domains)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
