from typing import Dict, List, Optional
from ..models.robot import Robot
from ..models.nav_graph import NavigationGraph
import time
from ..utils.logger import FleetLogger
from ..models.robot import Robot, RobotStatus, Task

class FleetManager:
    def __init__(self, nav_graph: NavigationGraph):
        self.nav_graph = nav_graph
        self.robots: Dict[int, Robot] = {}
        self.next_robot_id = 0
        self.logger = FleetLogger()
    
    def spawn_robot(self, vertex_id: int) -> Robot:
        robot = Robot(self.next_robot_id, vertex_id)
        self.robots[self.next_robot_id] = robot
        self.next_robot_id += 1
        self.logger.log(f"Spawned robot {robot.id} at vertex {vertex_id}")
        return robot
    
    def assign_navigation_task(self, robot_id: int, destination_id: int, path: List[int]) -> bool:
        """Assign navigation task to robot with provided path"""
        robot = self.get_robot(robot_id)
        if not robot:
            return False
        
        try:
            robot.assign_task(destination_id, path)
            self.logger.log(f"Assigned robot {robot_id} path: {path}")
            return True
        except Exception as e:
            self.logger.log(f"Task assignment failed for robot {robot_id}: {str(e)}")
            return False
    
    def get_robot(self, robot_id: int) -> Optional[Robot]:
        return self.robots.get(robot_id)
    
    def get_all_robots(self) -> List[Robot]:
        return list(self.robots.values())
    
    def update_robot_position(self, robot_id: int) -> bool:
        """Update a robot's position along its path"""
        robot = self.get_robot(robot_id)
        if not robot or not robot.task:
            return False

        next_vertex = robot.get_next_vertex()
        if next_vertex is None:
            robot.status = RobotStatus.TASK_COMPLETE
            self.logger.log(f"Robot {robot_id} reached destination")
            return False

        # Update the robot's position
        robot.current_vertex_id = next_vertex
        robot.task.current_path_index += 1

        self.logger.log(f"Robot {robot_id} moved to vertex {next_vertex}")
        return True