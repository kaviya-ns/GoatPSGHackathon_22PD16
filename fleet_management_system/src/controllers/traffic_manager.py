from typing import Dict, List, Optional, Set, Tuple
from ..models.nav_graph import NavigationGraph, Lane
from ..models.robot import Robot,RobotStatus
from ..utils.logger import FleetLogger
from queue import Queue

class TrafficManager:
    def __init__(self, nav_graph: NavigationGraph):
        self.nav_graph = nav_graph
        self.lane_queues: Dict[Tuple[int, int], Queue[int]] = {}  # (v1, v2) -> queue of robot IDs
        self.occupied_vertices: Set[int] = set()
        self.logger = FleetLogger()

    def initialize_occupancy_maps(self):
        """Initialize occupancy tracking for all vertices and lanes"""
        self.vertex_occupancy = {v.id: None for v in self.nav_graph.vertices}
        self.lane_occupancy = {}

    def initialize_lane_queues(self):
        """Initialize queues for all lanes"""
        for lane in self.nav_graph.lanes:
            key = self._get_lane_key(lane.start, lane.end)
            self.lane_queues[key] = Queue()
    
    def _get_lane_key(self, v1: int, v2: int) -> Tuple[int, int]:
        """Get consistent key for a lane regardless of vertex order"""
        return (min(v1, v2), max(v1, v2))
    
    def request_lane_access(self, robot: Robot, next_vertex_id: int) -> bool:
        """Request access to a lane, returns True if granted"""
        current_vertex = robot.current_vertex_id
        lane_key = self._get_lane_key(current_vertex, next_vertex_id)
        
        if lane_key not in self.lane_queues:
            self.lane_queues[lane_key] = Queue()
        
        # Check if lane is available
        if self.lane_queues[lane_key].empty() and next_vertex_id not in self.occupied_vertices:
            self.lane_queues[lane_key].put(robot.id)
            self.occupied_vertices.add(next_vertex_id)
            self.logger.log(f"Robot {robot.id} granted access to lane {current_vertex}-{next_vertex_id}")
            return True
        else:
            robot.set_waiting()
            self.lane_queues[lane_key].put(robot.id)
            self.logger.log(f"Robot {robot.id} queued for lane {current_vertex}-{next_vertex_id}")
            return False
    
    def release_lane(self, robot: Robot, next_vertex_id: int):
        """Release lane after crossing"""
        current_vertex = robot.current_vertex_id
        lane_key = self._get_lane_key(current_vertex, next_vertex_id)
        
        if lane_key in self.lane_queues and not self.lane_queues[lane_key].empty():
            # Check if this robot is at the front of the queue
            if self.lane_queues[lane_key].queue[0] == robot.id:
                self.lane_queues[lane_key].get()
                self.occupied_vertices.discard(next_vertex_id)
                self.logger.log(f"Robot {robot.id} released lane {current_vertex}-{next_vertex_id}")
                
                # Notify next robot in queue
                if not self.lane_queues[lane_key].empty():
                    next_robot_id = self.lane_queues[lane_key].queue[0]
                    self.logger.log(f"Robot {next_robot_id} can now proceed on lane {current_vertex}-{next_vertex_id}")
                    return next_robot_id
        return None
    
    def check_collision(self, robot_id: int, next_vertex: int) -> bool:
        """
        Check if moving to next_vertex would cause a collision
        Returns True if collision would occur, False otherwise
        """
        robot = self.fleet_manager.get_robot(robot_id)
        if not robot:
            return False
            
        current_vertex = robot.current_vertex_id
        
        # Check if target vertex is occupied by another robot
        if next_vertex in self.vertex_occupancy and self.vertex_occupancy[next_vertex] not in [None, robot_id]:
            return True
            
        # Check if lane is occupied (bidirectional check)
        lane1 = (current_vertex, next_vertex)
        lane2 = (next_vertex, current_vertex)
        
        if (lane1 in self.lane_occupancy and self.lane_occupancy[lane1] not in [None, robot_id]) or \
           (lane2 in self.lane_occupancy and self.lane_occupancy[lane2] not in [None, robot_id]):
            return True
            
        return False

    def manage_traffic(self,fleet_manager):
        """Update occupancy maps and manage robot movements"""
        self.fleet_manager = fleet_manager  # Store reference to fleet manager
        robots = fleet_manager.get_all_robots()
        self.initialize_occupancy_maps()
        
        for robot in fleet_manager.get_all_robots():
            self.vertex_occupancy[robot.current_vertex_id] = robot.id
            
        # Process waiting robots first
        for robot in [r for r in fleet_manager.get_all_robots() if r.status == RobotStatus.WAITING]:
            next_vertex = robot.get_next_vertex()
            if next_vertex and not self.check_collision(robot.id, next_vertex):
                robot.resume_moving()
                
        # Then process moving robots
        for robot in [r for r in fleet_manager.get_all_robots() if r.status == RobotStatus.MOVING]:
            next_vertex = robot.get_next_vertex()
            if next_vertex:
                lane = (robot.current_vertex_id, next_vertex)
                self.lane_occupancy[lane] = robot.id