#!/usr/bin/env python3
"""
Script to load and visualize a STEP file using occ-python (Open CASCADE Python bindings)
"""

import sys
import os
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Display.SimpleGui import init_display

def load_step_file(filename):
    """Load a STEP file and return the shape"""
    # Create a STEP reader
    step_reader = STEPControl_Reader()

    # Read the STEP file
    status = step_reader.ReadFile(filename)

    if status != IFSelect_RetDone:
        raise Exception(f"Error reading STEP file: {filename}")

    # Transfer the data to a shape
    step_reader.TransferRoot()
    shape = step_reader.Shape()

    return shape

def main():
    # Path to the STEP file (assuming it's in the same directory as this script)
    step_file = os.path.join(os.path.dirname(__file__), "block_with_holes.step")

    if not os.path.exists(step_file):
        print(f"STEP file not found: {step_file}")
        print("Please ensure the STEP file exists in the same directory as this script.")
        sys.exit(1)

    try:
        # Load the STEP file
        print(f"Loading STEP file: {step_file}")
        shape = load_step_file(step_file)
        print("STEP file loaded successfully!")

        # Initialize the 3D display
        display, start_display, add_menu, add_function_to_menu = init_display()

        # Display the shape
        display.DisplayShape(shape, update=True)

        # Set up the viewer
        display.FitAll()
        display.View_Iso()

        # Start the display loop
        start_display()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()