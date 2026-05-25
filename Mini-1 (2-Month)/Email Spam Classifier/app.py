from flask import Flask, request, jsonify, render_template
import joblib
import os
import datetime
import sqlite3
import numpy as np
from train import preprocess_text
import re

app = Flask(__name__)

# Load Model and Vectorizer globally
MODEL_PATH = 'models/best_spam_model.pkl'
VECTORIZER_PATH = 'models/tfidf_vectorizer.pkl'
DB_PATH = 'spam_history.db'

model = None
vectorizer = None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_snippet TEXT,
            prediction TEXT,
            confidence REAL,
            color TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_resources():
    global model, vectorizer
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        print("Model and vectorizer loaded successfully.")
    else:
        print("Model or vectorizer not found. Please run train.py first.")

@app.before_request
def startup():
    if model is None or vectorizer is None:
        load_resources()

def get_word_importance(text, model, vectorizer):
    """Calculates spam contribution of individual words for explainability."""
    try:
        # Check if the model has coefficients (Linear SVM, LogReg, NB)
        coefs = None
        if hasattr(model, 'coef_'):
            coefs = model.coef_[0]
        elif hasattr(model, 'feature_log_prob_'):
            coefs = model.feature_log_prob_[1] - model.feature_log_prob_[0]
            
        if coefs is None:
            return []
            
        feature_names = vectorizer.get_feature_names_out()
        vocab = vectorizer.vocabulary_
        
        words = re.findall(r'\b\w+\b', text.lower())
        importance_list = []
        seen = set()
        
        for w in words:
            if w in vocab and w not in seen:
                idx = vocab[w]
                score = coefs[idx]
                # If score > 0, it pushes towards spam. We only highlight strong spam indicators.
                if score > 0.5:
                    importance_list.append({'word': w, 'score': float(score)})
                seen.add(w)
                
        # Sort by importance
        importance_list.sort(key=lambda x: x['score'], reverse=True)
        return importance_list[:10] # Top 10 spammy words
    except Exception as e:
        print("Error calculating importance:", e)
        return []

@app.route('/')
def home():
    stats = {}
    if os.path.exists('static/spam_keywords.png'):
        stats['has_viz'] = True
    else:
        stats['has_viz'] = False
        
    return render_template('index.html', stats=stats)

@app.route('/predict', methods=['POST'])
def predict():
    if model is None or vectorizer is None:
        return jsonify({'error': 'Model not trained. Run train.py first.'}), 500
        
    data = request.get_json()
    email_text = data.get('text', '')
    
    if not email_text.strip():
        return jsonify({'error': 'Empty email text'}), 400
        
    # Preprocess
    processed_text = preprocess_text(email_text)
    
    # Vectorize
    features = vectorizer.transform([processed_text]).toarray()
    
    # Predict
    prediction = model.predict(features)[0]
    
    # Provide probabilities if model supports it
    confidence = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(features)[0]
        confidence = round(float(proba[prediction]) * 100, 2)
    elif hasattr(model, "decision_function"):
        decision = model.decision_function(features)[0]
        confidence = round(1 / (1 + 2.718 ** -decision) * 100, 2)
        if prediction == 0:
            confidence = 100 - confidence
    
    result = 'Spam' if prediction == 1 else 'Legitimate (Ham)'
    color = 'error' if prediction == 1 else 'success'
    
    # Explainability Features
    important_words = get_word_importance(email_text, model, vectorizer)
    
    timestamp = datetime.datetime.now().strftime("%b %d, %H:%M:%S")
    snippet = email_text[:60] + '...' if len(email_text) > 60 else email_text
    
    # Save to SQLite DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO history (text_snippet, prediction, confidence, color, timestamp) VALUES (?, ?, ?, ?, ?)",
        (snippet, result, confidence, color, timestamp)
    )
    conn.commit()
    inserted_id = c.lastrowid
    conn.close()
    
    record = {
        'id': inserted_id,
        'text_snippet': snippet,
        'prediction': result,
        'confidence': confidence,
        'color': color,
        'timestamp': timestamp
    }
    
    return jsonify({
        'prediction': result,
        'confidence': confidence,
        'color': color,
        'record': record,
        'highlights': important_words
    })

@app.route('/history', methods=['GET'])
def get_history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY id DESC LIMIT 15")
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in rows])

@app.route('/stats', methods=['GET'])
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM history")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM history WHERE color='error'")
    spam = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM history WHERE color='success'")
    ham = c.fetchone()[0]
    conn.close()
    
    return jsonify({
        'total': total,
        'spam': spam,
        'ham': ham
    })

@app.route('/clear', methods=['POST'])
def clear_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM history")
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    init_db()
    load_resources()
    app.run(debug=True, port=5000)
