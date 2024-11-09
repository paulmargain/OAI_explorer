import streamlit as st
import os
import pyvista as pv
from stpyvista import stpyvista
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import glob

def load_and_process_mesh(stl_path, thickness_path):
    mesh = pv.read(stl_path)
    thickness_data = pd.read_csv(thickness_path, header=None, names=['thickness'])
    mesh.point_data['thickness'] = thickness_data['thickness'].values
    return mesh, thickness_data['thickness']

def find_file_path(base_path):
    pattern = os.path.join(base_path, "*_SAG_3D_DESS_LEFT")
    matching_files = glob.glob(pattern)
    if matching_files:
        return matching_files[0]
    else:
        raise FileNotFoundError(f"No matching file found for pattern: {pattern}")

def create_custom_colormap():
    n_bins = 256
    colors = plt.cm.jet(np.linspace(0, 1, n_bins))[::-1]  # Reverse the colors
    colors[0] = [0.5, 0.5, 0.5, 1.0]  # Set the first color to grey for NaN values
    return ListedColormap(colors)

def stl_viewer_page():
    st.title("3D Bone Viewer")

    if st.session_state.selected_id is None:
        st.warning("Please select an ID on the ID Selection page first.")
        return

    selected_id = st.session_state.selected_id
    # Time point selection
    time_points = ['00m', '12m', '24m', '48m', '72m']
    selected_time_point = st.selectbox("Select Time Point", time_points)
    # Calculate separate vmin and vmax for tibia and femur across all time points
    thickness_data = {'femur': [], 'tibia': []}
    for time_point in time_points:
        base_folder = os.path.join(st.session_state.data_path, 
                                  'DATA/processed_PP', 
                                  time_point)
        try:
            full_path = find_file_path(base_folder)
            print(full_path)
            for bone in ['femur', 'tibia']:
                print(os.path.join(full_path, os.path.basename(full_path) + '_' + bone + '_cartThickness.txt'))
                _, thickness = load_and_process_mesh(
                    os.path.join(st.session_state.data_path, 'DATA', bone + '_ref_final.stl'),
                    os.path.join(full_path, os.path.basename(full_path) + '_' + bone + '_cartThickness.txt')
                )
                thickness_data[bone].append(thickness)
        except FileNotFoundError:
            st.warning(f"No data found for ID {selected_id} at time point {time_point}")

    vmin_vmax = {}
    for bone in ['femur', 'tibia']:
       
        all_thickness = np.concatenate(thickness_data[bone])
        vmin_vmax[bone] = (np.nanmin(all_thickness), np.nanmax(all_thickness))

    # Create separate plots for femur and tibia
    for bone in ['femur', 'tibia']:
        st.subheader(f"{bone.capitalize()} Visualization")

        # Create custom colormap
        thickness_cmap = create_custom_colormap()

        base_folder = os.path.join(st.session_state.data_path, 
                                  'DATA/processed_PP', 
                                  selected_time_point)
        try:
            full_path = find_file_path(base_folder)
            mesh, _ = load_and_process_mesh(
                os.path.join(st.session_state.data_path, 'DATA', bone + '_ref_final.stl'),
                os.path.join(full_path, os.path.basename(full_path) + '_' + bone + '_cartThickness.txt')
            )

            # Thickness plot
            plotter_thickness = pv.Plotter()
            plotter_thickness.background_color = 'black'
            plotter_thickness.add_mesh(mesh, scalars='thickness', cmap=thickness_cmap, clim=vmin_vmax[bone],
                                       show_scalar_bar=True, nan_color='grey')
            plotter_thickness.add_text(f"{selected_time_point} - Thickness", position='upper_left', font_size=10, color='white')
            plotter_thickness.view_isometric()
            stpyvista(plotter_thickness, key=f"stl_viewer_thickness_{bone}_{selected_time_point}")

        except FileNotFoundError:
            st.error(f"No data found for ID {selected_id} at time point {selected_time_point}")
            continue

if __name__ == "__main__":
    stl_viewer_page()
