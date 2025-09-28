from dataclasses import dataclass, field
from typing import List, Optional

dataclass
class Task:
    id: int
    name: str
    status: str = field(default='pending')

class TaskQueue:
    def __init__(self):
        self.tasks: List[Task] = []
        self.next_id = 1

    def add_task(self, name: str) -> Task:
        task = Task(id=self.next_id, name=name)
        self.tasks.append(task)
        self.next_id += 1
        return task

    def get_next_task(self) -> Optional[Task]:
        for task in self.tasks:
            if task.status == 'pending':
                return task
        return None

    def update_task_status(self, task_id: int, status: str) -> bool:
        for task in self.tasks:
            if task.id == task_id:
                task.status = status
                return True
        return False

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def view_queue(self) -> List[Task]:
        return self.tasks