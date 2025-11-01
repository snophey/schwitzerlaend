#!/usr/bin/env python3
"""
Diagnostic script to check user "3" status in the database.

This helps debug why the history endpoint might be returning 404.
"""

import requests
import json

BASE_URL = "http://localhost:8000"
USER_ID = "3"

class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    OKCYAN = '\033[96m'


def main():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}Diagnostic Check for User '{USER_ID}'{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    try:
        # Check if user exists
        print(f"{Colors.OKCYAN}1. Checking if user exists...{Colors.ENDC}")
        response = requests.get(f"{BASE_URL}/users/{USER_ID}")
        
        if response.status_code == 404:
            print(f"{Colors.FAIL}✗ User '{USER_ID}' does NOT exist{Colors.ENDC}")
            print(f"\n{Colors.WARNING}Action needed:{Colors.ENDC}")
            print(f"  Run: python scripts/setup_test_user.py")
            return
        
        response.raise_for_status()
        user_data = response.json()
        print(f"{Colors.OKGREEN}✓ User '{USER_ID}' exists{Colors.ENDC}")
        
        # Check associated workouts
        print(f"\n{Colors.OKCYAN}2. Checking associated workouts...{Colors.ENDC}")
        workout_ids = user_data.get('associated_workout_ids', [])
        
        print(f"   User data: {json.dumps(user_data, indent=2)}")
        
        if not workout_ids or workout_ids == []:
            print(f"\n{Colors.FAIL}✗ User has NO associated workouts{Colors.ENDC}")
            print(f"\n{Colors.WARNING}This is why you're getting a 404!{Colors.ENDC}")
            print(f"\n{Colors.WARNING}Action needed:{Colors.ENDC}")
            print(f"  Run: python scripts/setup_test_user.py")
            print(f"  This will generate a workout and associate it with user '{USER_ID}'")
            return
        
        print(f"{Colors.OKGREEN}✓ User has {len(workout_ids)} associated workout(s){Colors.ENDC}")
        print(f"   Workout IDs: {workout_ids}")
        
        # Check if workouts actually exist
        print(f"\n{Colors.OKCYAN}3. Verifying workouts exist...{Colors.ENDC}")
        for workout_id in workout_ids:
            workout_response = requests.get(f"{BASE_URL}/workouts/{workout_id}")
            if workout_response.status_code == 200:
                workout_data = workout_response.json()
                workout_plan = workout_data.get('workout_plan', [])
                print(f"{Colors.OKGREEN}✓ Workout '{workout_id}' exists with {len(workout_plan)} day(s){Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}✗ Workout '{workout_id}' not found{Colors.ENDC}")
        
        # Test if history router is loaded
        print(f"\n{Colors.OKCYAN}4. Checking if history router is loaded...{Colors.ENDC}")
        try:
            health_response = requests.get(f"{BASE_URL}/history/health")
            if health_response.status_code == 200:
                print(f"{Colors.OKGREEN}✓ History router is loaded{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}✗ History router health check failed: {health_response.status_code}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}✗ History router not accessible: {str(e)}{Colors.ENDC}")
            print(f"\n{Colors.WARNING}The history router may not be registered in main.py{Colors.ENDC}")
            print(f"{Colors.WARNING}Please restart the server if you just added the router{Colors.ENDC}")
        
        # Try to get history
        print(f"\n{Colors.OKCYAN}5. Testing history endpoint...{Colors.ENDC}")
        history_response = requests.get(f"{BASE_URL}/history/{USER_ID}/latest")
        
        if history_response.status_code == 200:
            print(f"{Colors.OKGREEN}✓ History endpoint works!{Colors.ENDC}")
            history_data = history_response.json()
            print(f"   Current day: {history_data.get('day_name')}")
            print(f"   Sets: {len(history_data.get('sets', []))}")
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}Everything looks good! You can run the test:{Colors.ENDC}")
            print(f"  python scripts/test_history_workflow.py")
        else:
            print(f"{Colors.FAIL}✗ History endpoint returned {history_response.status_code}{Colors.ENDC}")
            print(f"   Error: {history_response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"{Colors.FAIL}✗ Could not connect to API{Colors.ENDC}")
        print(f"\n{Colors.WARNING}Action needed:{Colors.ENDC}")
        print(f"  Start the server: python main.py")
    except Exception as e:
        print(f"{Colors.FAIL}✗ Error: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
