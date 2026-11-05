import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def train_model():
    # 1. Load dataset
    data_path = os.path.join('data', 'sentences.csv')
    if not os.path.exists(data_path):
        print("Error: data/sentences.csv not found. Please create it first.")
        return
    
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} sentences from dataset.")
    
    X = df['text']
    y = df['label']
    
    # 2. Split into 80% train and 20% test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Vectorize text using character n-grams (ideal for short phrases & local languages)
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # 4. Train Multinomial Naive Bayes model
    model = MultinomialNB()
    model.fit(X_train_vec, y_train)
    
    # 5. Evaluate accuracy
    y_pred = model.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nLanguage Detector Model Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # 6. Save model and vectorizer
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/language_detector.pkl')
    joblib.dump(vectorizer, 'models/vectorizer.pkl')
    print("\nModel and vectorizer successfully saved to 'models/' folder!")

if __name__ == '__main__':
    train_model()