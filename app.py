import streamlit as st

st.title("🔮 SEOcuantic - Test")
st.write("If you see this, it works!")

uploaded_file = st.file_uploader("Upload CSV", type=['csv'])

if uploaded_file:
    import pandas as pd
    df = pd.read_csv(uploaded_file)
    st.write(f"Rows: {len(df)}")
    st.dataframe(df.head())
