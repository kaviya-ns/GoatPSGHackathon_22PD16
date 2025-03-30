from enum import Enum, auto
from typing import List, Optional
from dataclasses import dataclass
import time

class RobotStatus(Enum):
    IDLE = auto()
    MOVING = auto()
    WAITING = auto()
    CHARGING = auto()
    TASK_COMPLETE = auto()

@dataclass
class Task:
    destination_id: int
    path: List[int]
    current_path_index: int = 0

class Robot:
    def __init__(self, robot_id: int, start_vertex_id: int):
        self.id = robot_id
        self.current_vertex_id = start_vertex_id
        self.status = RobotStatus.IDLE
        self.task: Optional[Task] = None
        self.color = self._generate_color(robot_id)
        self.log = []
        
    def _generate_color(self, robot_id: int) -> str:
        """Generate a unique color based on robot ID"""
        colors = [
            '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF',
            '#00FFFF', '#FFA500', '#A52A2A', '#800080', '#008000'
        ]
        return colors[robot_id % len(colors)]
    
    def assign_task(self, destination_id, path):
        """Assign a navigation task to this robot"""
        print(f"\n[ROBOT {self.id}] New task assigned:")
        print(f"Destination: {destination_id}")
        print(f"Full path: {path}")
        self.task = Task(destination_id, path)
        self.status = RobotStatus.MOVING
        self.log.append(f"Assigned task to {destination_id} via {path}")
        
    def update_position(self, new_vertex_id: int):
        self.current_vertex_id = new_vertex_id
        if self.task:
            self.task.current_path_index += 1
            if new_vertex_id == self.task.destination_id:
                self.status = RobotStatus.TASK_COMPLETE
                self.log.append(f"Robot {self.id} reached destination {new_vertex_id}")
    
    def set_waiting(self,reason: str = ""):
        """Set robot to waiting state with optional reason"""
        if self.status != RobotStatus.WAITING:
            self.status = RobotStatus.WAITING
            log_msg = f"Robot {self.id} waiting at {self.current_vertex_id}"
            if reason:
                log_msg += f" - {reason}"
            self.log.append(log_msg)
    
    def resume_moving(self):
        """Resume movement from waiting state"""
        if self.status == RobotStatus.WAITING:
            self.status = RobotStatus.MOVING
            self.log.append(f"Robot {self.id} resumed moving at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        return False
    
    def get_status_description(self) -> str:
        """Get human-readable status"""
        if self.status == RobotStatus.WAITING:
            next_vertex = self.get_next_vertex()
            return f"WAITING to move to {next_vertex}"
        return self.status.name
    
    def get_next_vertex(self) -> Optional[int]:
        """Get the next vertex in the robot's path"""
        if not self.task or self.task.current_path_index >= len(self.task.path) - 1:
            return None
        return self.task.path[self.task.current_path_index + 1]
    
    def get_current_lane(self) -> Optional[tuple[int, int]]:
        next_vertex = self.get_next_vertex()
        if next_vertex is not None:
            return (self.current_vertex_id, next_vertex)
        return None