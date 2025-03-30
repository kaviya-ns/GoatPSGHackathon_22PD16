import tkinter as tk
from tkinter import messagebox
import math
from src.models.nav_graph import NavigationGraph
from src.controllers.fleet_manager import FleetManager
from src.controllers.traffic_manager import TrafficManager
from src.models.robot import Robot, RobotStatus, Task

class FleetGUI(tk.Tk):
    def __init__(self, nav_graph_file: str, level: str = "level1"):
        super().__init__()
        self.title("Fleet Management System")
        self.geometry("1200x800")
        
        # Core system components
        self.nav_graph = NavigationGraph(nav_graph_file, level)
        self.fleet_manager = FleetManager(self.nav_graph)
        self.traffic_manager = TrafficManager(self.nav_graph)
        self.spawn_mode = False 
        self.traffic_manager.initialize_lane_queues()
        self.traffic_manager.initialize_occupancy_maps()

        # Visualization parameters - adjusted for the new graph coordinates
        self.scale_factor = 50
        self.offset_x = 200
        self.offset_y = 300
        
        # UI state
        self.selected_robot = None
        self.highlighted_vertex = None
        
        # Create UI
        self.create_widgets()
        self.draw_environment()
        
        # Setup simulation update
        self.after(1000, self.update_simulation)
    
    def enter_spawn_mode(self):
        """Enable spawn-only mode"""
        self.spawn_mode = True
        self.selected_robot = None
        self.status_var.set("SPAWN MODE: Click any vertex to spawn robot (Esc to cancel)")

    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for environment visualization with scrollbars
        self.canvas = tk.Canvas(main_frame, bg='white', scrollregion=(0, 0, 1200, 1200))
        
        # Add scrollbars
        hbar = tk.Scrollbar(main_frame, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        hbar.config(command=self.canvas.xview)
        vbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        vbar.config(command=self.canvas.yview)
        
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready. Click on a vertex to spawn a robot.")
        status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Control buttons frame
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Buttons
        clear_btn = tk.Button(control_frame, text="Clear Selection", command=self.clear_selection)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Zoom buttons
        zoom_in_btn = tk.Button(control_frame, text="Zoom In", command=lambda: self.zoom(1.2))
        zoom_in_btn.pack(side=tk.LEFT, padx=5)
        zoom_out_btn = tk.Button(control_frame, text="Zoom Out", command=lambda: self.zoom(0.8))
        zoom_out_btn.pack(side=tk.LEFT, padx=5)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # For Windows
        self.canvas.bind("<Button-4>", self.on_mousewheel)    # For Linux
        self.canvas.bind("<Button-5>", self.on_mousewheel)    # For Linux

         # Add spawn button
        spawn_btn = tk.Button(control_frame, 
                            text="Spawn Mode (S)", 
                            command=self.enter_spawn_mode)
        spawn_btn.pack(side=tk.LEFT, padx=5)
        
        # Add key bindings
        self.bind('<s>', lambda e: self.enter_spawn_mode())
        self.bind('<Escape>', lambda e: self.clear_selection())

    def handle_click(self, event):
        """Handle mouse clicks on the canvas"""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Check for clicks on robots first
        for robot in self.fleet_manager.get_all_robots():
            v = self.nav_graph.get_vertex_by_id(robot.current_vertex_id)
            rx = v.x * self.scale_factor + self.offset_x
            ry = -v.y * self.scale_factor + self.offset_y
            if (x-rx)**2 + (y-ry)**2 <= 100:  # Within click radius
                self.select_robot(robot.id)
                return
        
        # Then check for vertex clicks
        closest_vertex = None
        min_dist = float('inf')
        
        for vertex in self.nav_graph.vertices:
            vx = vertex.x * self.scale_factor + self.offset_x
            vy = -vertex.y * self.scale_factor + self.offset_y
            dist = (x-vx)**2 + (y-vy)**2
            
            if dist < 100 and dist < min_dist:  # Within click radius and closest
                min_dist = dist
                closest_vertex = vertex.id
        
        if closest_vertex is not None:
            self.handle_vertex_click(closest_vertex)
            
    def select_robot(self, robot_id):
        """Select a robot for task assignment"""
        self.spawn_mode = False  # Exit spawn mode if active
        self.selected_robot = self.fleet_manager.get_robot(robot_id)
        self.status_var.set(f"Selected Robot {robot_id} - Click destination vertex (Esc to cancel)")
        self.draw_environment()

    def handle_vertex_click(self, vertex_id):
        """Handle vertex click based on current state"""
        if self.spawn_mode:
            self.spawn_robot_at_vertex(vertex_id)
            self.spawn_mode = False
            self.status_var.set("Ready - Select a robot to assign task")
        elif self.selected_robot:
            self.assign_task_to_robot(vertex_id)
        else:
            # Regular click without selection - do nothing or show hint
            self.status_var.set("Hint: First select a robot or enable spawn mode")

    def assign_task_to_robot(self, destination_id):
        """Assign navigation task to selected robot"""
        if not self.selected_robot:
            messagebox.showwarning("No Selection", "No robot selected")
            return False
        
        try:
            start_id = self.selected_robot.current_vertex_id
            if start_id == destination_id:
                messagebox.showwarning("Invalid Task", "Robot is already at this vertex")
                return False
            
            # Get path from navigation graph
            path = self.nav_graph.find_shortest_path(start_id, destination_id)
            if not path:
                messagebox.showerror("No Path", f"No valid path from {start_id} to {destination_id}")
                return False
            
            # Assign task with path
            if self.fleet_manager.assign_navigation_task(
                robot_id=self.selected_robot.id,
                destination_id=destination_id,
                path=path
            ):
                self.status_var.set(f"Robot {self.selected_robot.id} moving to {destination_id}")
                self.visualize_path(path, self.selected_robot.color)
                return True
            else:
                messagebox.showerror("Assignment Failed", "Could not assign task")
                return False
                
        except Exception as e:
            messagebox.showerror("Error", f"Task assignment failed: {str(e)}")
            return False
        finally:
            self.selected_robot = None
            self.draw_environment()

    def spawn_robot_at_vertex(self, vertex_id):
        """Spawn new robot at vertex"""
        robot = self.fleet_manager.spawn_robot(vertex_id)
        vertex_name = self.nav_graph.get_vertex_by_id(vertex_id).name or f"Vertex {vertex_id}"
        self.status_var.set(f"Spawned Robot {robot.id} at {vertex_name}")
        self.draw_environment()

    def visualize_path(self, path, color):
        """Draw the planned path on canvas"""
        print(f"[VISUALIZING PATH] {path} in {color}")
        self.canvas.delete("path")
    
        for i in range(len(path)-1):
            v1 = self.nav_graph.get_vertex_by_id(path[i])
            v2 = self.nav_graph.get_vertex_by_id(path[i+1])
            x1 = v1.x * self.scale_factor + self.offset_x
            y1 = -v1.y * self.scale_factor + self.offset_y
            x2 = v2.x * self.scale_factor + self.offset_x
            y2 = -v2.y * self.scale_factor + self.offset_y
            
            # Thick path line
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=4,
                tags=("path", f"path_{path[i]}_{path[i+1]}")
            )
            
            # Arrowhead at end
            self.draw_arrow(x1, y1, x2, y2, color)

          
    def process_vertex_click(self, vertex_id):
        if self.selected_robot:
            start = self.selected_robot.current_vertex_id
            path = self.nav_graph.find_shortest_path(start, vertex_id)
            
            if not path:
                messagebox.showerror(
                    "No Path", 
                    f"No valid path from {start} to {vertex_id}"
                )
                return
                
            if self.fleet_manager.assign_navigation_task(
                self.selected_robot.id, vertex_id, path
            ):
                self.status_var.set(
                    f"Robot {self.selected_robot.id} path: {path}"
                )
                self.highlighted_vertex = None
                self.selected_robot = None
            else:
                messagebox.showwarning(
                    "Invalid Task", 
                    "Cannot assign this navigation task."
                )
        else:
            # Spawn new robot
            robot = self.fleet_manager.spawn_robot(vertex_id)
            self.status_var.set(
                f"Spawned Robot {robot.id} at {self.nav_graph.get_vertex_by_id(vertex_id).name or vertex_id}"
            )
        self.draw_environment()

    def clear_selection(self):
        """Reset all selections and modes"""
        self.selected_robot = None
        self.spawn_mode = False
        self.status_var.set("Selection cleared. Ready for commands")
        self.draw_environment() 

    def zoom(self, factor):
        self.scale_factor *= factor
        self.draw_environment()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_mousewheel(self, event):
        # Zoom with mouse wheel
        if event.num == 5 or event.delta < 0:
            self.zoom(0.9)
        elif event.num == 4 or event.delta > 0:
            self.zoom(1.1)
    
    def draw_environment(self):
        """Redraw the entire environment with error handling"""
        try:
            # Clear canvas safely
            self.canvas.delete("all")
            
            # Draw lanes
            for lane in self.nav_graph.lanes:
                try:
                    start = self.nav_graph.get_vertex_by_id(lane.start)
                    end = self.nav_graph.get_vertex_by_id(lane.end)
                    
                    x1 = start.x * self.scale_factor + self.offset_x
                    y1 = -start.y * self.scale_factor + self.offset_y
                    x2 = end.x * self.scale_factor + self.offset_x
                    y2 = -end.y * self.scale_factor + self.offset_y
                    
                    self.canvas.create_line(x1, y1, x2, y2, 
                                        fill="gray", width=2, tags="lane")
                except Exception as e:
                    print(f"Error drawing lane {lane.start}-{lane.end}: {e}")
            
            # Draw vertices
            for vertex in self.nav_graph.vertices:
                try:
                    x = vertex.x * self.scale_factor + self.offset_x
                    y = -vertex.y * self.scale_factor + self.offset_y
                    
                    color = "green" if vertex.is_charger else "white"
                    self.canvas.create_oval(
                        x-10, y-10, x+10, y+10,
                        fill=color, outline="black", width=2,
                        tags=f"vertex_{vertex.id}"
                    )
                    
                    if vertex.name:
                        self.canvas.create_text(
                            x, y-20,
                            text=vertex.name,
                            font=("Arial", 8),
                            tags=f"label_{vertex.id}"
                        )    
                except Exception as e:
                    print(f"Error drawing vertex {vertex.id}: {e}")

            for robot in self.fleet_manager.get_all_robots():
                vertex = self.nav_graph.get_vertex_by_id(robot.current_vertex_id)
                x = vertex.x * self.scale_factor + self.offset_x
                y = -vertex.y * self.scale_factor + self.offset_y
                
                # Draw robot with status-based appearance
                outline = "red" if robot.status == RobotStatus.WAITING else "black"
                width = 3 if robot.status == RobotStatus.WAITING else 2
                
                self.canvas.create_oval(
                    x-10, y-10, x+10, y+10,
                    fill=robot.color,
                    outline=outline,
                    width=width,
                    tags=f"robot_{robot.id}"
                )
                
                # Add status text below robot
                status_text = f"R{robot.id}: {robot.get_status_description()}"
                self.canvas.create_text(
                    x, y+25,
                    text=status_text,
                    font=("Arial", 7),
                    fill="black",
                    tags=f"robot_status_{robot.id}"
                )
            
        except Exception as e:
            print(f"Fatal error in draw_environment: {e}")
            self.status_var.set(f"Drawing error: {str(e)}")
        
    def draw_arrow(self, x1: float, y1: float, x2: float, y2: float, color: str):
            """Draw an arrowhead at the end of a lane"""
            arrow_size = 10
            angle = math.atan2(y1 - y2, x2 - x1)
            
            p1_x = x2 - math.cos(angle + math.pi/6) * arrow_size
            p1_y = y2 + math.sin(angle + math.pi/6) * arrow_size
            p2_x = x2 - math.cos(angle - math.pi/6) * arrow_size
            p2_y = y2 + math.sin(angle - math.pi/6) * arrow_size
            
            self.canvas.create_polygon(
                x2, y2,
                p1_x, p1_y,
                p2_x, p2_y,
                fill=color,
                outline=color,
                tags="arrow"
            )
    def is_dark_color(self, hex_color: str) -> bool:
        """Determine if a color is dark for text contrast"""
        if not hex_color.startswith('#'):
            return False
        # Convert hex to RGB
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        # Calculate luminance
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    
    def show_occupancy_warning(self, robot_id: int, blocked_vertex: int):
        """Show visual warning about occupancy conflict"""
        robot = self.fleet_manager.get_robot(robot_id)
        if not robot:
            return
            
        vertex = self.nav_graph.get_vertex_by_id(blocked_vertex)
        if not vertex:
            return

        # Visual indicator on the vertex
        x = vertex.x * self.scale_factor + self.offset_x
        y = -vertex.y * self.scale_factor + self.offset_y
        
        # Draw warning circle
        self.canvas.create_oval(
            x-15, y-15, x+15, y+15,
            outline="red", width=3, dash=(5,2),
            tags="occupancy_warning"
        )
        
        # Get blocking robot ID
        blocking_robot_id = self.traffic_manager.vertex_occupancy.get(blocked_vertex)
        
        # Status message
        if blocking_robot_id:
            msg = f"Robot {robot_id} waiting - Vertex {blocked_vertex} occupied by Robot {blocking_robot_id}"
        else:
            msg = f"Robot {robot_id} waiting - Vertex {blocked_vertex} is blocked"
        
        self.status_var.set(msg)
        
        # Flash the warning for 2 seconds
        self.after(2000, lambda: self.canvas.delete("occupancy_warning"))

    def update_simulation(self):
        try:
            # Update traffic manager first
            self.traffic_manager.manage_traffic(self.fleet_manager)
            
            # Process each robot
            for robot in self.fleet_manager.get_all_robots():
                if robot.status == RobotStatus.MOVING:
                    next_vertex = robot.get_next_vertex()
                    if next_vertex is None:
                        continue  # Robot has reached destination
                        
                    if self.traffic_manager.check_collision(robot.id, next_vertex):
                        robot.set_waiting()
                        self.show_occupancy_warning(robot.id, next_vertex)
                    else:
                        # Only update position if no collision
                        self.fleet_manager.update_robot_position(robot.id)
            
            # Redraw environment
            self.draw_environment()
            self.after(200, self.update_simulation)
            
        except Exception as e:
            print(f"Simulation error: {e}")
            self.status_var.set(f"Simulation error: {str(e)}")