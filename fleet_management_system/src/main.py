import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sys
from src.gui.fleet_gui import FleetGUI
import argparse

def main():
    parser = argparse.ArgumentParser(description='Fleet Management System')
    parser.add_argument('--graph', default='data/nav_graph.json', help='Path to navigation graph JSON file')
    parser.add_argument('--level', default='level1', help='Level to load from the navigation graph')
    args = parser.parse_args()
    
    try:
        app = FleetGUI(args.graph, args.level)
        app.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()