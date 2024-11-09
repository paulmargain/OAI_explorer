import streamlit as st
import pandas as pd
import os
from PIL import Image

def get_all_ids():
    base_paths = [
        os.path.join(st.session_state.data_path, 'DATA/processed_PP/00m'),
        os.path.join(st.session_state.data_path, 'DATA/processed_PP/12m'),
        os.path.join(st.session_state.data_path, 'DATA/processed_PP/24m'),
        os.path.join(st.session_state.data_path, 'DATA/processed_PP/48m'),
        os.path.join(st.session_state.data_path, 'DATA/processed_PP/72m')
    ]
    
    ids_sets = []
    
    for base_path in base_paths:
        ids = set()
        for folder in os.listdir(base_path):
            try:
                id = folder.split('_')[0]
                ids.add(int(id))
            except ValueError:
                # Skip folders that don't start with a number
                continue
        ids_sets.append(ids)
    
    all_ids = set.union(*ids_sets)
   
    return sorted(list(all_ids))

def load_data():
    df = pd.read_csv(os.path.join(st.session_state.data_path, 'DATA/processed_PP/OAI_KL.csv'))
    all_ids = get_all_ids()
    return df[df['ID'].isin(all_ids)]

def id_selection_page():
    st.title('ID Selection with KLs')

    # Load data
    df = load_data()

    # Display all IDs with KL values
    id_df = df[['ID'] + [col for col in df.columns if col.startswith('KL_')]].drop_duplicates()
    st.dataframe(id_df)

    # Select specific ID
    selected_id = st.selectbox('Choose ID', options=id_df['ID'].unique())

    if st.button('Confirm Selection'):
        st.session_state.selected_id = selected_id
        st.success(f"ID {selected_id} selected. You can now proceed to the Image Viewer or STL Viewer.")

# Run the app
if __name__ == '__main__':
    id_selection_page()
