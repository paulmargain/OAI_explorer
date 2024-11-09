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
    pattern = f"{base_path}*_SAG_3D_DESS_LEFT"
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

def comp_viewer_page():
    st.title("3D Bone Viewer")

    if st.session_state.selected_id is None:
        st.warning("Please select an ID on the ID Selection page first.")
        return

    selected_id = st.session_state.selected_id

    # Time points
    time_points = ['00m', '12m', '24m', '48m', '72m']

    # Calculate separate vmin and vmax for tibia and femur across all time points
    thickness_data = {'femur': [], 'tibia': []}

    for time_point in time_points:
        base_path = os.path.join(st.session_state.data_path, 'DATA/processed_PP', time_point, f"{selected_id}_")
        try:
            full_path = find_file_path(base_path)
            for bone in ['femur', 'tibia']:
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

    # Create custom colormap
    thickness_cmap = create_custom_colormap()

    # Create a 3x2 grid for femur and tibia
    for bone in ['femur', 'tibia']:
        st.subheader(f"{bone.capitalize()} Visualization")
        
        # Create a 3x2 grid with black background
        grid = pv.Plotter(shape=(3, 2))
        grid.background_color = 'black'
        for i, time_point in enumerate(time_points):
            base_path = os.path.join(st.session_state.data_path, 'DATA/processed_PP', time_point, f"{selected_id}_")
            try:
                full_path = find_file_path(base_path)
                mesh, _ = load_and_process_mesh(
                   os.path.join(st.session_state.data_path, 'DATA', bone + '_ref_final.stl'),
                    os.path.join(full_path, os.path.basename(full_path) + '_' + bone + '_cartThickness.txt')
                )
    
                # Thickness plot
                row = i // 2
                col = i % 2

                grid.subplot(row, col)
                grid.add_mesh(mesh, scalars='thickness', cmap=thickness_cmap, clim=vmin_vmax[bone],
                              show_scalar_bar=True, nan_color='grey')
                grid.add_text(f"{time_point} - Thickness", position='upper_left', font_size=10, color='white')
                grid.view_isometric()
    
            except FileNotFoundError:
                st.error(f"No data found for ID {selected_id} at time point {time_point}")
                continue
        # Link the cameras across all subplots
        grid.link_views()
    
        # Display the grid
        stpyvista(grid, key=f"stl_viewer_grid_{bone}")

if __name__ == "__main__":
    comp_viewer_page()
