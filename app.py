from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from textblob import TextBlob

app = Flask(__name__)

# Step 1: Scraping Data Historis dari ForexFactory
def scrape_forexfactory_historical(start_year, end_year):
    base_url = "https://www.forexfactory.com/calendar"
    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):  # Loop through all months
            url = f"{base_url}?month={month}.{year}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                return None, f"Failed to fetch data for {month}/{year}. Status code: {response.status_code}"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rows = soup.find_all('tr', class_='calendar__row')
            if not rows:
                return None, f"No data found for {month}/{year}."
            
            for row in rows:
                try:
                    date = row.find('td', class_='calendar__date').text.strip()
                    currency = row.find('td', class_='calendar__currency').text.strip()
                    impact = row.find('td', class_='calendar__impact').find('span')['title']
                    event = row.find('td', class_='calendar__event').text.strip()
                    actual = row.find('td', class_='calendar__actual').text.strip()
                    forecast = row.find('td', class_='calendar__forecast').text.strip()
                    previous = row.find('td', class_='calendar__previous').text.strip()
                    
                    if "High Impact" in impact:
                        all_data.append([date, currency, impact, event, actual, forecast, previous])
                except Exception as e:
                    continue
    
    df = pd.DataFrame(all_data, columns=['Date', 'Currency', 'Impact', 'Event', 'Actual', 'Forecast', 'Previous'])
    return df, None

# Step 2: Preprocessing Data
def preprocess_data(df):
    # Convert Actual, Forecast, Previous to numeric
    df['Actual'] = pd.to_numeric(df['Actual'].str.replace('%', '').str.replace('K', 'e3').str.replace('M', 'e6'), errors='coerce')
    df['Forecast'] = pd.to_numeric(df['Forecast'].str.replace('%', '').str.replace('K', 'e3').str.replace('M', 'e6'), errors='coerce')
    df['Previous'] = pd.to_numeric(df['Previous'].str.replace('%', '').str.replace('K', 'e3').str.replace('M', 'e6'), errors='coerce')
    
    # Calculate difference between Actual and Forecast
    df['Difference'] = df['Actual'] - df['Forecast']
    
    # Label Good/Bad based on Difference
    df['Outcome'] = np.where(df['Difference'] > 0, 'Good', 'Bad')
    
    # Sentiment Analysis on Event
    df['Sentiment'] = df['Event'].apply(lambda x: TextBlob(x).sentiment.polarity)
    
    return df.dropna()

# Step 3: Train Gradient Boosting Model
def train_model(df):
    X = df[['Actual', 'Forecast', 'Previous', 'Sentiment']]
    y = df['Difference']
    
    model = GradientBoostingRegressor(n_estimators=200, max_depth=5, learning_rate=0.1)
    model.fit(X, y)
    
    return model

# Route for home page
@app.route('/')
def home():
    return render_template('index.html')

# Route for scraping progress
@app.route('/scrape', methods=['POST'])
def scrape():
    start_year = 2018
    end_year = 2025
    progress = []
    
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            progress.append(f"Scraping data for {month}/{year}...")
            historical_data, error = scrape_forexfactory_historical(year, year)
            
            if error:
                return jsonify({"error": error}), 404
            
    # Preprocess data
    processed_data = preprocess_data(historical_data)
    
    # Train model
    model = train_model(processed_data)
    
    return jsonify({"message": "Scraping completed successfully!", "progress": progress})

# Route for prediction
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    event = data['event']
    actual = float(data['actual'])
    forecast = float(data['forecast'])
    previous = float(data['previous'])
    
    # Sentiment analysis
    sentiment = TextBlob(event).sentiment.polarity
    
    # Predict difference
    prediction = model.predict([[actual, forecast, previous, sentiment]])[0]
    outcome = "Good" if prediction > 0 else "Bad"
    
    return jsonify({
        'predicted_difference': round(prediction, 2),
        'outcome': outcome
    })

# Route for 404 Not Found
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
