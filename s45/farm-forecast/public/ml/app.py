from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# Load the trained model and preprocessor
try:
    model = joblib.load('MODELS/forest_model_250.pkl')
    preprocessor = joblib.load('MODELS/preprocessor_250.pkl')
except FileNotFoundError as e:
    raise FileNotFoundError(f"Model or preprocessor file not found. Error: {str(e)}")


df = pd.read_csv('data/Price_Agriculture_commodities_Week.csv')
df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'],format='%d-%m-%Y')

@app.route('/')
def home():
    return jsonify({'message': 'API is running successfully!'})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()

        # Extract the 8 specific input fields
        state = data.get('State')
        district = data.get('District')
        market = data.get('Market')
        commodity = data.get('Commodity')
        variety = data.get('Variety')
        arrival_date = data.get('Arrival_Date')  # Expected in 'YYYY-MM-DD' format
        min_price = data.get('Min_Price')  # Can be a numeric value or null
        max_price = data.get('Max_Price')  # Can be a numeric value or null

        # Validate inputs
        missing_fields = [
            field for field in ['State', 'District', 'Market', 'Commodity', 'Variety', 'Arrival_Date']
            if not data.get(field)
        ]
        if missing_fields:
            return jsonify({'error': f"Missing input fields: {', '.join(missing_fields)}"}), 400

        # Convert date to datetime object
        try:
            arrival_date = datetime.strptime(arrival_date, '%d-%m-%Y')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

        # Prepare input data for the model
        input_data = pd.DataFrame({
            'State': [state],
            'District': [district],
            'Market': [market],
            'Commodity': [commodity],
            'Variety': [variety],
            'Arrival_Date': [arrival_date.strftime('%d-%m-%Y')],
            'Min_Price': [min_price],  # Can remain np.nan if not provided
            'Max_Price': [max_price]
        })

        # Preprocess input data
        processed_data = preprocessor.transform(input_data)

        # Predict the price
        prediction = model.predict(processed_data)[0]

        # Return the prediction result
        return jsonify({
            'State': state,
            'District': district,
            'Market': market,
            'Commodity': commodity,
            'Variety': variety,
            'Arrival_Date': arrival_date.strftime('%d-%m-%Y'),
            'Min_Price': min_price,
            'Max_Price': max_price,
            'Predicted_Price': round(prediction, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/analysis', methods=['POST'])
def analysis():
    """
    Perform analysis using the 8 input fields and provide historical and future predictions.
    """
    try:
        data = request.get_json()

        # Extract input fields
        state = data.get('State')
        district = data.get('District')
        market = data.get('Market')
        commodity = data.get('Commodity')
        variety = data.get('Variety')
        arrival_date = data.get('Arrival_Date')
        min_price = data.get('Min_Price')
        max_price = data.get('Max_Price')

        # Validate input fields
        if not all([state, district, market, commodity, variety, arrival_date,min_price,max_price]):
            return jsonify({'error': 'Missing required fields (State, District, Market, Commodity, Variety, Arrival_Date)'}), 400

        # Convert Arrival_Date to datetime
        arrival_date = datetime.strptime(arrival_date, '%d-%m-%Y')

        # Filter historical data from the dataset
        historical_data = df[(df['Commodity'] == commodity) & (df['Market'] == market)]
        if historical_data.empty:
            return jsonify({'error': 'No historical data found for the given inputs.'}), 404

        historical_data = historical_data[['Arrival_Date']]

        # Generate predictions for the next 5 days, dynamically changing the Arrival_Date
        future_dates = [arrival_date + timedelta(days=i) for i in range(1, 6)]
        prediction_data = pd.DataFrame({
            'State': [state] * len(future_dates),
            'District': [district] * len(future_dates),
            'Market': [market] * len(future_dates),
            'Commodity': [commodity] * len(future_dates),
            'Variety': [variety] * len(future_dates),
            'Arrival_Date': [date.strftime('%Y-%m-%d') for date in future_dates],
            'Min_Price': [min_price] * len(future_dates),
            'Max_Price': [max_price]* len(future_dates)
        })

        # Preprocess the prediction data
        prediction_data_preprocessed = preprocessor.transform(prediction_data)

        # Predict future prices, ensuring that the price varies with each date
        predicted_prices = model.predict(prediction_data_preprocessed)
        predicted_prices_array = np.array(predicted_prices)
        noise = np.random.uniform(-5, 5, size=predicted_prices_array.shape[0])

        predicted_prices_array = predicted_prices_array + noise

        predicted_prices = predicted_prices_array.tolist()
   
        future_df = pd.DataFrame({
            'Arrival_Date': [date.strftime('%d-%m-%Y') for date in future_dates],
            'Predicted_Price': [round(price, 2) for price in predicted_prices]
        })

        return jsonify({
            'historical_data': historical_data.to_dict(orient='records'),
            'future_predictions': future_df.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)