# Workouts API

A FastAPI-based REST API for managing workout plans and exercises. This API supports manual workout creation and AI-powered workout generation using OpenAI.

## Features

- **Workout Management**: Create, retrieve, and delete workout plans
- **Exercise Management**: Add and remove exercises from workouts
- **AI-Powered Generation**: Generate custom workout plans using natural language prompts via OpenAI
- **MongoDB Integration**: Persistent storage using MongoDB Atlas with X509 certificate authentication
- **Type Safety**: Pydantic models for request/response validation

## Prerequisites

- Python 3.8 or higher (for local development)
- Docker and Docker Compose (for containerized deployment)
- MongoDB Atlas account with X509 certificate authentication configured
- OpenAI API key
- X509 certificate file for MongoDB authentication

## Installation

1. **Clone the repository** and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MongoDB X509 certificate**:
   - Place your X509 certificate file in the `secrets/` directory
   - The default expected path is `secrets/X509-cert-7850383135344030658.pem`
   - Update `CERTIFICATE_FILE` in `main.py` if your certificate has a different name

5. **Set up environment variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

   Or create a `.env` file (not included in this setup):
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

## Configuration

The application uses the following configuration (defined in `main.py`):

- **MongoDB Cluster**: `cluster0.udio3ct.mongodb.net`
- **Database Name**: `schwitzerland`
- **Certificate Path**: `secrets/X509-cert-7850383135344030658.pem`

To change these settings, modify the constants at the top of `main.py`:
```python
CLUSTER_HOST = "cluster0.udio3ct.mongodb.net"
DATABASE_NAME = "schwitzerland"
CERTIFICATE_FILE = "secrets/X509-cert-7850383135344030658.pem"
```

## Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

For production, use:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### API Documentation

Once the server is running, you can access:
- **Interactive API docs (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative docs (ReDoc)**: `http://localhost:8000/redoc`

## Docker Deployment

The application can be deployed using Docker for a consistent, isolated environment.

### Prerequisites for Docker

- Docker Desktop installed and running
- X509 certificate file placed in the `secrets/` directory
- OpenAI API key set as an environment variable

### Using Docker Compose (Recommended)

1. **Navigate to the backend directory:**
   ```bash
   cd code/backend
   ```

2. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. **Build and start the container:**
   ```bash
   docker compose up --build -d
   ```

4. **View logs:**
   ```bash
   docker compose logs -f
   ```

5. **Stop the container:**
   ```bash
   docker compose down
   ```

### Using Docker Run

Alternatively, you can build and run the container directly:

1. **Build the Docker image:**
   ```bash
   docker build -t backend-api -f code/backend/Dockerfile code/backend
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 8000:8000 \
     --name backend-api-container \
     -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
     backend-api
   ```

3. **View logs:**
   ```bash
   docker logs -f backend-api-container
   ```

4. **Stop the container:**
   ```bash
   docker stop backend-api-container
   docker rm backend-api-container
   ```

### Docker Commands Reference

**Docker Compose:**
- `docker compose up -d` - Start in detached mode
- `docker compose up --build -d` - Rebuild and start
- `docker compose down` - Stop and remove containers
- `docker compose logs -f` - Follow logs
- `docker compose ps` - List running containers
- `docker compose restart` - Restart services
- `docker compose stop` - Stop without removing

**Docker Run:**
- `docker ps` - List running containers
- `docker images` - List images
- `docker logs <container-name>` - View logs
- `docker exec -it <container-name> /bin/bash` - Access container shell

### Environment Variables

The container requires the `OPENAI_API_KEY` environment variable. You can:

1. **Export it before running:**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   docker compose up -d
   ```

2. **Create a `.env` file** in the backend directory:
   ```
   OPENAI_API_KEY=your-key-here
   ```
   Docker Compose will automatically load variables from `.env`.

### Notes

- The X509 certificate is copied into the Docker image during build
- Port 8000 is exposed and mapped to `localhost:8000`
- The container runs in detached mode (`-d`) by default
- Use `docker compose logs` to debug issues

## API Endpoints

### Root Endpoint

#### `GET /`
Returns API information and available endpoints.

**Response:**
```json
{
  "message": "Welcome to the Workouts API",
  "endpoints": [
    "GET /workouts - Get all workout names",
    "POST /workouts - Add a new workout manually",
    "POST /workouts/generate - Generate a workout using AI from a prompt",
    "DELETE /workouts/{workout_name} - Delete an entire workout",
    "DELETE /workouts/{workout_name}/exercises/{exercise_name} - Delete an exercise from a workout"
  ]
}
```

### Workouts

#### `GET /workouts`
Retrieves a list of all workout names from the database.

**Response:** `List[str]`
```json
["CrossFit", "WeightLifting", "Running", "Yoga"]
```

#### `POST /workouts`
Manually adds a new workout to the database.

**Request Body:**
```json
{
  "workout_name": "Yoga",
  "exercises": {
    "Downward Dog": {
      "type": "time",
      "duration_sec": 60,
      "description": "Hold downward dog pose for 60 seconds"
    },
    "Sun Salutation": {
      "type": "repetition",
      "reps": 5,
      "description": "Complete 5 rounds of sun salutation"
    }
  }
}
```

**Response:**
```json
{
  "message": "Successfully added workout 'Yoga'",
  "workout_name": "Yoga",
  "exercises_count": 2
}
```

#### `POST /workouts/generate`
Generates a workout using OpenAI based on a natural language prompt.

**Request Body:**
```json
{
  "prompt": "I want soft yoga mainly stretching mid efforts"
}
```

**Response:**
```json
{
  "message": "Successfully generated and added workout 'Gentle Yoga'",
  "workout_name": "Gentle Yoga",
  "exercises_count": 4,
  "generated_exercises": ["Downward Dog", "Child's Pose", "Cat-Cow", "Warrior I"]
}
```

#### `DELETE /workouts/{workout_name}`
Deletes an entire workout from the database.

**Parameters:**
- `workout_name` (path): Name of the workout to delete

**Response:**
```json
{
  "message": "Successfully deleted workout 'Yoga'",
  "workout_name": "Yoga"
}
```

#### `DELETE /workouts/{workout_name}/exercises/{exercise_name}`
Deletes a specific exercise from a workout.

**Parameters:**
- `workout_name` (path): Name of the workout
- `exercise_name` (path): Name of the exercise to delete

**Response:**
```json
{
  "message": "Successfully deleted exercise 'Downward Dog' from workout 'Yoga'",
  "workout_name": "Yoga",
  "exercise_name": "Downward Dog"
}
```

## Data Models

### Exercise Types

Exercises can be one of four types:

1. **`repetition`**: Exercise based on number of repetitions
   - Required: `type`, `description`
   - Optional: `reps`

2. **`weighted repetition`**: Exercise with weight and repetitions
   - Required: `type`, `description`
   - Optional: `reps`, `weight`

3. **`time`**: Time-based exercise
   - Required: `type`, `description`
   - Optional: `duration_sec`

4. **`distance`**: Distance-based exercise
   - Required: `type`, `description`
   - Optional: `distance_m`

### Exercise Schema
```json
{
  "type": "repetition" | "weighted repetition" | "time" | "distance",
  "description": "string",
  "reps": 0,                    // Optional, for "repetition" or "weighted repetition"
  "weight": 0.0,                // Optional, for "weighted repetition"
  "duration_sec": 0,            // Optional, for "time"
  "distance_m": 0               // Optional, for "distance"
}
```

## Error Handling

The API returns standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (e.g., workout already exists)
- `404`: Not Found (e.g., workout or exercise doesn't exist)
- `500`: Internal Server Error (e.g., database connection issues, OpenAI API errors)

Error responses include a `detail` field with a description:
```json
{
  "detail": "Workout 'Yoga' already exists"
}
```

## Database Structure

Workouts are stored in MongoDB with the following structure:

```json
{
  "_id": ObjectId("..."),
  "Workout Name 1": {
    "Exercise 1": {
      "type": "repetition",
      "reps": 10,
      "description": "..."
    },
    "Exercise 2": {
      "type": "time",
      "duration_sec": 60,
      "description": "..."
    }
  },
  "Workout Name 2": {
    ...
  }
}
```

The collection name is automatically determined by the `get_collection_name()` function, which prioritizes a collection named "schwitzerland" or uses the first available collection.

## Logging

The application uses Python's logging module with INFO level logging by default. Logs include:
- Connection status
- API endpoint access
- Database operations
- OpenAI API calls
- Errors and warnings

## Development

### Testing

You can test the API using curl or any HTTP client:

```bash
# Get all workouts
curl http://localhost:8000/workouts

# Add a workout
curl -X POST http://localhost:8000/workouts \
  -H "Content-Type: application/json" \
  -d '{
    "workout_name": "Test Workout",
    "exercises": {
      "Push-ups": {
        "type": "repetition",
        "reps": 10,
        "description": "Do 10 push-ups"
      }
    }
  }'

# Generate a workout
curl -X POST http://localhost:8000/workouts/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A quick 15 minute cardio workout"}'
```

### Code Structure

- `main.py`: Main FastAPI application with all endpoints
- `connect.py`: MongoDB connection utilities (if used)
- `requirements.txt`: Python dependencies

## Troubleshooting

### MongoDB Connection Issues

- Verify the X509 certificate file exists at the specified path
- Check that the certificate file has proper read permissions
- Ensure MongoDB Atlas cluster is accessible
- Verify network connectivity to MongoDB Atlas

### OpenAI API Issues

- Ensure `OPENAI_API_KEY` environment variable is set
- Verify the API key is valid and has sufficient credits
- Check OpenAI API status if requests are failing

### Common Errors

- **"Certificate file not found"**: Place the X509 certificate in the `secrets/` directory
- **"Database connection not available"**: Check MongoDB connection settings and certificate
- **"OpenAI API key not configured"**: Set the `OPENAI_API_KEY` environment variable
- **"Workout already exists"**: The workout name must be unique

## License

See the main project license file.

