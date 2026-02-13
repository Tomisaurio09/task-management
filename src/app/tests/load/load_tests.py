# locustfile.py


from locust import HttpUser, task, between, events
import random
import logging

# Pre-registered test users (created by setup_users.py)
TEST_USERS = [
    {"email": f"loadtest{i}@example.com", "password": "LoadTest123!"}
    for i in range(1, 101)  # 100 pre-registered users
]

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test - log that pre-registered users should be created"""
    logger.info("=" * 60)
    logger.info("LOAD TEST STARTING")
    logger.info("Using pre-registered users: loadtest1@example.com - loadtest100@example.com")
    logger.info("=" * 60)


class TaskManagementUser(HttpUser):
    """
    Simulates a realistic user workflow:
    1. Login with existing credentials
    2. Discover existing projects/boards/tasks
    3. Perform typical daily operations (read-heavy)
    4. Create/update content occasionally
    """
    wait_time = between(1, 3)  # Realistic think time between actions
    
    def on_start(self):
        """Initialize user session"""
        user = random.choice(TEST_USERS)
        self._email = user["email"]
        self._password = user["password"]
        
        # State tracking
        self.projects = []
        self.boards = {}  # {project_id: [board_ids]}
        self.tasks_id = {}   # {board_id: [task_ids]}
        self.headers = {}
        
        self._login()
        
        self._discover_projects()
    
    def _login(self):
        """Login with pre-registered credentials"""
        response = self.client.post(
            "/auth/login",
            data={
                "username": self._email,
                "password": self._password
            },
            name="Auth: Login"
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            logger.error(f"Login failed for {self._email}: {response.text}")
            self.environment.runner.quit()
    
    def _discover_projects(self):
        """Load user's existing projects on startup"""
        response = self.client.get(
            "/projects?page=1&page_size=50",
            headers=self.headers,
            name="Startup: Discover projects"
        )
        
        if response.status_code == 200:
            items = response.json().get("items", [])
            self.projects = [p["id"] for p in items]
            
            if self.projects and len(self.projects) > 0:
                project_id = self.projects[0]
                self._discover_boards(project_id)
    
    def _discover_boards(self, project_id):
        """Load boards for a project"""
        response = self.client.get(
            f"/projects/{project_id}/boards?page=1&page_size=20",
            headers=self.headers,
            name="Startup: Discover boards"
        )
        
        if response.status_code == 200:
            items = response.json().get("items", [])
            self.boards[project_id] = [b["id"] for b in items]
            
            # Discover tasks from first board
            if self.boards[project_id]:
                board_id = self.boards[project_id][0]
                self._discover_tasks(project_id, board_id)
    
    def _discover_tasks(self, project_id, board_id):
        """Load tasks for a board"""
        response = self.client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks?page=1&page_size=50",
            headers=self.headers,
            name="Startup: Discover tasks"
        )
        
        if response.status_code == 200:
            items = response.json().get("items", [])
            self.tasks_id[board_id] = [t["id"] for t in items]
    
    # READ OPERATIONS

    
    @task(10)
    def list_projects(self):
        """View project list (most common action)"""
        params = {
            "page": random.randint(1, 2),
            "page_size": random.choice([10, 20]),
            "sort_by": random.choice(["name", "created_at"])
        }
        
        self.client.get(
            "/projects",
            params=params,
            headers=self.headers,
            name="Projects: List"
        )
    
    @task(8)
    def view_project_details(self):
        """View specific project"""
        if not self.projects:
            return
        
        project_id = random.choice(self.projects)
        self.client.get(
            f"/projects/{project_id}",
            headers=self.headers,
            name="Projects: View details"
        )
    
    @task(12)
    def list_boards(self):
        """View boards in project (very common)"""
        if not self.projects:
            return
        
        project_id = random.choice(self.projects)
        params = {
            "page": 1,
            "page_size": 20,
            "sort_by": random.choice(["position", "name"])
        }
        
        self.client.get(
            f"/projects/{project_id}/boards",
            params=params,
            headers=self.headers,
            name="Boards: List"
        )
    
    @task(15)
    def list_tasks(self):
        """View tasks in board (most common action)"""
        if not self.boards:
            return
        
        project_id = random.choice(list(self.boards.keys()))
        if not self.boards[project_id]:
            return
        
        board_id = random.choice(self.boards[project_id])
        
        filters = {
            "page": 1,
            "page_size": random.choice([20, 50]),
            "sort_by": random.choice(["position", "due_date", "priority"]),
            "sort_order": random.choice(["asc", "desc"])
        }
        
        if random.random() < 0.3:
            filters["status"] = random.choice(["active", "completed"])
        if random.random() < 0.2:
            filters["priority"] = random.choice(["high", "medium"])
        
        self.client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            params=filters,
            headers=self.headers,
            name="Tasks: List with filters"
        )
    
    @task(6)
    def view_task_details(self):
        """View specific task"""
        if not self.tasks_id:
            return
        
        board_id = random.choice(list(self.tasks_id.keys()))
        if not self.tasks_id[board_id]:
            return
        
        task_id = random.choice(self.tasks_id[board_id])
        
        # Find project_id
        project_id = self._find_project_for_board(board_id)
        if not project_id:
            return
        
        self.client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            headers=self.headers,
            name="Tasks: View details"
        )
    
    @task(4)
    def view_project_members(self):
        """View project team members"""
        if not self.projects:
            return
        
        project_id = random.choice(self.projects)
        self.client.get(
            f"/projects/{project_id}/members",
            headers=self.headers,
            name="Projects: View members"
        )

    # WRITE OPERATIONS
    
    
    @task(3)
    def create_project(self):
        """Create new project (occasional)"""
        response = self.client.post(
            "/projects",
            json={"name": f"Project {random.randint(1000, 9999)}"},
            headers=self.headers,
            name="Projects: Create"
        )
        
        if response.status_code == 201:
            project = response.json()
            self.projects.append(project["id"])
    
    @task(4)
    def create_board(self):
        """Create new board"""
        if not self.projects:
            return
        
        project_id = random.choice(self.projects)
        response = self.client.post(
            f"/projects/{project_id}/boards",
            json={"name": f"Board {random.randint(1000, 9999)}"},
            headers=self.headers,
            name="Boards: Create"
        )
        
        if response.status_code == 201:
            board = response.json()
            if project_id not in self.boards:
                self.boards[project_id] = []
            self.boards[project_id].append(board["id"])
    
    @task(6)
    def create_task(self):
        """Create new task"""
        if not self.boards:
            return
        
        project_id = random.choice(list(self.boards.keys()))
        if not self.boards[project_id]:
            return
        
        board_id = random.choice(self.boards[project_id])
        
        task_data = {
            "name": f"Task {random.randint(1000, 9999)}",
            "description": random.choice([
                "Fix bug in authentication flow",
                "Implement new feature X",
                "Review pull request",
                "Update documentation",
                "Refactor legacy code"
            ]),
            "priority": random.choice(["low", "medium", "high"]),
            "status": "active"
        }
        
        response = self.client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json=task_data,
            headers=self.headers,
            name="Tasks: Create"
        )
        
        if response.status_code == 201:
            task_data_response = response.json()
            if board_id not in self.tasks_id:
                self.tasks_id[board_id] = []
            self.tasks_id[board_id].append(task_data_response["id"])
    
    @task(5)
    def update_task(self):
        """Update task (common: marking complete, changing priority)"""
        if not self.tasks_id:
            return
        
        board_id = random.choice(list(self.tasks_id.keys()))
        if not self.tasks_id[board_id]:
            return
        
        task_id = random.choice(self.tasks_id[board_id])
        project_id = self._find_project_for_board(board_id)
        if not project_id:
            return
        
        # Realistic updates
        updates = random.choice([
            {"status": "completed"},
            {"priority": random.choice(["low", "medium", "high"])},
            {"name": f"Updated: {random.randint(1000, 9999)}"},
            {"status": "completed", "priority": "low"}
        ])
        
        self.client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            json=updates,
            headers=self.headers,
            name="Tasks: Update"
        )
    
    @task(2)
    def update_project(self):
        """Update project name"""
        if not self.projects:
            return
        
        project_id = random.choice(self.projects)
        self.client.patch(
            f"/projects/{project_id}",
            json={"name": f"Updated {random.randint(1000, 9999)}"},
            headers=self.headers,
            name="Projects: Update"
        )
    
    @task(2)
    def update_board(self):
        """Update board"""
        if not self.boards:
            return
        
        project_id = random.choice(list(self.boards.keys()))
        if not self.boards[project_id]:
            return
        
        board_id = random.choice(self.boards[project_id])
        
        self.client.patch(
            f"/projects/{project_id}/boards/{board_id}",
            json={"name": f"Updated Board {random.randint(1000, 9999)}"},
            headers=self.headers,
            name="Boards: Update"
        )
    
    # HELPER METHODS

    def _find_project_for_board(self, board_id):
        """Find project_id for a given board_id"""
        for pid, boards in self.boards.items():
            if board_id in boards:
                return pid
        return None