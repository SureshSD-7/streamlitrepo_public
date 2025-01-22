import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import create_engine

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "00000"

# Disable actions (e.g., zoom, pan, reset) for embedded charts
alt.renderers.set_embed_options(actions=False)


def get_db_connection():
    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    return engine

def fetch_data(query):
    engine = get_db_connection()
    return pd.read_sql(query, engine)

actual_price_query = "SELECT LOWER(material) AS material, record_date AS date, price AS price_actual FROM material_prices;"
predicted_price_query = "SELECT LOWER(metal) AS material, model, prediction_date AS date, prediction_value AS price_predicted FROM predictions;"

# Fetch data
actual_price = fetch_data(actual_price_query)
predicted_price = fetch_data(predicted_price_query)

# Convert date columns to datetime
actual_price['date'] = pd.to_datetime(actual_price['date'])
predicted_price['date'] = pd.to_datetime(predicted_price['date'])

# Sidebar filters
st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Start Date", actual_price['date'].min())
end_date = st.sidebar.date_input("End Date", actual_price['date'].max())
material_name = st.sidebar.selectbox("Material Name", actual_price['material'].unique())
# model_name = st.sidebar.selectbox("Model Name", predicted_price['model'].unique())

multiple_model = st.sidebar.multiselect("Model Name", predicted_price['model'].unique(), default=predicted_price['model'].unique()[0])

if start_date > end_date:
    st.sidebar.error("Error: End Date must be after Start Date.")
else:
    # Filter actual and predicted data separately
    filtered_actual_price = actual_price[
        (actual_price['date'] >= pd.Timestamp(start_date)) &
        (actual_price['date'] <= pd.Timestamp(end_date)) &
        (actual_price['material'] == material_name)
    ]

    filtered_predicted_price = predicted_price[
        (predicted_price['date'] >= pd.Timestamp(start_date)) &
        (predicted_price['date'] <= pd.Timestamp(end_date)) &
        (predicted_price['material'] == material_name) &
        (predicted_price['model'].isin(multiple_model))
    ]

    # Combine actual and predicted data for a unified chart with a legend
    filtered_actual_price['type'] = "Actual Price"
    filtered_predicted_price['type'] = "Predicted Price"
    
    
    # filtered_actual_price = filtered_actual_price.rename(columns={"price_actual": "price"})
    # filtered_predicted_price = filtered_predicted_price.rename(columns={"price_predicted": "price"})

    
    selection = alt.selection_multi(fields=['type'], bind='legend')
    # Create Altair charts
    actual_price_chart = alt.Chart(filtered_actual_price).mark_line(color="blue").encode(
        x="date:T",
        y=alt.Y("price_actual:Q", title="Price"),
        color=alt.Color("type:N", scale=alt.Scale(domain=["Actual Price", "Predicted Price"], range=["blue", "red"]), title="Price_type"),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
        tooltip=["date:T", "price_actual:Q"]
    ).add_selection(selection)

    predicted_price_chart = alt.Chart(filtered_predicted_price).mark_line(color="red").encode(
        x="date:T",
        y=alt.Y("price_predicted:Q", title="Price"),
        color=alt.Color("type:N", scale=alt.Scale(domain=["Actual Price", "Predicted Price"], range=["blue", "red"]), title="Price_type"),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
        tooltip=["date:T", "price_predicted:Q"]
    ).add_selection(selection)
    
    # Merge actual and predicted data to calculate the price difference
    price_difference_data = pd.merge(
        filtered_actual_price,
        filtered_predicted_price,
        on=["date", "material"],
        how="inner",
        suffixes=("_actual", "_predicted")
    )

    price_difference_data['price_difference'] = price_difference_data['price_actual'] - price_difference_data['price_predicted']
    # Calculate the percentage difference
    price_difference_data['price_difference_percentage'] = (
        (price_difference_data['price_difference'] / price_difference_data['price_actual']) * 100
    ).round()

    
    # Combine charts
    combined_chart = alt.layer(
        actual_price_chart,
        predicted_price_chart
    ).resolve_scale(
        y="shared"
    ).properties(
        title="Actual vs Predicted Prices Over Time",
        width=800,
        height=400
    )
    # Create a chart for price difference
    # price_difference_chart = alt.Chart(price_difference_data).mark_bar(color="green").encode(
    #     x=alt.X("date:T", title="Date"),
    #     y=alt.Y("price_difference_percentage:Q", title="Price Difference"),
    #     tooltip=["date:T", "price_difference_percentage:Q"],
    #     text="price_difference_percentage:Q"
    # ).properties(
    #     title="Price Difference percentage",
    #     width=800,
    #     height=400
    # )
    
    # Create a chart for percentage price difference
    price_difference_percentage_chart = alt.Chart(price_difference_data).mark_bar(color="purple").encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("price_difference_percentage:Q", title="Price Difference (%)"),
        color = alt.condition(
            alt.datum.price_difference_percentage > 0,
            alt.value("steelblue"),  # The positive color
            alt.value("orange")  # The negative color 
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("price_difference_percentage:Q", title="Price Difference (%)", format=".0f")
        ]
    ).properties(
        title="Percentage Price Difference",
        width=800,
        height=400
    ).interactive()
    
    text = price_difference_percentage_chart.mark_text(
        align='left',
        baseline='middle',
        dx=3  # Nudges text to right so it doesn't appear on top of the bar
    ).encode(
        text='price_difference_percentage:Q'
    )
    
    price_difference_percentage_chart = (price_difference_percentage_chart + text)

    combined_chart["usermeta"] = {
    "embedOptions": {
        "downloadFileName": "price-comparison",
        "actions": {"export": True, "source": False, "editor": False, "compiled": False},
    }
    }

    price_difference_percentage_chart["usermeta"] = {
    "embedOptions": {
        "downloadFileName": "price-difference",
        "actions": {"export": True, "source": False, "editor": False, "compiled": False},
    }
    }
    
    # Display the chart
    st.altair_chart(combined_chart, theme= None, use_container_width=True)
    # st.altair_chart(price_difference_chart, use_container_width=True)
    st.altair_chart(price_difference_percentage_chart, theme= None, use_container_width=True)
    
    
    

    # # Display data tables
    # st.subheader("Filtered Actual Prices")
    # st.write(filtered_actual_price)

    # st.subheader("Filtered Predicted Prices")
    # st.write(filtered_predicted_price)
