import streamlit as st
from page1_id_selection import id_selection_page
from page2_image_viewer import image_viewer_page
from page3_stl_viewer import stl_viewer_page
from page4_maps_comparaison import comp_viewer_page
st.set_page_config(page_title='OAI Data Viewer', layout="wide")

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["ID Selection", "DESS Segmentation", "Model Viewer","Comparaison of maps"])

    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None

    if page == "ID Selection":
        id_selection_page()
    elif page ==  "DESS Segmentation":
        image_viewer_page()
    elif page =='Model Viewer':
        stl_viewer_page()
    else:
        comp_viewer_page()

if __name__ == "__main__":
    main()