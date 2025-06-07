import pandas as pd
import numpy as np
import streamlit as st
import re
import asyncio
import nest_asyncio
from streamlit.components.v1 import html

nest_asyncio.apply()

st.set_page_config(
    page_title="Your Dream Home Finder",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS for styling
st.markdown("""
    <style>
        body {
            background-color: #f5f7fa;
        }
        .main {
            background-color: #f5f7fa;
        }
        .property-card {
            border: 2px solid #ccc;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            background-color: #ffffff;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        }
        .property-card h3 {
            color: #1e90ff;
        }
        .property-detail {
            font-size: 16px;
        }
        .property-detail span {
            font-weight: bold;
            color: #444;
        }
    </style>
""", unsafe_allow_html=True)

DATA_PATH = 'properties.csv'

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    required_columns = ['type', 'title', 'location', 'bedroom', 'bathroom', 'size_sqm', 'price', 'contact_person', 'image_link']
    if not all(col in df.columns for col in required_columns):
        st.error(f"Dataset must contain the following columns: {', '.join(required_columns)}")
        st.stop()

    df['price'] = df['price'].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce')
    for col in ['bedroom', 'bathroom', 'size_sqm']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'City' not in df.columns:
        df['City'] = df['location'].apply(lambda x: x.split(',')[-2].strip() if pd.notna(x) and ',' in x else x)

    df['phone_number'] = df['contact_person'].astype(str)
    df.dropna(subset=required_columns + ['phone_number'], inplace=True)

    # Menghapus encode title yang rusak
    def is_gibberish(text):
        if pd.isna(text): return False
        non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / len(text)
        return non_ascii_ratio > 0.5

    df = df[~df['title'].apply(is_gibberish)]

    df['formatted_price'] = df['price'].apply(lambda x: f"EGP {int(x):,}" if pd.notna(x) else "-")

    return df

df = load_data()

unique_types = ['Any'] + sorted(df['type'].unique())
unique_locations = ['Any'] + sorted(df['City'].dropna().unique())

min_bedroom_data = int(df['bedroom'].dropna().min())
max_bedroom_data = int(df['bedroom'].dropna().max())
min_bathroom_data = int(df['bathroom'].dropna().min())
max_bathroom_data = int(df['bathroom'].dropna().max())
min_size_data = int(df['size_sqm'].dropna().min())
max_size_data = int(df['size_sqm'].dropna().max())
min_price_data = int(df['price'].dropna().min())
max_price_data = int(df['price'].dropna().max())

def recommend_houses(df_data, user_inputs, top_n=5):
    filtered_df = df_data.copy()
    if user_inputs['type'] != 'Any':
        filtered_df = filtered_df[filtered_df['type'] == user_inputs['type']]
    if user_inputs['location'] != 'Any':
        filtered_df = filtered_df[filtered_df['City'] == user_inputs['location']]
    if user_inputs['bedroom_min'] is not None:
        filtered_df = filtered_df[filtered_df['bedroom'] >= user_inputs['bedroom_min']]
    if user_inputs['bathroom_min'] is not None:
        filtered_df = filtered_df[filtered_df['bathroom'] >= user_inputs['bathroom_min']]
    if user_inputs['size_min'] is not None:
        filtered_df = filtered_df[filtered_df['size_sqm'] >= user_inputs['size_min']]
    if user_inputs['size_max'] is not None:
        filtered_df = filtered_df[filtered_df['size_sqm'] <= user_inputs['size_max']]
    if user_inputs['price_min'] is not None:
        filtered_df = filtered_df[filtered_df['price'] >= user_inputs['price_min']]
    if user_inputs['price_max'] is not None:
        filtered_df = filtered_df[filtered_df['price'] <= user_inputs['price_max']]

    if filtered_df.empty:
        st.warning("No matching results. Showing closest matches instead.")
        relaxed_df = df_data.copy()
        if user_inputs['type'] != 'Any':
            relaxed_df = relaxed_df[relaxed_df['type'] == user_inputs['type']]
        if user_inputs['location'] != 'Any':
            relaxed_df = relaxed_df[relaxed_df['City'] == user_inputs['location']]
        return relaxed_df.sort_values(by='price').head(top_n)

    return filtered_df.sort_values(by='price').head(top_n)

st.title("\U0001F3E1 Find Your Dream House in Egypt")
st.markdown("Fill in your preferences to get the best recommendations‼️")

with st.sidebar:
    st.header("Preferences Filter")
    property_type = st.selectbox("Property Type:", unique_types, key='type')
    location = st.selectbox("City:", unique_locations)
    bedroom_min = st.number_input("Min. Bedrooms:", min_value=0, max_value=max_bedroom_data+5, value=min_bedroom_data)
    bathroom_min = st.number_input("Min. Bathrooms:", min_value=0, max_value=max_bathroom_data+5, value=min_bathroom_data)
    size_min_input = st.number_input("Min. Size (sqm):", min_value=0, value=min_size_data)
    size_max_input = st.number_input("Max. Size (sqm):", min_value=1, value=max_size_data+100)
    price_min_idr = st.number_input("Min. Price (EGP):", min_value=0, value=min_price_data)
    price_max_idr = st.number_input("Max. Price (EGP):", min_value=0, value=max_price_data+1_000_000_000)

    if st.button("Search Houses"):
        user_inputs = {
            'type': property_type,
            'location': location,
            'bedroom_min': bedroom_min,
            'bathroom_min': bathroom_min,
            'size_min': size_min_input,
            'size_max': size_max_input,
            'price_min': price_min_idr,
            'price_max': price_max_idr
        }
        st.session_state['recommendations'] = recommend_houses(df, user_inputs)

# Tambahkan CSS custom
st.markdown("""
    <style>
        .property-card {
            background-color: #CDBE78;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            font-weight: 800;
        }
        .property-card h3 {
            color: #c0392b;
            margin: 0 0 10px 0;
        }
        .property-detail p {
            margin: 5px 0;
            font-size: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Tampilkan rekomendasi
if 'recommendations' in st.session_state and not st.session_state['recommendations'].empty:
    st.subheader("🌟 Recommended Properties:")
    for _, row in st.session_state['recommendations'].iterrows():
        st.markdown(f"""
        <div class="property-card">
            <div style="display: flex; align-items: center;">
                <img src="{row['image_link']}" width="180" style="margin-right: 20px; border-radius: 10px;"/>
                <div>
                    <h3 style="font-weight: 800; margin-bottom: 0px;">{row['title']}</h3>
                    <div class="property-detail" style="color: #000;">
                        <p style="margin-top: 1px;">Location: {row['location']}</p>
                        <p style="margin: 1px 0;">Type: {row['type']} | Bedrooms: {int(row['bedroom'])} | Bathrooms: {int(row['bathroom'])}</p>
                        <p style="margin: 1px 0;">Size: {int(row['size_sqm'])} m²</p>
                        <p style="margin: 1px 0;">Price: <span style='color:#c0392b; font-weight: bold;'>{row['formatted_price']}</span></p>
                        <p style="margin: 1px 0;"><a href="https://wa.me/{row['phone_number']}" target="_blank">📞 Contact via WhatsApp</a></p>
                    </div>
                </div>  
            </div>
        </div>
        """, unsafe_allow_html=True)




