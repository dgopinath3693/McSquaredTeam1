# FastAPIApp Component

A comprehensive REST API built with FastAPI and PostgreSQL that serves as the backend for the McSquared AI analytics platform. This component exposes endpoints for managing crawled content, competitive analysis data, bot tracking information, and generates AI-powered recommendations.

## Overview

FastAPIApp provides:

- **RESTful API**: Clean, modern endpoints for all data operations
- **Database Integration**: PostgreSQL backend with SQLAlchemy ORM
- **Authentication**: User and session management
- **Data Validation**: Pydantic schemas for request/response validation
- **Analytics**: Computed metrics and recommendation generation
- **Documentation**: Auto-generated Swagger/OpenAPI docs

## Contents

### Core Files

- **`main.py`** - FastAPI application and endpoint definitions:
  - Application initialization and configuration
  - Route handlers for Items, Users, and Logs
  - Request/response processing
  - Error handling and status codes
  - Swagger documentation setup

- **`config.py`** - Configuration and settings management:
  - Database connection settings
  - Environment variable handling
  - API configuration (timeouts, limits)
  - Logging configuration
  - Feature flags

- **`database.py`** - Database connection and session management:
  - SQLAlchemy engine and session factory setup
  - Connection pooling configuration
  - Database initialization
  - Session middleware integration

- **`models.py`** - SQLAlchemy ORM models:
  - Database table definitions
  - Relationships between entities
  - Column constraints and defaults
  - Indexes for query optimization

- **`schemas.py`** - Pydantic request/response schemas:
  - Data validation models
  - Serialization/deserialization logic
  - API request bodies
  - API response formats

### Configuration Files

- **`.env.example`** - Template for environment variables:
  - Database connection string
  - API keys and secrets
  - Feature configuration
  - Port and host settings

- **`requirements.txt`** - Python dependencies:
  - FastAPI - Web framework
  - SQLAlchemy - ORM
  - Psycopg2 - PostgreSQL adapter
  - Pydantic - Data validation
  - Uvicorn - ASGI server

## Architecture

### API Structure

```
FastAPIApp/
├── Core Layer
│   ├── main.py (FastAPI app, routes)
│   └── config.py (settings)
├── Database Layer
│   ├── database.py (connections)
│   └── models.py (ORM definitions)
└── API Layer
    ├── schemas.py (Pydantic models)
    └── endpoints (route handlers)
```

### Request Flow

```
HTTP Request
    ↓
FastAPI Router
    ↓
Pydantic Schema Validation
    ↓
Route Handler
    ↓
SQLAlchemy Query
    ↓
PostgreSQL Database
    ↓
ORM to Schema Conversion
    ↓
HTTP Response
```

## Setup and Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 12+ (or Docker)
- Docker and Docker Compose (optional, for database)

### Installation Steps

#### 1. Start PostgreSQL Database

From repository root:

```bash
docker-compose up -d postgres
```

This creates a PostgreSQL container with:
- Host: localhost
- Port: 5432
- Database: mcsq_db
- User: mcsq_user
- Password: mcsq_pass

#### 2. Install Python Dependencies

```bash
cd FastAPIApp
pip install -r requirements.txt
```

#### 3. Configure Environment

Copy environment template:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```
DATABASE_URL=postgres://mcsq_user:mcsq_pass@localhost:5432/mcsq_db
API_PORT=8000
API_HOST=0.0.0.0
DEBUG=false
```

#### 4. Initialize Database

```bash
python3 database.py
```

Or using Alembic for migrations (if configured):

```bash
alembic upgrade head
```

## Running the Application

### Development Mode

```bash
# From FastAPIApp directory
python3 -m uvicorn main:app --reload --port 8000
```

Access the API at: `http://localhost:8000`

Swagger documentation: `http://localhost:8000/docs`

### Production Mode

```bash
# Using gunicorn with uvicorn workers
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## API Endpoints

### Items Endpoints

```
GET    /items/              - List all items
GET    /items/{id}          - Get item by ID
POST   /items/              - Create new item
PUT    /items/{id}          - Update item
DELETE /items/{id}          - Delete item
```

### Users Endpoints

```
GET    /users/              - List all users
GET    /users/{id}          - Get user by ID
POST   /users/              - Create new user
PUT    /users/{id}          - Update user
DELETE /users/{id}          - Delete user
```

### Logs Endpoints

```
GET    /logs/               - List all logs
GET    /logs/{id}           - Get log by ID
POST   /logs/               - Create new log entry
DELETE /logs/{id}           - Delete log entry
```

### Analytics Endpoints (Custom)

```
GET    /analytics/gaps      - Get competitive gap analysis
GET    /analytics/coverage  - Get content coverage metrics
GET    /analytics/bots      - Get bot activity summary
GET    /analytics/recommendations - Get AI recommendations
```

## Data Models

### Item Model

```python
class Item(Base):
    __tablename__ = "items"
    
    id: int              # Primary key
    name: str            # Item name
    description: str     # Item description
    price: float         # Item price
    owner_id: int        # Foreign key to User
    created_at: datetime # Creation timestamp
    updated_at: datetime # Last update timestamp
```

### User Model

```python
class User(Base):
    __tablename__ = "users"
    
    id: int              # Primary key
    username: str        # Unique username
    email: str           # Email address
    created_at: datetime # Creation timestamp
```

### Log Model

```python
class Log(Base):
    __tablename__ = "logs"
    
    id: int              # Primary key
    level: str           # Log level (INFO, ERROR, etc.)
    message: str         # Log message
    timestamp: datetime  # When logged
    source: str          # Source of log
```

## Request/Response Examples

### Create Item

**Request:**
```bash
POST /items/
Content-Type: application/json

{
  "name": "Wireless Headphones",
  "description": "High-quality noise-canceling headphones",
  "price": 199.99,
  "owner_id": 1
}
```

**Response:**
```json
{
  "id": 42,
  "name": "Wireless Headphones",
  "description": "High-quality noise-canceling headphones",
  "price": 199.99,
  "owner_id": 1,
  "created_at": "2025-01-10T10:30:45.123456",
  "updated_at": "2025-01-10T10:30:45.123456"
}
```

### Get Analytics

**Request:**
```bash
GET /analytics/gaps?owned_brand=Nike&competitor=Adidas
```

**Response:**
```json
{
  "owned_brand": "Nike",
  "competitor": "Adidas",
  "gap_score": 0.73,
  "top_gaps": [
    {
      "topic": "sustainable products",
      "gap_value": 0.85,
      "recommendation": "Increase content on eco-friendly initiatives"
    }
  ],
  "coverage_metrics": {
    "owned_pages": 145,
    "competitor_pages": 187,
    "owned_words": 520000,
    "competitor_words": 640000
  }
}
```

## Configuration Options

### Database Configuration

```python
# In config.py
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
SQLALCHEMY_ECHO = False  # Log SQL statements
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_POOL_RECYCLE = 3600
SQLALCHEMY_POOL_PRE_PING = True  # Test connections
```

### API Configuration

```python
API_TITLE = "McSquared AI Analytics API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "REST API for content analysis and AI bot tracking"
CORS_ORIGINS = ["http://localhost:3000"]  # Frontend URL
API_KEY_REQUIRED = False
```

## Integration Points

### Upstream Dependencies

- **URL_Crawler**: Provides crawled content stored in `ai_crawler_store.json`
- **ContentGapAnalysis**: Generates gap analysis reports
- **AICrawlerLogging**: Provides bot tracking data
- **AiExtractionAgent**: Provides extracted/summarized content

### Downstream Usage

- **Frontend Applications**: Consume API for dashboards
- **Analytics Pipelines**: Query data for reporting
- **Third-party Integrations**: Export data to external systems

## Security Considerations

### Database Security

```python
# Use environment variables for credentials
DATABASE_URL = os.getenv("DATABASE_URL")  # Never hardcode

# Enable SSL for remote databases
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://...?sslmode=require"
```

### API Security

```python
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate limiting (implement with slowapi or similar)
# API key validation (implement with APIKey scheme)
```

## Monitoring and Logging

### Structured Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Item created", extra={
    "item_id": item.id,
    "user_id": item.owner_id
})
```

### Health Check Endpoint

```python
@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

## Performance Optimization

### Database Indexes

```python
class Item(Base):
    __tablename__ = "items"
    
    id: int = Column(Integer, primary_key=True, index=True)
    owner_id: int = Column(Integer, ForeignKey("users.id"), index=True)
    name: str = Column(String, index=True)
```

### Query Optimization

```python
# Use select() with eager loading
from sqlalchemy import select
from sqlalchemy.orm import selectinload

query = select(User).options(selectinload(User.items))
```

## Deployment

### Docker Deployment

Create `Dockerfile` in FastAPIApp:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t mcsq-api .
docker run -p 8000:8000 --env-file .env mcsq-api
```

## Troubleshooting

### Issue: "Connection refused" to PostgreSQL
- Verify PostgreSQL is running: `docker compose ps`
- Check DATABASE_URL is correct
- Ensure port 5432 is accessible

### Issue: "Table already exists"
- Database already initialized; skip initialization step

### Issue: "ModuleNotFoundError"
- Install all requirements: `pip install -r requirements.txt`
- Verify virtual environment is activated

## Next Steps

- Implement JWT authentication for secure API access
- Add WebSocket support for real-time updates
- Create comprehensive API tests with pytest
- Set up CI/CD pipeline for automated deployment
- Add caching layer (Redis) for performance
- Implement background task queue (Celery) for async operations
