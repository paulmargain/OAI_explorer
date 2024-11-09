import streamlit as st
import os
import pyvista as pv
from stpyvista import stpyvista

def load_and_plot_stl(plotter, file_path, color):
    mesh = pv.read(file_path)
    plotter.add_mesh(mesh, color=color, opacity=0.7)

def stl_viewer_page():
    st.title("3D Bone Viewer")

    if st.session_state.selected_id is None:
        st.warning("Please select an ID on the ID Selection page first.")
        return

    selected_id = st.session_state.selected_id

    # Time point selection
    time_points = ['00m', '12m', '24m', '48m', '72m']
    selected_time_point = st.selectbox("Select Time Point", time_points)

    # Bone selection
    bone_options = ['Femur', 'Tibia']
    selected_bone = st.selectbox("Select Bone", bone_options)

    # Construct file paths
    base_folder = f"/media/chuv/T7/DATA/processed_PP/{selected_time_point}"
    
    # Find the folder for the selected ID
    id_folder = next((f for f in os.listdir(base_folder) if f.startswith(f"{selected_id}_") and f.endswith("_SAG_3D_DESS_LEFT")), None)

    if id_folder:
        folder_path = os.path.join(base_folder, id_folder)
        
        # Construct file paths for the selected bone
        ref_registered_file = os.path.join(folder_path, f"{id_folder}_{selected_bone.lower()}_ref_registered.stl")
        bone_file = os.path.join(folder_path, f"{id_folder}_{selected_bone.lower()}_bone.stl")

        if os.path.exists(ref_registered_file) and os.path.exists(bone_file):
            # Create a PyVista plotter
            plotter = pv.Plotter()

            # Load and plot the ref_registered STL in red
            load_and_plot_stl(plotter, ref_registered_file, 'red')

            # Load and plot the bone STL in blue
            load_and_plot_stl(plotter, bone_file, 'blue')


            
            # Set up the camera
            plotter.camera_position = 'xy'
            plotter.camera.zoom(1.5)

            # Render the plot in Streamlit
            stpyvista(plotter, key="stl_viewer")
        else:
            st.error(f"STL files not found for {selected_bone} at time point {selected_time_point}")
    else:
        st.error(f"No folder found for ID {selected_id} at time point {selected_time_point}")

if __name__ == "__main__":
    stl_viewer_page()