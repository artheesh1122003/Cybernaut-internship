from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
import os

app = Flask(__name__)

MODEL_PATH = 'sleep_model.pkl'

if not os.path.exists(MODEL_PATH):
    print(f"Model File '{MODEL_PATH}' not found. Training it now...")
    from train_model import train
    train()
    
model = joblib.load(MODEL_PATH)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # Extract features
        sleep_duration = float(data.get('sleep_duration', 7.0))
        
        caffeine_map = {'None': 0, 'Low': 1, 'Moderate': 2, 'High': 3}
        caffeine = caffeine_map.get(data.get('caffeine', 'None'), 0)
        
        exercise = float(data.get('exercise', 0.0))
        screen_time = float(data.get('screen_time', 0.0))
        stress = int(data.get('stress', 5))
        
        mood_map = {'Happy': 0, 'Neutral': 1, 'Sad': 2, 'Anxious': 3}
        mood = mood_map.get(data.get('mood', 'Neutral'), 1)
        
        interruptions = 1 if data.get('interruptions') == 'Yes' else 0
        
        features = np.array([[
            sleep_duration, caffeine, exercise, screen_time, stress, mood, interruptions
        ]])
        
        prediction = model.predict(features)[0]
        
        quality_map = {0: 'Good', 1: 'Average', 2: 'Poor'}
        quality = quality_map.get(prediction, 'Unknown')
        
        tips = []
        if sleep_duration < 7:
            tips.append("Try to increase your sleep duration to at least 7-8 hours.")
        if caffeine >= 2:
            tips.append("Lower your caffeine intake, especially in the afternoon and evening.")
        if exercise < 30:
            tips.append("Increase your daily physical activity. Even a 30-minute walk can help.")
        if screen_time > 60:
            tips.append("Try reducing screen time by at least 30-60 minutes before bed.")
        if stress >= 7:
            tips.append("Your stress levels are high. Consider relaxation techniques like meditation.")
        if interruptions == 1:
            tips.append("Ensure your sleeping environment is quiet, dark, and cool.")
            
        if not tips and quality == 'Good':
            tips.append("Keep up the great habits! Your lifestyle is highly conducive to good sleep.")
        elif not tips and quality != 'Good':
            tips.append("Maintain consistency in your daily routines for better sleep schedules.")
            
        return jsonify({
            'success': True,
            'quality': quality,
            'tips': tips
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
