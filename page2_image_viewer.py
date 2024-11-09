import streamlit as st
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import nibabel as nib
import base64
from io import BytesIO

def load_nifti_file(filepath):
    nifti_img = nib.load(filepath)
    image_np = np.asanyarray(nifti_img.dataobj)
    spacing = nifti_img.header.get_zooms()[:3]
    return image_np, spacing

def normalize_mri(image):
    p1, p99 = np.percentile(image, (1, 99))
    image_normalized = np.clip(image, p1, p99)
    image_normalized = (image_normalized - p1) / (p99 - p1)
    return image_normalized

def apply_window(image, window_center, window_width):
    min_val = window_center - window_width / 2
    max_val = window_center + window_width / 2
    return np.clip((image - min_val) / (max_val - min_val), 0, 1)




def create_custom_colormap():
    colors = [(0, 0, 0, 0),  # Transparent for background
              (1, 0, 0, 0.5),  # Red with 50% opacity for bone
              (0, 1, 0, 0.5),  # Red with 50% opacity for bone
              (1, 0, 0, 0.5),  # Green with 50% opacity for cartilage
              (0, 1, 0, 0.5)]  # Green with 50% opacity for cartilage
    return mcolors.ListedColormap(colors)

def plot_slice(slice, mask_slice, spacing=None, window_center=0.5, window_width=1.0, show_mask=True):
    aspect_ratio = spacing[1] / spacing[0] if spacing else 1
    fig, ax = plt.subplots(figsize=(6, 6))

    slice = np.rot90(slice)
    slice = apply_window(slice, window_center, window_width)
    
    ax.imshow(slice, cmap='gray', aspect=aspect_ratio)
    
    if show_mask:
        mask_slice = np.rot90(mask_slice)
        custom_cmap = create_custom_colormap()
        ax.imshow(mask_slice, cmap=custom_cmap, vmin=0, vmax=4, aspect=aspect_ratio)
    
    ax.axis('off')
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def image_viewer_page():
    st.title("DESS Segmentation")

    if st.session_state.selected_id is None:
        st.warning("Please select an ID on the ID Selection page first.")
        return

    selected_id = st.session_state.selected_id

    # Time point selection
    time_points = ['00m', '12m', '24m', '48m', '72m']
    selected_time_point = st.selectbox("Select Time Point", time_points)

    # Load image
    image_path = os.path.join(st.session_state.data_path, 'IMAGE', selected_time_point, f"DESS_{selected_time_point}", f"{selected_id}_*_SAG_3D_DESS_LEFT_0000.nii.gz")
    matching_files = [f for f in os.listdir(os.path.dirname(image_path)) if f.startswith(f"{selected_id}_") and f.endswith("_SAG_3D_DESS_LEFT_0000.nii.gz")]
    
    # Load mask
    mask_path = os.path.join(st.session_state.data_path, 'DATA', 'pred', f"pred_{selected_time_point.lower()}_PP", f"{selected_id}_*_SAG_3D_DESS_LEFT.nii.gz")
    matching_mask_files = [f for f in os.listdir(os.path.dirname(mask_path)) if f.startswith(f"{selected_id}_") and f.endswith("_SAG_3D_DESS_LEFT.nii.gz")]
    
    if matching_files and matching_mask_files:
        image_path = os.path.join(os.path.dirname(image_path), matching_files[0])
        mask_path = os.path.join(os.path.dirname(mask_path), matching_mask_files[0])
        
        image_np, spacing = load_nifti_file(image_path)
        image_np = normalize_mri(image_np)
        
        mask_np, _ = load_nifti_file(mask_path)

        # Add contrast adjustment controls
        st.sidebar.header("Image Adjustment")
        window_center = st.sidebar.slider("Window Center", 0.0, 1.0, 0.5, 0.01)
        window_width = st.sidebar.slider("Window Width", 0.0, 1.0, 0.5, 0.01)
        
        # Add mask toggle
        show_mask = st.sidebar.checkbox("Show Mask", value=True)

        # View selection
        st.sidebar.header("View Selection")
        view = st.sidebar.radio("Choose view", ["Sagittal", "Coronal", "Axial"])

        if view == "Axial":
            slice_num = st.sidebar.slider("Axial Slice", 0, image_np.shape[2] - 1, image_np.shape[2] // 2)
            slice_data = image_np[:, :, slice_num]
            mask_slice = mask_np[:, :, slice_num]
            spacing_2d = (spacing[0], spacing[1])
        elif view == "Coronal":
            slice_num = st.sidebar.slider("Coronal Slice", 0, image_np.shape[1] - 1, image_np.shape[1] // 2)
            slice_data = image_np[:, slice_num, :]
            mask_slice = mask_np[:, slice_num, :]
            spacing_2d = (spacing[0], spacing[2])
        else:  # Sagittal
            slice_num = st.sidebar.slider("Sagittal Slice", 0, image_np.shape[0] - 1, image_np.shape[0] // 2)
            slice_data = image_np[slice_num, :, :]
            mask_slice = mask_np[slice_num, :, :]
            spacing_2d = (spacing[1], spacing[2])

        img_str = plot_slice(slice_data, mask_slice, spacing_2d, window_center=window_center, window_width=window_width, show_mask=show_mask)

        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; height: 500px;">
            <img id="mri-image" src="data:image/png;base64,{img_str}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error(f"No image or mask found for ID {selected_id} at time point {selected_time_point}")
