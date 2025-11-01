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


def get_latest_history() -> Dict[str, Any]:
    """Get the latest history for the user."""
    response = requests.get(f"{BASE_URL}/history/{USER_ID}/latest")
    response.raise_for_status()
    return response.json()


def update_set_progress(set_id: str, completed_reps: int):
    """Update progress on a set."""
    response = requests.post(
        f"{BASE_URL}/history/{USER_ID}/update",
        json={
            "set_id": set_id,
            "completed_reps": completed_reps
        }
    )
    response.raise_for_status()
    return response.json()


def complete_set(set_id: str) -> Dict[str, Any]:
    """Mark a set as complete."""
    response = requests.post(
        f"{BASE_URL}/history/{USER_ID}/complete",
        json={"set_id": set_id}
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


def complete_day(week_num: int = 1):
    """Complete all sets for the current day."""
    history = get_latest_history()
    day_name = history.get('day_name', 'Unknown')
    day_index = history.get('current_day_index', 0)
    
    print_header(f"Week {week_num} - Day {day_index + 1}: {day_name}")
    display_history(history)
    
    sets = history.get('sets', [])
    
    if not sets:
        print_warning(f"No sets found for {day_name}")
        return
    
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
            result = update_set_progress(set_id, partial_reps)
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
        result = complete_set(set_id)
        print_success(f"Set complete!")
        
        # Check if day/week completed
        if result.get('new_day_started'):
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 {result.get('message')}{Colors.ENDC}")
            time.sleep(1)
            return True
        elif result.get('day_complete'):
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 {result.get('message')}{Colors.ENDC}")
            time.sleep(1)
            return False
    
    return False


def main():
    """Main test workflow."""
    print_header("History Tracking Test - Full Week Simulation")
    print_info(f"Testing with User ID: {USER_ID}")
    print_info(f"API Base URL: {BASE_URL}\n")
    
    try:
        # Check initial state
        print_header("Initial State")
        try:
            initial_history = get_latest_history()
            display_history(initial_history)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print_error("User not found or user has no workouts!")
                print_warning("\nPlease run the setup script first:")
                print_info("  python scripts/setup_test_user.py")
                print_info("\nThis will create user '3' and generate a workout plan.")
                return
            raise
        
        input(f"\n{Colors.BOLD}Press Enter to start the workout week...{Colors.ENDC}")
        
        # Simulate a full week (7 days)
        week_num = 1
        day_count = 0
        max_days = 20  # Safety limit to prevent infinite loops
        
        while day_count < max_days:
            has_next_day = complete_day(week_num)
            day_count += 1
            
            if not has_next_day:
                # Check if there's another day in the plan
                try:
                    history = get_latest_history()
                    if day_count > 0 and history.get('current_day_index') == 0:
                        # We've wrapped around to a new week
                        week_num += 1
                        print_header(f"Starting Week {week_num}!")
                        
                        if week_num > 2:
                            print_success("Successfully completed 2 full weeks!")
                            print_info("Test cycle complete - stopping here.")
                            break
                    
                    # Small delay before next day
                    time.sleep(1)
                except Exception as e:
                    print_warning(f"Reached end of workout plan: {str(e)}")
                    break
            else:
                # Automatically moved to next day
                time.sleep(1)
        
        # Final summary
        print_header("Test Complete - Final Summary")
        final_history = get_latest_history()
        display_history(final_history)
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Test completed successfully!{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"   Total days completed: {day_count}")
        print(f"   Weeks completed: {week_num}")
        print(f"   Current day: {final_history.get('day_name', 'Unknown')}")
        print(f"   Current day index: {final_history.get('current_day_index', 0)}")
        
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
