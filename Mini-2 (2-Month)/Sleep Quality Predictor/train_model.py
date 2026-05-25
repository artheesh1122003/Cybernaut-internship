import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train():
    print("Generating simulated sleep data...")
    np.random.seed(42)
    n_samples = 2000

    # Features:
    # Sleep Duration: 4.0 to 10.0
    sleep_duration = np.random.uniform(4.0, 10.0, n_samples)
    # Caffeine Intake: 0: None, 1: Low, 2: Moderate, 3: High
    caffeine = np.random.randint(0, 4, n_samples)
    # Exercise Duration: 0 to 120
    exercise = np.random.uniform(0, 120, n_samples)
    # Screen Time: 0 to 180
    screen_time = np.random.uniform(0, 180, n_samples)
    # Stress Level: 0 to 10
    stress = np.random.randint(0, 11, n_samples)
    # Mood: 0: Happy, 1: Neutral, 2: Sad, 3: Anxious
    mood = np.random.randint(0, 4, n_samples)
    # Sleep Interruptions: 0: No, 1: Yes
    interruptions = np.random.randint(0, 2, n_samples)

    # Simple heuristic to determine "true" sleep quality
    score = (
        (sleep_duration >= 7) * 2 + 
        (sleep_duration >= 6) * 1 - 
        caffeine * 0.5 + 
        (exercise > 30) * 1 - 
        (screen_time > 60) * 1 - 
        stress * 0.3 - 
        (mood >= 2) * 1 - 
        interruptions * 1.5
    )

    def assign_quality(s):
        if s >= 1.5: return 0 # Good
        elif s >= -0.5: return 1 # Average
        else: return 2 # Poor

    quality = np.vectorize(assign_quality)(score)

    data = pd.DataFrame({
        'sleep_duration': sleep_duration,
        'caffeine': caffeine,
        'exercise': exercise,
        'screen_time': screen_time,
        'stress': stress,
        'mood': mood,
        'interruptions': interruptions,
        'quality': quality
    })

    X = data.drop('quality', axis=1)
    y = data['quality']

    print("Training RandomForest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    joblib.dump(model, 'sleep_model.pkl')
    print("Model trained and saved as sleep_model.pkl")

if __name__ == '__main__':
    train()
