class Agent:
    def __init__(self):
        self.memory = {}
        self.status = "idle"

    def execute_task(self, task):
        # Logic to execute the task
        self.status = "busy"
        # Simulate task execution
        # Update memory or status as needed
        self.status = "idle"

    def update_memory(self, key, value):
        self.memory[key] = value

    def get_status(self):
        return self.status

    def shutdown(self):
        self.status = "shutting down"
        # Logic to safely shutdown the agent
        self.status = "shutdown"