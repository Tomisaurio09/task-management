#!/usr/bin/env python3
import requests
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

API_BASE_URL = "http://localhost:8000"
NUM_USERS = 100


def create_user(user_num):
    """Create a single test user"""
    email = f"loadtest{user_num}@example.com"
    password = "LoadTest123!"
    full_name = "New User Load"
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name
            },
            timeout=10
        )
        print(response.status_code, response.json())

        if response.status_code == 201:
            return {"success": True, "email": email}
        elif response.status_code == 409:  # User already exists
            return {"success": True, "email": email, "existed": True}
        else:
            return {"success": False, "email": email, "error": response.text}
    
    except Exception as e:
        return {"success": False, "email": email, "error": str(e)}


def create_initial_data_for_user(email, password):
    """Create some initial projects/boards/tasks for a user"""
    try:
        # Login
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": email, "password": password},
            timeout=10
        )
        
        if login_response.status_code != 200:
            return {"success": False, "email": email, "error": "Login failed"}
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create 2-3 projects
        projects_created = 0
        for i in range(2):
            project_response = requests.post(
                f"{API_BASE_URL}/projects",
                json={"name": f"Test Project {i+1}"},
                headers=headers,
                timeout=10
            )
            
            if project_response.status_code == 201:
                projects_created += 1
                project_id = project_response.json()["id"]
                
                # Create 1-2 boards per project
                for j in range(2):
                    board_response = requests.post(
                        f"{API_BASE_URL}/projects/{project_id}/boards",
                        json={"name": f"Board {j+1}"},
                        headers=headers,
                        timeout=10
                    )
                    
                    if board_response.status_code == 201:
                        board_id = board_response.json()["id"]
                        
                        # Create 3-5 tasks per board
                        for k in range(3):
                            requests.post(
                                f"{API_BASE_URL}/projects/{project_id}/boards/{board_id}/tasks",
                                json={
                                    "name": f"Task {k+1}",
                                    "priority": ["low", "medium", "high"][k % 3],
                                    "status": "active"
                                },
                                headers=headers,
                                timeout=10
                            )
        
        return {"success": True, "email": email, "projects": projects_created}
    
    except Exception as e:
        return {"success": False, "email": email, "error": str(e)}


def main():
    """Main setup function"""
    print("=" * 70)
    print("LOAD TEST SETUP - Creating Pre-registered Users")
    print("=" * 70)
    print(f"\nCreating {NUM_USERS} test users...")
    print(f"API endpoint: {API_BASE_URL}")
    
    # Check if API is accessible
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"API health check failed: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Cannot connect to API at {API_BASE_URL}")
        print(f"Error: {e}")
        sys.exit(1)
    
    
    # Create users in parallel
    created = 0
    existed = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_user, i) for i in range(1, NUM_USERS + 1)]
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            
            if result["success"]:
                if result.get("existed"):
                    existed += 1
                    symbol = "↻"
                else:
                    created += 1
                    symbol = "✓"
            else:
                failed += 1
                symbol = "✗"
            
            # Progress indicator
            if i % 10 == 0:
                print(f"  Progress: {i}/{NUM_USERS} users processed...")
    
    print()
    print("=" * 70)
    print("USER CREATION COMPLETE")
    print("=" * 70)
    print(f"Created: {created}")
    print(f"↻  Already existed: {existed}")
    if failed > 0:
        print(f"Failed: {failed}")
    print()
    
    if failed > NUM_USERS / 2:
        print("WARNING: More than 50% of users failed to create")
        sys.exit(1)
    
    # Create initial data for first 20 users (representative sample)
    print("Creating initial data for 20 users (projects/boards/tasks)...")
    
    data_created = 0
    for i in range(1, 21):
        email = f"loadtest{i}@example.com"
        password = "LoadTest123!"
        
        result = create_initial_data_for_user(email, password)
        if result["success"]:
            data_created += 1
            if i % 5 == 0:
                print(f"  Created data for {i}/20 users...")
    
    print()
    print(f"Created initial data for {data_created}/20 users")
    print()
    
    # Final instructions
    print("=" * 70)
    print("SETUP COMPLETE - Ready for Load Testing")
    print("=" * 70)
    print()
    print("Next steps:")
    print()
    print("1. Make sure rate limiting is DISABLED:")
    print("   Edit src/app/core/rate_limit.py")
    print("   Set: limiter.enabled = False")
    print()
    print("2. Run Locust:")
    print("   locust -f load_tests.py --host=http://localhost:8000")
    print()
    print("3. Open web UI:")
    print("   http://localhost:8089")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()