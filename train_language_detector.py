import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
import os

def train_model():
    # Load dataset
    csv_path = 'data/sentences.csv' # Make sure path matches your folder structure
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} sentences from dataset.")

    # These match the column headers we just added above:
    X = df['text']
    y = df['language']

    # Vectorize and train
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X_vec = vectorizer.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42)

    model = MultinomialNB()
    model.fit(X_train, y_train)

    # Save model and vectorizer
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/language_detector.pkl')
    joblib.dump(vectorizer, 'models/vectorizer.pkl')
    print("Model and vectorizer successfully saved to 'models/' folder!")

if __name__ == '__main__':
    train_model()