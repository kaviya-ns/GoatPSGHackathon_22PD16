import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Vertex:
    id: int
    x: float
    y: float
    name: str
    is_charger: bool = False

@dataclass
class Lane:
    start: int
    end: int
    speed_limit: int
    occupied_by: Optional[int] = None  # Robot ID if occupied

class NavigationGraph:
    def __init__(self, json_file: str, level: str = "level1"):
        self.vertices: List[Vertex] = []
        self.lanes: List[Lane] = []
        self.level = level
        self.load_from_json(json_file)
        
    def load_from_json(self, json_file: str):
        with open(json_file, 'r') as f:
            data = json.load(f)
            level_data = data['levels'][self.level]
            
            # Load vertices
            for idx, vertex_data in enumerate(level_data['vertices']):
                x, y, attributes = vertex_data
                name = attributes.get('name', f'V{idx}')
                is_charger = attributes.get('is_charger', False)
                self.vertices.append(Vertex(idx, x, y, name, is_charger))
            
            # Load lanes
            for lane_data in level_data['lanes']:
                start, end, attributes = lane_data
                speed_limit = attributes.get('speed_limit', 0)
                self.lanes.append(Lane(start, end, speed_limit))
    
    def get_vertex_by_id(self, vertex_id: int) -> Vertex:
        return self.vertices[vertex_id]
    
    def get_adjacent_vertices(self, vertex_id: int) -> List[Vertex]:
        adjacent = []
        for lane in self.lanes:
            if lane.start == vertex_id:
                adjacent.append(self.vertices[lane.end])
            elif lane.end == vertex_id:
                adjacent.append(self.vertices[lane.start])
        return adjacent
    
    def get_lane_between(self, v1_id: int, v2_id: int) -> Optional[Lane]:
        for lane in self.lanes:
            if (lane.start == v1_id and lane.end == v2_id) or (lane.start == v2_id and lane.end == v1_id):
                return lane
        return None
    
    def find_shortest_path(self, start_id: int, end_id: int) -> List[int]:
        """Find shortest path using Dijkstra's algorithm with fixed weights"""
        # Initialize data structures
        distances = {vertex.id: float('inf') for vertex in self.vertices}
        previous = {vertex.id: None for vertex in self.vertices}
        distances[start_id] = 0
        unvisited = set(vertex.id for vertex in self.vertices)
        
        while unvisited:
            current = min(unvisited, key=lambda v: distances[v])
            unvisited.remove(current)
            
            # Early exit if we reach the destination
            if current == end_id:
                break
                
            # Explore neighbors
            for neighbor in self.get_adjacent_vertices(current):
                if neighbor.id in unvisited:
                    # Fixed weight - treat all edges equally since speed limits are 0
                    weight = 1  # Constant weight for all edges
                    new_distance = distances[current] + weight
                    
                    if new_distance < distances[neighbor.id]:
                        distances[neighbor.id] = new_distance
                        previous[neighbor.id] = current
        
        # Reconstruct path if one exists
        path = []
        current = end_id
        
        if previous[current] is None and current != start_id:
            return path  # No path exists
        
        while current is not None:
            path.insert(0, current)
            current = previous[current]
        
        return path