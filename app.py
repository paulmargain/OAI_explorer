import streamlit as st
from streamlit_option_menu import option_menu
from page1_id_selection import id_selection_page
from page2_image_viewer import image_viewer_page
from page3_stl_viewer import stl_viewer_page
from page4_maps_comparaison import comp_viewer_page
import os

st.set_page_config(page_title='OAI Data Viewer', layout="wide")

def main():
    # Initialize session state for data path
    if "data_path" not in st.session_state:
        st.session_state.data_path = None
    
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None

    # Data path selection
    if st.session_state.data_path is None:
        st.title("OAI Data Viewer Setup")
        data_path = st.text_input("Enter the path to your data folder (e.g., /media/chuv/T7):")
        if st.button("Confirm Path"):
            print(data_path)
            if os.path.exists(data_path):
                st.session_state.data_path = data_path
                
                st.rerun()
            else:
                st.error("Invalid path. Please enter a valid directory path.")
        return

    # Main navigation menu
    selected = option_menu(
        None, 
        ["ID Selection", "DESS Segmentation", "Model Viewer", "Comparaison of maps"],
        menu_icon="cast", 
        default_index=0, 
        orientation="horizontal"
    )

    if selected == "ID Selection":
        id_selection_page()
    elif selected == "DESS Segmentation":
        image_viewer_page()
    elif selected == 'Model Viewer':
        stl_viewer_page()
    else:
        comp_viewer_page()

if __name__ == "__main__":
    main()