import streamlit as st
import os
import pyvista as pv
from stpyvista import stpyvista
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import glob

def load_and_process_mesh(stl_path, thickness_path, t2_path=None):
    mesh = pv.read(stl_path)
    thickness_data = pd.read_csv(thickness_path, header=None, names=['thickness'])
    mesh.point_data['thickness'] = thickness_data['thickness'].values
    if t2_path and os.path.exists(t2_path):
        t2_data = pd.read_csv(t2_path, header=None, names=['t2'])
        mesh.point_data['t2'] = t2_data['t2'].values
        return mesh, thickness_data['thickness'], t2_data['t2']
    return mesh, thickness_data['thickness'], None

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
    t2_data = {'femur': [], 'tibia': []}

    for time_point in time_points:
        base_path = f'/media/chuv/T7/DATA/processed_PP/{time_point}/{selected_id}_'
        try:
            full_path = find_file_path(base_path)
            for bone in ['femur', 'tibia']:
                t2_path = f'{full_path}/{os.path.basename(full_path)}_{bone}_t2_map.txt'
                _, thickness, t2 = load_and_process_mesh(
                    f'{full_path}/{os.path.basename(full_path)}_{bone}_ref.stl',
                    f'{full_path}/{os.path.basename(full_path)}_{bone}_cartThickness.txt',
                    t2_path
                )
                thickness_data[bone].append(thickness)
                if t2 is not None:
                    t2_data[bone].append(t2)
        except FileNotFoundError:
            st.warning(f"No data found for ID {selected_id} at time point {time_point}")

    vmin_vmax = {}
    t2_vmin_vmax = {}
    for bone in ['femur', 'tibia']:
        all_thickness = np.concatenate(thickness_data[bone])
        vmin_vmax[bone] = (np.nanmin(all_thickness), np.nanmax(all_thickness))
        if t2_data[bone]:
            all_t2 = np.concatenate(t2_data[bone])
            t2_vmin_vmax[bone] = (np.nanmin(all_t2), np.nanmax(all_t2))

    # Create custom colormaps
    thickness_cmap = create_custom_colormap()
    t2_cmap = create_custom_colormap()

       # Create a 3x2 grid for femur and tibia
    for bone in ['femur', 'tibia']:
        st.subheader(f"{bone.capitalize()} Visualization")
        
        # Create a 3x2 grid
        grid = pv.Plotter(shape=(3, 2)) 
    
        for i, time_point in enumerate(time_points):
            base_path = f'/media/chuv/T7/DATA/processed_PP/{time_point}/{selected_id}_'
            try:
                full_path = find_file_path(base_path)
                t2_path = f'{full_path}/{os.path.basename(full_path)}_{bone}_t2_map.txt'
                mesh, _, t2 = load_and_process_mesh(
                    f'{full_path}/{os.path.basename(full_path)}_{bone}_ref.stl',
                    f'{full_path}/{os.path.basename(full_path)}_{bone}_cartThickness.txt',
                    t2_path
                )
    
                # Thickness plot
                row = i // 2
                col = i % 2
                print(row)
                print(col)
                grid.subplot(row, col)
                grid.add_mesh(mesh, scalars='thickness', cmap=thickness_cmap, clim=vmin_vmax[bone],
                              show_scalar_bar=True, nan_color='grey')
                grid.add_text(f"{time_point} - Thickness", position='upper_left', font_size=10)
                grid.view_isometric()
    
            except FileNotFoundError:
                st.error(f"No data found for ID {selected_id} at time point {time_point}")
                continue
                # Link the cameras across all subplots
        grid.link_views()
    
        # Display the grid
        stpyvista(grid, key=f"stl_viewer_grid_{bone}")

               # T2 map visualization (if available)
        if t2_data[bone]:
            st.subheader(f"{bone.capitalize()} T2 Map Visualization")
            
            grid_t2 = pv.Plotter(shape=(3, 2))
        
            for i, time_point in enumerate(time_points):
                base_path = f'/media/chuv/T7/DATA/processed_PP/{time_point}/{selected_id}_'
                try:
                    full_path = find_file_path(base_path)
                    t2_path = f'{full_path}/{os.path.basename(full_path)}_{bone}_t2_map.txt'
                    mesh, _, t2 = load_and_process_mesh(
                        f'{full_path}/{os.path.basename(full_path)}_{bone}_ref.stl',
                        f'{full_path}/{os.path.basename(full_path)}_{bone}_cartThickness.txt',
                        t2_path
                    )
        
                    if t2 is not None:
                        row = i // 2
                        col = i % 2
                        grid_t2.subplot(row, col)
                        grid_t2.add_mesh(mesh, scalars='t2', cmap=t2_cmap, clim=t2_vmin_vmax[bone],
                                         show_scalar_bar=True, nan_color='grey')
                        grid_t2.add_text(f"{time_point} - T2 Map", position='upper_left', font_size=10)
                        grid_t2.view_isometric()
                    else:
                        st.info(f"No T2 map data available for {bone} at {time_point}")
        
                except FileNotFoundError:
                    st.error(f"No data found for ID {selected_id} at time point {time_point}")
                    continue
                    # Link the cameras across all subplots
            grid_t2.link_views()
        
            # Display the T2 grid
            stpyvista(grid_t2, key=f"stl_viewer_grid_t2_{bone}")
        else:
            st.info(f"No T2 map data available for {bone}")


if __name__ == "__main__":
    stl_viewer_page()