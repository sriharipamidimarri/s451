import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Streamlit app
st.title("Commodity Price Prediction and Analysis")

# User inputs
commodity = st.text_input("Commodity", "Wheat")
location = st.text_input("Location", "Delhi")
date = st.date_input("Date")

if st.button("Predict"):
    api_url = "http://127.0.0.1:5000/predict"
    input_data = {"commodity": commodity, "location": location, "date": date.strftime('%Y-%m-%d')}

    response = requests.post(api_url, json=input_data)
    if response.status_code == 200:
        result = response.json()
        st.subheader(f"Predicted Price: ₹{result['predicted_price']}")
    else:
        st.error(f"Error: {response.json()['error']}")

if st.button("Analyze"):
    api_url = "http://127.0.0.1:5000/analysis"
    input_data = {"commodity": commodity, "location": location}

    response = requests.post(api_url, json=input_data)
    if response.status_code == 200:
        result = response.json()
        historical_data = pd.DataFrame(result['historical_data'])
        future_predictions = pd.DataFrame(result['future_predictions'])

        st.subheader("Historical Prices")
        st.write(historical_data)

        st.subheader("Future Predictions")
        st.write(future_predictions)

        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(historical_data['Arrival_Date'], historical_data['Historical_Price'], label='Historical Prices')
        plt.plot(future_predictions['Arrival_Date'], future_predictions['Predicted_Price'], label='Predicted Prices', color='orange')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        st.pyplot(plt)
    else:
        st.error(f"Error: {response.json()['error']}")
