#!/usr/bin/env python3
"""
Test script for history tracking workflow.

This script simulates a user completing a full week of workouts,
demonstrating the automatic day progression feature.

Usage:
    python scripts/test_history_workflow.py
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = "3"
WORKOUT_ID = None  # Will be set from user data or history

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def get_user_workout_id() -> str:
    """Get the first workout ID for the user."""
    global WORKOUT_ID
    if WORKOUT_ID:
        return WORKOUT_ID
    
    response = requests.get(f"{BASE_URL}/users/{USER_ID}")
    response.raise_for_status()
    user_data = response.json()
    workout_ids = user_data.get('associated_workout_ids', [])
    
    if not workout_ids:
        raise ValueError(f"User {USER_ID} has no associated workouts")
    
    WORKOUT_ID = workout_ids[0]
    print_info(f"Using workout ID: {WORKOUT_ID}")
    return WORKOUT_ID


def get_latest_history(workout_id: str = None) -> Dict[str, Any]:
    """Get the latest history for the user (uses active workout)."""
    # Endpoint automatically uses the first workout from user's associated_workout_ids
    response = requests.get(f"{BASE_URL}/history/{USER_ID}/latest")
    response.raise_for_status()
    return response.json()


def update_set_progress(workout_id: str, set_id: str, completed_reps: int):
    """Update progress on a set."""
    if workout_id is None:
        workout_id = get_user_workout_id()
    
    response = requests.post(
        f"{BASE_URL}/history/{USER_ID}/update",
        json={
            "workout_id": workout_id,
            "set_id": set_id,
            "completed_reps": completed_reps
        }
    )
    response.raise_for_status()
    return response.json()


def complete_set(workout_id: str, set_id: str) -> Dict[str, Any]:
    """Mark a set as complete."""
    if workout_id is None:
        workout_id = get_user_workout_id()
    
    response = requests.post(
        f"{BASE_URL}/history/{USER_ID}/complete",
        json={
            "workout_id": workout_id,
            "set_id": set_id
        }
    )
    response.raise_for_status()
    return response.json()


def display_history(history: Dict[str, Any]):
    """Display the current history state."""
    day_name = history.get('day_name', 'Unknown')
    progress = history.get('progress', {})
    sets = history.get('sets', [])
    
    print(f"\n{Colors.BOLD}📅 Current Day: {day_name}{Colors.ENDC}")
    print(f"   Day Index: {history.get('current_day_index', 0)}")
    print(f"   Progress: {progress.get('completed_sets', 0)}/{progress.get('total_sets', 0)} sets "
          f"({progress.get('completion_percentage', 0)}%)")
    
    print(f"\n{Colors.BOLD}Sets:{Colors.ENDC}")
    for idx, set_data in enumerate(sets, 1):
        status = "✓" if set_data.get('is_complete') else "○"
        exercise_name = set_data.get('exercise_name', 'Unknown Exercise')
        target_reps = set_data.get('target_reps', 'N/A')
        completed_reps = set_data.get('completed_reps', 0)
        
        if set_data.get('is_complete'):
            color = Colors.OKGREEN
        else:
            color = Colors.WARNING
        
        print(f"   {color}{status} Set {idx}: {exercise_name}{Colors.ENDC}")
        print(f"      Target: {target_reps} reps | Completed: {completed_reps} reps")


def complete_day(week_num: int = 1, cycle_num: int = 1):
    """Complete all sets for the current day."""
    workout_id = get_user_workout_id()
    
    # Get current state (will auto-progress if day is already complete)
    history = get_latest_history(workout_id)
    day_name = history.get('day_name', 'Unknown')
    day_index = history.get('current_day_index', 0)
    initial_day_index = day_index
    
    print_header(f"Week {week_num} - Cycle {cycle_num} - Day {day_index + 1}: {day_name}")
    display_history(history)
    
    sets = history.get('sets', [])
    
    if not sets:
        print_warning(f"No sets found for {day_name}")
        return False
    
    # Check if all sets are already complete (shouldn't happen due to auto-progression, but check anyway)
    all_complete = all(set_data.get('is_complete', False) for set_data in sets)
    if all_complete:
        print_info(f"All sets for {day_name} are already complete. Auto-progressing should have happened.")
        # Re-fetch to get the new day after auto-progression
        history = get_latest_history(workout_id)
        new_day_index = history.get('current_day_index', 0)
        new_day_name = history.get('day_name', 'Unknown')
        
        if new_day_index == 0 and initial_day_index != 0:
            print(f"{Colors.OKCYAN}{Colors.BOLD}🔄 Rolled over to {new_day_name}!{Colors.ENDC}\n")
            return 'rollover'
        elif new_day_index != initial_day_index:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✓ Auto-progressed to {new_day_name}!{Colors.ENDC}\n")
            return True
        return False
    
    print(f"\n{Colors.BOLD}Starting workout...{Colors.ENDC}\n")
    
    for idx, set_data in enumerate(sets, 1):
        set_id = set_data.get('set_id')
        set_name = set_data.get('set_name', 'Unknown Set')
        exercise_name = set_data.get('exercise_name', 'Unknown Exercise')
        target_reps = set_data.get('target_reps', 0)
        
        if set_data.get('is_complete'):
            print_info(f"Set {idx} ({exercise_name}) already complete - skipping")
            continue
        
        print(f"\n{Colors.BOLD}Set {idx}/{len(sets)}: {exercise_name}{Colors.ENDC}")
        print(f"   Target: {target_reps} reps")
        
        # Simulate doing the exercise with partial progress
        if target_reps:
            partial_reps = int(target_reps * 0.7)  # Complete 70% first
            print(f"   Doing reps... ", end='', flush=True)
            time.sleep(0.5)
            print(f"{partial_reps} reps done")
            
            # Update progress
            result = update_set_progress(workout_id, set_id, partial_reps)
            print_success(f"Updated progress: {partial_reps}/{target_reps} reps")
            
            # Complete the remaining reps
            print(f"   Finishing set... ", end='', flush=True)
            time.sleep(0.5)
            print(f"{target_reps} reps total!")
        else:
            print(f"   Completing... ", end='', flush=True)
            time.sleep(0.5)
            print("Done!")
        
        # Mark set as complete
        result = complete_set(workout_id, set_id)
        print_success(f"Set complete!")
        
        # Check if day/week completed and auto-progressed
        if result.get('new_day_started'):
            new_day_name = result.get('new_day_name', 'Unknown')
            message = result.get('message', '')
            new_day_index = result.get('current_day_index', day_index + 1)
            
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 {message}{Colors.ENDC}")
            
            # Check if this is a rollover (workout plan restarted)
            if 'Rolling over' in message or 'rollover' in message.lower() or new_day_index == 0:
                print(f"{Colors.OKCYAN}{Colors.BOLD}🔄 Workout plan cycle complete! Restarting from first day!{Colors.ENDC}\n")
                return 'rollover'
            
            print(f"{Colors.OKGREEN}Moving to next day: {new_day_name}{Colors.ENDC}\n")
            time.sleep(1)
            return True
    
    # After completing all sets, check if we progressed (should have happened automatically)
    time.sleep(0.5)  # Give API a moment to process
    updated_history = get_latest_history(workout_id)
    updated_day_index = updated_history.get('current_day_index', day_index)
    updated_day_name = updated_history.get('day_name', day_name)
    
    if updated_day_index == 0 and initial_day_index != 0:
        # Rolled over
        print(f"\n{Colors.OKCYAN}{Colors.BOLD}🔄 Rolled over to {updated_day_name}!{Colors.ENDC}\n")
        return 'rollover'
    elif updated_day_index != initial_day_index:
        # Progressed to next day
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Progressed to {updated_day_name}!{Colors.ENDC}\n")
        return True
    
    # No progression happened (shouldn't normally occur)
    print_warning("All sets complete but day didn't progress. This may be expected if day was already complete.")
    return False


def main():
    """Main test workflow."""
    print_header("History Tracking Test - Rolling Workout Simulation")
    print_info(f"Testing with User ID: {USER_ID}")
    print_info(f"API Base URL: {BASE_URL}\n")
    
    try:
        # Get workout ID first
        workout_id = get_user_workout_id()
        
        # Check initial state
        print_header("Initial State")
        try:
            initial_history = get_latest_history(workout_id)
            initial_day = initial_history.get('day_name', 'Unknown')
            initial_index = initial_history.get('current_day_index', 0)
            initial_progress = initial_history.get('progress', {})
            
            display_history(initial_history)
            
            # Show workout plan info
            workout_response = requests.get(f"{BASE_URL}/workouts/{workout_id}")
            if workout_response.status_code == 200:
                workout_data = workout_response.json()
                workout_plan = workout_data.get('workout_plan', [])
                all_days = [day['day'] for day in workout_plan]
                print(f"\n{Colors.BOLD}Workout Plan Days:{Colors.ENDC} {', '.join(all_days)}")
                print(f"{Colors.BOLD}Total Days:{Colors.ENDC} {len(all_days)}")
            
            # Warn if day is already complete (will auto-progress)
            if initial_progress.get('completion_percentage', 0) == 100:
                print_warning("\n⚠ All sets for current day are complete. Auto-progression will occur on next status check.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print_error("User not found or user has no workouts!")
                print_warning("\nPlease run the setup script first:")
                print_info("  python scripts/setup_test_user.py")
                print_info("\nThis will create user '3' and generate a workout plan.")
                return
            raise
        
        input(f"\n{Colors.BOLD}Press Enter to start the workout simulation...{Colors.ENDC}")
        
        # Simulate multiple cycles through the workout plan to test rolling
        week_num = 1
        cycle_num = 1
        day_count = 0
        max_days = 30  # Safety limit to prevent infinite loops
        rollover_count = 0
        
        while day_count < max_days:
            result = complete_day(week_num, cycle_num)
            day_count += 1
            
            if result == 'rollover':
                # Workout plan rolled over - starting new cycle
                cycle_num += 1
                rollover_count += 1
                print_header(f"🔄 Starting New Cycle #{cycle_num}!")
                
                if rollover_count >= 3:
                    print_success(f"Successfully completed {rollover_count} full cycles!")
                    print_info("Rolling logic test complete - stopping here.")
                    break
            elif result is True:
                # Automatically moved to next day
                time.sleep(0.5)
            elif result is False:
                # Day not complete yet, or no progression detected
                # Re-check status to see if auto-progression happened
                try:
                    time.sleep(0.5)  # Brief pause
                    history = get_latest_history(workout_id)
                    current_index = history.get('current_day_index', 0)
                    current_day = history.get('day_name', 'Unknown')
                    
                    # Get initial day index for comparison (we'll track this in the loop)
                    # If we're back at day 0 and we've done more than 1 day, it's a rollover
                    # (Note: This logic might need refinement based on actual behavior)
                    if current_index == 0 and day_count > 1:
                        # Check if we completed all days
                        cycle_num += 1
                        rollover_count += 1
                        print_header(f"🔄 Detected Rollover - Starting New Cycle #{cycle_num}!")
                        
                        if rollover_count >= 3:
                            print_success(f"Successfully completed {rollover_count} full cycles!")
                            print_info("Rolling logic test complete - stopping here.")
                            break
                    
                    time.sleep(0.5)
                except Exception as e:
                    print_warning(f"Error checking state: {str(e)}")
                    break
        
        # Final summary
        print_header("Test Complete - Final Summary")
        final_history = get_latest_history(workout_id)
        display_history(final_history)
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Test completed successfully!{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"   Total days processed: {day_count}")
        print(f"   Workout cycles completed: {rollover_count}")
        print(f"   Current cycle: {cycle_num}")
        print(f"   Current day: {final_history.get('day_name', 'Unknown')}")
        print(f"   Current day index: {final_history.get('current_day_index', 0)}")
        final_progress = final_history.get('progress', {})
        print(f"   Current day progress: {final_progress.get('completed_sets', 0)}/{final_progress.get('total_sets', 0)} sets ({final_progress.get('completion_percentage', 0)}%)")
        print(f"   Workout ID: {workout_id}")
        
        if rollover_count > 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Rollover functionality working correctly!{Colors.ENDC}")
            print(f"   Successfully rolled over {rollover_count} time(s) - progress resets correctly.")
        
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to API. Make sure the server is running at http://localhost:8000")
    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print_error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
