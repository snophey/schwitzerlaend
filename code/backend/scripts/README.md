# Backend Scripts

This directory contains utility scripts for testing and managing the Workouts API.

## Quick Start

Before running the history workflow test, set up the test user:

```bash
# 1. Make sure API server is running
python main.py  # or uvicorn main:app --reload

# 2. Set up test user (creates user "3" with a workout plan)
python scripts/setup_test_user.py

# 3. Run the history workflow test
python scripts/test_history_workflow.py
```

## Available Scripts

### setup_test_user.py

**Purpose:** Prepares the database for history tracking tests by creating user "3" with a workout plan.

**What it does:**
1. Creates user "3" if it doesn't exist
2. Checks if user has any workouts
3. If no workouts exist, generates a 3-day beginner workout using AI
4. Verifies everything is ready for testing

**Usage:**

```bash
python scripts/setup_test_user.py
```

**Prerequisites:**
- API server running at http://localhost:8000
- `requests` library installed: `pip install requests`
- OpenAI API key (set as `OPENAI_API_KEY` environment variable)
- Exercises loaded in the database (for AI workout generation)

**Note:** This script should be run before `test_history_workflow.py` to ensure user "3" has a workout plan to test with.

### test_history_workflow.py

A comprehensive test script that simulates a user completing workouts over multiple weeks using the history tracking system.

**Purpose:**
- Tests the history tracking endpoints (`/history/{user_id}/latest`, `/history/{user_id}/update`, `/history/{user_id}/complete`)
- Demonstrates automatic day progression when all sets in a day are completed
- Simulates partial progress updates and full completions
- Shows week-to-week cycling through the workout plan

**Prerequisites:**
1. The API server must be running at `http://localhost:8000`
2. User ID "3" must exist in the database with at least one associated workout
3. Python `requests` library must be installed: `pip install requests`

**Usage:**

```bash
# From the backend directory
cd code/backend

# Run the script
python scripts/test_history_workflow.py

# Or make it executable and run directly
chmod +x scripts/test_history_workflow.py
./scripts/test_history_workflow.py
```

**What it does:**

1. **Initial State Check**: Displays the current workout status for user "3"
2. **Day Simulation**: For each day in the workout plan:
   - Shows the day name and all sets to complete
   - Simulates partial progress (70% of target reps)
   - Updates progress via API
   - Completes the remaining reps
   - Marks each set as complete
3. **Automatic Progression**: When all sets in a day are complete, automatically moves to the next day
4. **Week Cycling**: Completes two full weeks to demonstrate the system handles week transitions
5. **Summary**: Shows final statistics including days completed and current position

**Sample Output:**

```
================================================================================
                   History Tracking Test - Full Week Simulation                
================================================================================

ℹ Testing with User ID: 3
ℹ API Base URL: http://localhost:8000

================================================================================
                                 Initial State                                 
================================================================================

📅 Current Day: Monday
   Day Index: 0
   Progress: 0/3 sets (0.0%)

Sets:
   ○ Set 1: Push-ups
      Target: 15 reps | Completed: 0 reps
   ○ Set 2: Squats
      Target: 20 reps | Completed: 0 reps
   ○ Set 3: Plank
      Target: 30 reps | Completed: 0 reps

Press Enter to start the workout week...

================================================================================
                          Week 1 - Day 1: Monday                          
================================================================================
...
```

**Configuration:**

You can modify the script to test with different users or API endpoints:

```python
# At the top of the script
BASE_URL = "http://localhost:8000"  # Change API URL if needed
USER_ID = "3"                        # Change user ID to test with
```

**Troubleshooting:**

If you get connection errors:
- Ensure the API server is running: `python main.py` or `uvicorn main:app --reload`
- Check the API is accessible at http://localhost:8000
- Verify the port number matches your server configuration

If you get 404 errors for the user:
- Make sure user "3" exists in the database
- Check that the user has at least one associated workout
- You can create a user via: `POST /users/3`

## Adding New Scripts

When adding new test or utility scripts to this directory:

1. Include a docstring at the top explaining the script's purpose
2. Add configuration variables at the top for easy customization
3. Include error handling for common issues (connection errors, missing data, etc.)
4. Update this README with usage instructions
5. Make scripts executable with `chmod +x`
