import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import io

# Define the main page (CSV to Parquet converter)
def csv_to_parquet():
    st.title("CSV to Parquet Converter")
    csv_file = st.file_uploader("Upload a CSV file", type=["csv"])
    file_name = st.text_input("Downloaded Parquet File Name")
    if csv_file:
        df = pd.read_csv(csv_file)
        if file_name:
            file_name = file_name + ".parquet"
        else:
            file_name = "converted.parquet"
        
        parquet_file = df.to_parquet(index=False, path=None)
        st.success(f"CSV data converted to Parquet. Download the Parquet file below:")
        st.download_button(label="Download Parquet", data=parquet_file, file_name=file_name)     

        

# Define the second page (Parquet viewer)
def parquet_viewer():
    st.title("Parquet File Viewer")
    parquet_file = st.file_uploader("Upload a Parquet file", type=["parquet"])

    if parquet_file:
        try:
            df = pd.read_parquet(parquet_file)
            st.write("Preview of the first few rows:")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error reading the Parquet file: {e}")

# Create a multipage app
def main():
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose a page", ["CSV to Parquet", "Parquet Viewer"])

    if app_mode == "CSV to Parquet":
        csv_to_parquet()
    elif app_mode == "Parquet Viewer":
        parquet_viewer()

if __name__ == "__main__":
    main()
