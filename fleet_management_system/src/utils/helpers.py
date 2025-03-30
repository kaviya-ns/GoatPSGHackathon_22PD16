from typing import List, Optional
from ..models.nav_graph import NavigationGraph

def validate_nav_graph(nav_graph: NavigationGraph) -> bool:
    """Validate the navigation graph structure"""
    if not nav_graph.vertices:
        return False
    
    # Check that all lane references are valid vertices
    vertex_ids = {v.id for v in nav_graph.vertices}
    for lane in nav_graph.lanes:
        if lane.start not in vertex_ids or lane.end not in vertex_ids:
            return False
    
    return True

def calculate_distance(v1: tuple, v2: tuple) -> float:
    """Calculate Euclidean distance between two points"""
    return ((v1[0] - v2[0])**2 + (v1[1] - v2[1])**2)**0.5