# FastAPI Application with PostgreSQL

A FastAPI application with PostgreSQL database integration featuring three main endpoints for managing Items, Users, and Logs.

## Project Structure

```
FastAPIApp/
├── main.py                 # FastAPI application and endpoints
├── config.py              # Configuration and settings management
├── database.py            # Database connection and session management
├── models.py              # SQLAlchemy ORM models
├── schemas.py             # Pydantic request/response schemas
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment variables
└── README.md              # This file
```

## Setup and Installation

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- PostgreSQL (running in Docker container)

### 1. Start PostgreSQL Database

From the project root directory:

```bash
docker-compose up -d
```

This starts a PostgreSQL container with the following credentials:
- **Host**: localhost
- **Port**: 5432
- **Database**: mcsq_db
- **User**: mcsq_user
- **Password**: mcsq_pass

### 2. Install Python Dependencies

```bash
cd FastAPIApp
pip install -r requirements.txt
```

### 3. Configure Environment (Optional)

Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

### 4. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check

- **GET** `/health` - Check if API is running

### Items Endpoint

- **POST** `/items/` - Create a new item
  ```json
  {
    "name": "Item Name",
    "description": "Optional description"
  }
  ```

- **GET** `/items/` - List all items (with pagination)
  - Query params: `skip=0`, `limit=10`

- **GET** `/items/{item_id}` - Get a specific item

### Users Endpoint

- **POST** `/users/` - Create a new user
  ```json
  {
    "email": "user@example.com",
    "name": "User Name"
  }
  ```

- **GET** `/users/` - List all users (with pagination)
  - Query params: `skip=0`, `limit=10`

- **GET** `/users/{user_id}` - Get a specific user

### Logs Endpoint

- **POST** `/logs/` - Create a new log entry
  ```json
  {
    "event_type": "info",
    "message": "Log message content"
  }
  ```

- **GET** `/logs/` - List all logs (with pagination)
  - Query params: `skip=0`, `limit=10`

- **GET** `/logs/type/{event_type}` - Filter logs by event type
  - Query params: `skip=0`, `limit=10`

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Database Models

### Item
- `id` (Integer, Primary Key)
- `name` (String, Required)
- `description` (Text, Optional)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### User
- `id` (Integer, Primary Key)
- `email` (String, Unique, Required)
- `name` (String, Required)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Log
- `id` (Integer, Primary Key)
- `event_type` (String, Required)
- `message` (Text, Required)
- `created_at` (DateTime)

## Development

### Enable SQL Debugging

In `database.py`, change `echo=False` to `echo=True` to see all SQL queries.

### Add New Models

1. Create a new model class in `models.py` inheriting from `Base`
2. Create corresponding schemas in `schemas.py`
3. Add endpoints in `main.py`
4. Tables are automatically created on startup

### Stopping the Database

```bash
docker-compose down
```

To remove data volumes:

```bash
docker-compose down -v
```

## Error Handling

The application includes comprehensive error handling:
- 404 errors for non-existent resources
- 400 errors for invalid requests (e.g., duplicate email)
- Proper HTTP status codes for all responses

## Environment Variables

Configure via `.env` file:
- `DATABASE_URL` - Full PostgreSQL connection string
- `DATABASE_HOST` - Hostname
- `DATABASE_PORT` - Port number
- `DATABASE_NAME` - Database name
- `DATABASE_USER` - Username
- `DATABASE_PASSWORD` - Password

## License

MIT
