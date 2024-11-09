import streamlit as st
import pyvista as pv
from stpyvista import stpyvista
import numpy as np

# Set up PyVista for off-screen rendering
pv.OFF_SCREEN = True
pv.global_theme.background = 'white'
pv.global_theme.window_size = [800, 600]
pv.global_theme.smooth_shading = True
pv.global_theme.camera['viewup'] = [0.5, 0.5, 1]
pv.global_theme.camera['position'] = [1, 1, 1]

def load_scalar_from_file(file_path):
    with open(file_path, 'r') as file:
        scalars = [float(line.strip()) for line in file]
    return np.array(scalars)

def main():
    st.set_page_config(page_title='3D Bone Viewer', layout="wide")
    st.title("3D Bone Viewer with PBR")

    # File paths
    stl_path = "/Volumes/T7/DATA/DATA_12m/9003126_20060727_SAG_3D_DESS_LEFT/9003126_20060727_SAG_3D_DESS_LEFT_femur_ref.stl"
    scalar_path = "/Volumes/T7/DATA/DATA_12m/9003126_20060727_SAG_3D_DESS_LEFT/9003126_20060727_SAG_3D_DESS_LEFT_femur_cartThickness.txt"

    # Read the STL file
    mesh = pv.read(stl_path)

    # Load scalars from the text file
    scalars = load_scalar_from_file(scalar_path)

    # Ensure the number of scalars matches the number of points in the mesh
    if len(scalars) != mesh.n_points:
        st.error(f"Number of scalars ({len(scalars)}) does not match number of vertices in the mesh ({mesh.n_points})")
        return

    # Add scalars to the mesh
    mesh.point_data['scalars'] = scalars

    # Create a plotter
    plotter = pv.Plotter(off_screen=True)

    # Add mesh to the plotter with PBR and jet colormap
    plotter.add_mesh(
        mesh,
        scalars='scalars',
        cmap='jet',
        show_edges=False,
        pbr=True,
        metallic=0.1,
        roughness=0.6,
        diffuse=1.0,
    )

    # Add a colorbar
    plotter.add_scalar_bar('Scalar Values', vertical=True, position_x=0.05, position_y=0.05)

    # Set up the camera
    plotter.camera_position = 'iso'
    plotter.camera.zoom(0.8)

    # Display the plot using stpyvista
    stpyvista(plotter, key="pv_stl")

if __name__ == "__main__":
    main()