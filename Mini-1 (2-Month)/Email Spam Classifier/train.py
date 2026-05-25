import pandas as pd
import numpy as np
import os
import joblib
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

# Download required NLTK data (quietly)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

def generate_sample_data():
    """Generates a small dummy dataset of spam and ham emails if no real dataset exists."""
    data = {
        'label': [
            'ham', 'ham', 'ham', 'ham', 'ham', 'ham', 'ham', 'ham', 'ham', 'ham',
            'spam', 'spam', 'spam', 'spam', 'spam', 'spam', 'spam', 'spam', 'spam', 'spam'
        ],
        'text': [
            'Hey, are we still meeting for lunch today?',
            'Please find attached the report for Q3.',
            'Let me know when you are available for a quick call.',
            'I will be late to the meeting by 10 minutes.',
            'Can you review the pull request I sent?',
            'The project deadline has been extended to next Friday.',
            'Happy birthday! Hope you have a great day.',
            'Thanks for your help with the presentation.',
            'Where did you save the new design assets?',
            'I am heading out for the day, see you tomorrow!',
            'CONGRATULATIONS! You have won a $1000 Walmart gift card. Click here to claim now!',
            'Urgent! Your account has been suspended. Please log in immediately to verify your identity.',
            'Enlarge your ... and boost your confidence by 500% with these new pills!',
            'You have been selected for a free vacation to the Bahamas. Reply to this email.',
            'Earn $5000 a week working from home! No experience needed.',
            'Your invoice #84992 is overdue. Please pay immediately or face legal action.',
            'Meet hot singles in your area tonight! Click here to chat.',
            'Invest in this new cryptocurrency and double your money in 24 hours!',
            'Exclusive offer for our lucky customers: 90% off all luxury watches!',
            'Claim your inheritance of $10,000,000 from a distant relative in Nigeria.'
        ]
    }
    df = pd.DataFrame(data)
    # create 'data' dir if missing
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/spam.csv', index=False)
    print("Created sample dataset at data/spam.csv")

def preprocess_text(text):
    """Cleans and preprocesses the text data."""
    import re
    # Lowercase
    text = text.lower()
    # Remove punctuation & numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Tokenize and remove stopwords
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    words = text.split()
    words = [lemmatizer.lemmatize(w) for w in words if w not in stop_words]
    return ' '.join(words)

def main():
    print("Initializing Email Spam Classifier Training...")
    
    # 1. Load Data
    data_path = 'data/spam.csv'
    if not os.path.exists(data_path):
        generate_sample_data()
        
    df = pd.read_csv(data_path)
    print(f"Loaded dataset with {len(df)} records.")
    
    # 2. Preprocess Data
    print("Preprocessing text data...")
    df['processed_text'] = df['text'].apply(preprocess_text)
    
    # Encode labels
    df['label_num'] = df['label'].map({'ham': 0, 'spam': 1})
    
    # 3. Feature Extraction (TF-IDF)
    print("Extracting features (TF-IDF)...")
    vectorizer = TfidfVectorizer(max_features=3000)
    X = vectorizer.fit_transform(df['processed_text']).toarray()
    y = df['label_num'].values
    
    # Save the vectorizer
    os.makedirs('models', exist_ok=True)
    joblib.dump(vectorizer, 'models/tfidf_vectorizer.pkl')
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Train Models
    models = {
        "Naive Bayes": MultinomialNB(),
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "SVM": SVC(kernel='linear', probability=True)
    }
    
    best_model = None
    best_accuracy = 0
    best_name = ""
    
    results = []
    
    print("\nTraining and Evaluating Models:")
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        results.append({'Model': name, 'Accuracy': acc})
        print(f"--- {name} ---")
        print(f"Accuracy: {acc:.4f}")
        print(classification_report(y_test, y_pred, zero_division=0))
        
        if acc >= best_accuracy:
            best_accuracy = acc
            best_model = model
            best_name = name
            
    print(f"\nBest Model: {best_name} (Accuracy: {best_accuracy:.4f})")
    
    # 5. Save the best model
    joblib.dump(best_model, 'models/best_spam_model.pkl')
    print("Saved best model to models/best_spam_model.pkl")
    
    # 6. Generate important keywords visualization (Optionally)
    if isinstance(best_model, LogisticRegression) or isinstance(best_model, MultinomialNB) or (isinstance(best_model, SVC) and best_model.kernel == 'linear'):
        if isinstance(best_model, MultinomialNB):
            coefs = best_model.feature_log_prob_[1] - best_model.feature_log_prob_[0]
        else:
            coefs = best_model.coef_[0]
            
        feature_names = vectorizer.get_feature_names_out()
        
        # Top 10 spam keywords
        top_spam_idx = np.argsort(coefs)[-10:]
        top_spam_words = [feature_names[i] for i in top_spam_idx]
        top_spam_coefs = [coefs[i] for i in top_spam_idx]
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x=top_spam_coefs, y=top_spam_words, hue=top_spam_words, palette="Reds_r", legend=False)
        plt.title('Top 10 Spam Indicating Keywords')
        plt.xlabel('Importance (Coefficient)')
        plt.ylabel('Keyword')
        plt.tight_layout()
        os.makedirs('static', exist_ok=True)
        plt.savefig('static/spam_keywords.png')
        print("Saved spam keyword visualization to static/spam_keywords.png")

if __name__ == '__main__':
    main()
