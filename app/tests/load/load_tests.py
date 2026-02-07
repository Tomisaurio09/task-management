# locustfile.py
"""
Load testing for Task Management API using Locust.

Run with:
    locust -f app/tests/load/load_tests.py --host=http://localhost:8000

Access web UI at: http://localhost:8089
Turn off the limiter with limiter.enabled = False
"""

from locust import HttpUser, task, between
import random


class AuthenticatedUser(HttpUser):
    """Base class for authenticated users"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts - register and login"""
        # Register a unique user
        self._email = f"loadtest_{random.randint(10000, 99999)}@example.com"
        self._password = "LoadTest123"

        self.projects = []
        self.boards = {}  
        self.tasks_ids = {}   
        self.headers = {}
        full_name = random.choice([
            "Juan Perez",
            "Maria Gonzalez",
            "Carlos Lopez",
            "Ana Martinez",
            "Lucia Fernandez"
        ])
        response = self.client.post("/auth/register", json={
            "email": self._email,
            "password": self._password,
            "full_name": full_name
        })
        
        if response.status_code != 201:
            print(f"Registration failed: {response.text}")
            return
        
        # Login
        response = self.client.post("/auth/login", data={
            "username": self._email,
            "password": self._password
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print(f"Login failed: {response.text}")
    
    @task(3)
    def create_project(self):
        """Create a new project (weighted 3x)"""
        response = self.client.post(
            "/projects",
            json={"name": f"Project {random.randint(1000, 9999)}"},
            headers=self.headers,
            name="/projects [POST]"
        )
        
        if response.status_code == 201:
            project = response.json()
            self.projects.append(project["id"])
    
    @task(5)
    def list_projects(self):
        """List projects (weighted 5x - most common operation)"""
        params = {
            "page": random.randint(1, 3),
            "page_size": random.choice([10, 20, 50])
        }
        
        self.client.get(
            "/projects",
            params=params,
            headers=self.headers,
            name="/projects [GET]"
        )
    @task(2)
    def get_project_details(self):
        """Get specific project details"""
        if not self.projects:
            return
        
        project_id = random.choice(self.projects)
        self.client.get(
            f"/projects/{project_id}",
            headers=self.headers,
            name="/projects/{id} [GET]"
        )
    @task(3)
    def create_board(self):
        """Create a board in a project"""
        if not self.projects:
            return
        
        project_id = random.choice(self.projects)
        response = self.client.post(
            f"/projects/{project_id}/boards",
            json={"name": f"Board {random.randint(1000, 9999)}"},
            headers=self.headers,
            name="/projects/{id}/boards [POST]"
        )
        
        if response.status_code == 201:
            board = response.json()
            if project_id not in self.boards:
                self.boards[project_id] = []
            self.boards[project_id].append(board["id"])
    
    @task(4)
    def list_boards(self):
        """List boards in a project"""
        if not self.projects:
            return
        
        project_id = random.choice(self.projects)
        params = {
            "page": 1,
            "page_size": 20,
            "sort_by": random.choice(["name", "position", "created_at"]),
            "sort_order": random.choice(["asc", "desc"])
        }
        
        self.client.get(
            f"/projects/{project_id}/boards",
            params=params,
            headers=self.headers,
            name="/projects/{id}/boards [GET]"
        )
    
    @task(4)
    def create_task(self):
        """Create a task in a board"""
        if not self.boards:
            return
        
        project_id = random.choice(list(self.boards.keys()))
        if not self.boards[project_id]:
            return
        
        board_id = random.choice(self.boards[project_id])
        
        task_data = {
            "name": f"Task {random.randint(1000, 9999)}",
            "description": f"Description for task {random.randint(1000, 9999)}",
            "priority": random.choice(["low", "medium", "high"]),
            "status": random.choice(["active", "completed"])
        }
        
        response = self.client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json=task_data,
            headers=self.headers,
            name="/projects/{id}/boards/{id}/tasks [POST]"
        )
        if response.status_code == 201:
            task = response.json()
            if board_id not in self.tasks_ids:
                self.tasks_ids[board_id] = []
            self.tasks_ids[board_id].append(task["id"])
    
    @task(6)
    def list_tasks(self):
        """List tasks in a board (weighted 6x - very common)"""
        if not self.boards:
            return
        
        project_id = random.choice(list(self.boards.keys()))
        if not self.boards[project_id]:
            return
        
        board_id = random.choice(self.boards[project_id])
        
        params = {
            "page": 1,
            "page_size": random.choice([10, 20, 50]),
            "sort_by": random.choice(["name", "position", "due_date", "priority"]),
            "sort_order": random.choice(["asc", "desc"]),
            "status": random.choice([None, "active", "completed"]),
            "priority": random.choice([None, "low", "medium", "high"])
        }
        
        params = {k: v for k, v in params.items() if v is not None}
        
        self.client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            params=params,
            headers=self.headers,
            name="/projects/{id}/boards/{id}/tasks [GET]"
        )
    
    @task(2)
    def update_task(self):
        """Update a task"""
        if not self.tasks_ids:
            return
        
        board_id = random.choice(list(self.tasks_ids.keys()))
        if not self.tasks_ids[board_id]:
            return
        
        task_id = random.choice(self.tasks_ids[board_id])
        
        # Find project_id for this board
        project_id = None
        for pid, boards in self.boards.items():
            if board_id in boards:
                project_id = pid
                break
        if not project_id:
            return
     
        update_data = {
            "status": random.choice(["active", "completed"]),
            "priority": random.choice(["low", "medium", "high"])
        }
        
        self.client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            json=update_data,
            headers=self.headers,
            name="/projects/{id}/boards/{id}/tasks/{id} [PATCH]"
        )
    
    @task(1)
    def update_project(self):
        """Update a project"""
        if not self.projects:
            return
        
        project_id = random.choice(self.projects)
        
        self.client.patch(
            f"/projects/{project_id}",
            json={"name": f"Updated Project {random.randint(1000, 9999)}"},
            headers=self.headers,
            name="/projects/{id} [PATCH]"
        )
