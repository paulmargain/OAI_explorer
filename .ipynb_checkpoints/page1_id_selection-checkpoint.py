import streamlit as st
import pandas as pd
import os
from PIL import Image

def get_all_ids():
    base_paths = [
        '/media/chuv/T7/DATA/processed_PP/00m',
        '/media/chuv/T7/DATA/processed_PP/12m',
        '/media/chuv/T7/DATA/processed_PP/24m',
        '/media/chuv/T7/DATA/processed_PP/48m',
        '/media/chuv/T7/DATA/processed_PP/72m'
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
    print(ids_sets)
    return sorted(list(all_ids))

def load_data():
    df = pd.read_csv('/media/chuv/T7/DATA/processed_PP/OAI_KL.csv')
    all_ids = get_all_ids()
    return df[df['ID'].isin(all_ids)]

def id_selection_page():
    st.title('ID Selection with KLs')

    # Load and filter data
    df = load_data()

    # KL value selection
    st.sidebar.header("Select KL Values")
    kl_columns = [col for col in df.columns if col.startswith('KL_')]
    kl_filters = {}

    for col in kl_columns:
        unique_values = sorted(df[col].dropna().unique())
        kl_filters[col] = st.sidebar.selectbox(f'Choose {col} value', options=['Any'] + list(unique_values))

    # Filter data based on selected KL values
    filtered_df = df.copy()
    for col, value in kl_filters.items():
        if value != 'Any':
            filtered_df = filtered_df[filtered_df[col] == value]

    # Display filtered IDs
    id_df = filtered_df[['ID'] + kl_columns].drop_duplicates()
    st.dataframe(id_df)

    # Select specific ID
    selected_id = st.selectbox('Choose ID', options=id_df['ID'].unique())

    if st.button('Confirm Selection'):
        st.session_state.selected_id = selected_id
        st.success(f"ID {selected_id} selected. You can now proceed to the Image Viewer or STL Viewer.")

# Run the app
if __name__ == '__main__':
    id_selection_page()
