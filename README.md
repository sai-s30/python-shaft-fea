# python-shaft-fea
A desktop application built with Python (Tkinter, NumPy, PyVista) and Gmsh for performing Finite Element Analysis on cylindrical shafts, allowing users to define geometry, materials, apply axial, bending (at specific points), and torsional loads, and visualize stress and deformation.

# Shaft FEA Simulator

A simple Finite Element Analysis (FEA) application built with Python and Gmsh for simulating stress and displacement in a cylindrical shaft under various loading conditions (axial, bending, torsion).

## Features

* **Interactive GUI:** User-friendly interface built with `tkinter` for inputting shaft dimensions, material properties, and load parameters.
* **Customizable Meshing:** Control mesh density directly from the GUI to balance accuracy and computational cost.
* **Multiple Load Types:** Supports axial, bending, and torsional loads, as well as combinations.
* **Bending Load Position:** Specify the exact (X, Y) location on the top face where the bending force is applied.
* **3D Visualization:** Utilizes `PyVista` to visualize the deformed shaft and Von Mises stress distribution.
* **Animation:** Play an animation of the shaft's deformation.

## How it Works

This application follows a standard FEA workflow:

1.  **Pre-processing:**
    * User inputs parameters via GUI.
    * `generate_mesh.py` creates the 3D tetrahedral mesh of the shaft geometry using `Gmsh` based on user-defined element size.
2.  **Solver:**
    * `fea_solver.py` orchestrates the FEA process.
    * `material.py` defines the material's elasticity matrix.
    * `fea_math.py` handles the assembly of the global stiffness matrix, application of boundary conditions (fixed at one end), and calculation of Von Mises stress.
    * External loads (axial, bending, torsion) are applied to the top face nodes.
    * The system of linear equations is solved to obtain nodal displacements.
3.  **Post-processing:**
    * Results (deformed shape, displacement, Von Mises stress) are saved to a VTK file.
    * `main.py` uses `PyVista` to visualize these results in a 3D plot and provides a deformation animation.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YourUsername/Shaft-FEA-Simulator.git](https://github.com/YourUsername/Shaft-FEA-Simulator.git)
    cd Shaft-FEA-Simulator
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    # On Windows:
    .venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Install Gmsh:**
    This application requires the `gmsh` executable to be installed and accessible in your system's PATH.
    * Download Gmsh from their official website: [https://gmsh.info/#Download](https://gmsh.info/#Download)
    * Follow the installation instructions for your operating system.
    * Verify installation by opening your terminal/command prompt and typing `gmsh -version`.

## Usage

1.  **Run the application:**
    ```bash
    python main.py
    ```
2.  **Input Parameters:**
    * Enter shaft dimensions, material properties.
    * Specify "Mesh Element Size". Smaller values lead to finer meshes and higher accuracy (but longer computation).
    * Select "Load Type" and enter load values.
    * For "bending" loads, specify "Bending X-pos (m)" and "Bending Y-pos (m)" relative to the center of the top face.
3.  **Run FEA:** Click the "Run FEA" button.
4.  **Visualize Results:** Click "Visualize Results" to see the deformed shaft and stress distribution.
5.  **Animate Deformation:** Click "Play Animation" for a step-by-step visualization of the deformation.

## Project Structure
