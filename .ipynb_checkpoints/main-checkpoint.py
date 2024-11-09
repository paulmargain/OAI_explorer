import streamlit as st
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import os
import nibabel as nib
import base64
from io import BytesIO
import pyvista as pv
from stpyvista import stpyvista

def load_and_store_dicom_series(directory, session_key):
    if session_key not in st.session_state:
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(directory)
        reader.SetFileNames(dicom_names)
        image_sitk = reader.Execute()
        image_np = sitk.GetArrayFromImage(image_sitk)
        spacing = image_sitk.GetSpacing()
        st.session_state[session_key] = (image_np, spacing)
    return st.session_state[session_key]

def normalize_mri(image):
    p1, p99 = np.percentile(image, (1, 99))
    image_normalized = np.clip(image, p1, p99)
    image_normalized = (image_normalized - p1) / (p99 - p1)
    return image_normalized

def apply_window(image, window_center, window_width):
    min_val = window_center - window_width / 2
    max_val = window_center + window_width / 2
    return np.clip((image - min_val) / (max_val - min_val), 0, 1)

def plot_slice(slice, mask_slice=None, spacing=None, is_nifti=False, window_center=0.5, window_width=1.0):
    aspect_ratio = spacing[1] / spacing[0] if spacing else 1
    fig, ax = plt.subplots(figsize=(6, 6))

    if is_nifti:
        slice = np.rot90(slice)
        if mask_slice is not None:
            mask_slice = np.rot90(mask_slice)
    else:
        slice = slice[::-1, ::-1]
        if mask_slice is not None:
            mask_slice = mask_slice[::-1, ::-1]

    slice = apply_window(slice, window_center, window_width)

    ax.imshow(slice, cmap='gray', aspect=aspect_ratio)

    if mask_slice is not None:
        ax.imshow(mask_slice, cmap='hot', alpha=0.3, aspect=aspect_ratio)

    ax.axis('off')
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def load_nifti_file(filepath, session_key):
    if session_key not in st.session_state:
        nifti_img = nib.load(filepath)
        image_np = np.asanyarray(nifti_img.dataobj)
        spacing = nifti_img.header.get_zooms()[:3]
        st.session_state[session_key] = (image_np, spacing)
    return st.session_state[session_key]

def mri_viewer():
    st.markdown("""
    <style>
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    </style>
    """, unsafe_allow_html=True)

    st.title("3D MRI Viewer")

    uploaded_files = st.file_uploader("Choose DICOM or NIfTI Files", accept_multiple_files=True, type=["dcm", "nii", "nii.gz"], key="file_uploader")
    mask_file = st.file_uploader("Choose Mask File (NIfTI)", type=["nii", "nii.gz"], key="mask_uploader")

    if uploaded_files:
        with tempfile.TemporaryDirectory() as temp_dir:
            is_nifti = False
            for uploaded_file in uploaded_files:
                bytes_data = uploaded_file.read()
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, 'wb') as f:
                    f.write(bytes_data)
                if uploaded_file.name.endswith(('.nii', '.nii.gz')):
                    is_nifti = True

            if is_nifti:
                image_np, spacing = load_nifti_file(file_path, "nifti_image_data")
            else:
                image_np, spacing = load_and_store_dicom_series(temp_dir, "dicom_image_data")

        if mask_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz') as temp_mask_file:
                temp_mask_file.write(mask_file.getvalue())
                mask_np, mask_spacing = load_nifti_file(temp_mask_file.name, "mask_data")
            os.unlink(temp_mask_file.name)
        else:
            mask_np = None

        # Normalize the MRI image globally
        image_np = normalize_mri(image_np)

        # Add contrast adjustment controls
        st.sidebar.header("Contrast Adjustment")
        window_center = st.sidebar.slider("Window Center", 0.0, 1.0, 0.5, 0.01)
        window_width = st.sidebar.slider("Window Width", 0.0, 1.0, 0.5, 0.01)

        # View selection
        st.sidebar.header("View Selection")
        view = st.sidebar.radio("Choose view", ["Axial", "Coronal", "Sagittal"])

        if view == "Axial":
            slice_num = st.sidebar.slider("Axial Slice", 0, image_np.shape[2] - 1, image_np.shape[2] // 2)
            slice_data = image_np[:, :, slice_num]
            mask_slice = mask_np[:, :, slice_num] if mask_np is not None else None
            spacing_2d = (spacing[0], spacing[1])
        elif view == "Coronal":
            slice_num = st.sidebar.slider("Coronal Slice", 0, image_np.shape[1] - 1, image_np.shape[1] // 2)
            slice_data = image_np[:, slice_num, :]
            mask_slice = mask_np[:, slice_num, :] if mask_np is not None else None
            spacing_2d = (spacing[0], spacing[2])
        else:  # Sagittal
            slice_num = st.sidebar.slider("Sagittal Slice", 0, image_np.shape[0] - 1, image_np.shape[0] // 2)
            slice_data = image_np[slice_num, :, :]
            mask_slice = mask_np[slice_num, :, :] if mask_np is not None else None
            spacing_2d = (spacing[1], spacing[2])

        img_str = plot_slice(slice_data, mask_slice, spacing_2d, is_nifti=is_nifti, window_center=window_center, window_width=window_width)

        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; height: 500px;">
            <img id="mri-image" src="data:image/png;base64,{img_str}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
        </div>
        <script>
            function resizeImage() {{
                var img = document.getElementById('mri-image');
                var container = img.parentElement;
                var containerWidth = container.offsetWidth;
                var containerHeight = container.offsetHeight;
                var imgAspectRatio = img.naturalWidth / img.naturalHeight;
                var containerAspectRatio = containerWidth / containerHeight;

                if (imgAspectRatio > containerAspectRatio) {{
                    img.style.width = '100%';
                    img.style.height = 'auto';
                }} else {{
                    img.style.width = 'auto';
                    img.style.height = '100%';
                }}
            }}

            window.addEventListener('load', resizeImage);
            window.addEventListener('resize', resizeImage);
        </script>
        """, unsafe_allow_html=True)

def load_scalar_from_file(file):
    scalars = []
    for line in file:
        scalars.append(float(line.strip()))
    return np.array(scalars)

def bone_viewer():
    st.title("3D Bone Viewer with PBR")

    obj_file = st.file_uploader("Upload OBJ file", type="obj")
    scalar_file = st.file_uploader("Upload scalar file (txt)", type="txt")

    if obj_file and scalar_file:
        with tempfile.TemporaryDirectory() as temp_dir:
            obj_path = os.path.join(temp_dir, "model.obj")

            # Save uploaded OBJ file to temporary directory
            with open(obj_path, "wb") as f:
                f.write(obj_file.getvalue())

            # Read the OBJ file
            mesh = pv.read(obj_path)

            # Load scalars from the uploaded text file
            scalars = load_scalar_from_file(scalar_file)

            # Ensure the number of scalars matches the number of points in the mesh
            if len(scalars) != mesh.n_points:
                st.error(f"Number of scalars ({len(scalars)}) does not match number of vertices in the mesh ({mesh.n_points})")
                return

            # Add scalars to the mesh
            mesh.point_data['scalars'] = scalars

            # Create a plotter with PBR enabled
            plotter = pv.Plotter(lighting=None, window_size=[800, 600])

            # Set background color
            plotter.set_background('black')

            # Add mesh to the plotter with PBR and jet colormap
            plotter.add_mesh(
                mesh,
                scalars='scalars',
                cmap='jet',
                show_edges=False,
                pbr=True,
                metallic=0.1,  # Bone is not very metallic
                roughness=0.6,  # Bone has a moderate roughness
                diffuse=1.0,
            )

            # Add lights
            light1 = pv.Light(position=(-2, 2, 0), focal_point=(0, 0, 0), color='white')
            plotter.add_light(light1)

            light2 = pv.Light(position=(2, 0, 0), focal_point=(0, 0, 0), color=(0.7, 0.0862, 0.0549))
            plotter.add_light(light2)

            light3 = pv.Light(position=(0, 0, 10), focal_point=(0, 0, 0), color='white')
            plotter.add_light(light3)

            # Set up the camera
            plotter.camera_position = 'iso'
            plotter.camera.zoom(0.8)

            # Add controls for rotation
            plotter.add_camera_orientation_widget()

            # Add a colorbar
            plotter.add_scalar_bar('Scalar Values', vertical=True, position_x=0.05, position_y=0.05)

            # Display the plot
            stpyvista(plotter, key="pv_obj")
    else:
        st.write("Please upload both an OBJ file and a scalar file.")

def main():
    st.set_page_config(page_title='3D Viewer', layout="wide")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["MRI Viewer", "Bone Viewer"])

    if page == "MRI Viewer":
        mri_viewer()
    else:
        bone_viewer()

if __name__ == "__main__":
    main()
