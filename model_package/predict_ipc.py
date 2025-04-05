import json
import numpy as np
from keras.models import load_model
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder
import re

def load_model_components():
    """Load the trained model and its components"""
    model = load_model('text_prediction_model.keras')
    
    with open('vectorizer.json', 'r') as f:
        vectorizer_data = json.load(f)
    
    with open('label_encoder_classes.json', 'r') as f:
        label_encoder_classes = json.load(f)
    
    vectorizer = CountVectorizer(max_features=vectorizer_data['max_features'])
    vectorizer.vocabulary_ = {k: int(v) for k, v in vectorizer_data['vocabulary_'].items()}
    
    label_encoder = LabelEncoder()
    label_encoder.classes_ = np.array(label_encoder_classes)
    
    return model, vectorizer, label_encoder

def extract_parties(text):
    """Extract different parties involved in the incident"""
    parties = []
    # Look for patterns like "person A", "person B", etc.
    party_matches = re.finditer(r'person\s+([A-Za-z])', text, re.IGNORECASE)
    for match in party_matches:
        parties.append(f"person {match.group(1)}")
    return parties

def predict_ipc_sections(input_text):
    """Predict IPC sections for complex scenarios"""
    model, vectorizer, label_encoder = load_model_components()
    
    # Extract parties involved
    parties = extract_parties(input_text)
    if not parties:
        parties = ["attacker", "victim"]  # Default parties if none specified
    
    # Prepare input
    X = vectorizer.transform([input_text])
    
    # Get predictions
    predictions = model.predict(X)
    predicted_indices = np.argsort(predictions[0])[-3:][::-1]  # Get top 3 predictions
    
    # Decode predictions
    results = []
    for idx in predicted_indices:
        if predictions[0][idx] > 0.1:  # Confidence threshold
            section_data = json.loads(label_encoder.classes_[idx])
            for section in section_data:
                if section["section"]:  # Only include sections that apply
                    results.append({
                        "party": section["party"],
                        "section": section["section"],
                        "reason": section["reason"],
                        "confidence": float(predictions[0][idx])
                    })
    
    return results

def main():
    import sys
    if len(sys.argv) > 1:
        input_text = sys.argv[1]
    else:
        input_text = input("Enter the incident description: ")
    
    predictions = predict_ipc_sections(input_text)
    
    print("\nPredicted IPC Sections:")
    print("----------------------")
    for pred in predictions:
        print(f"\nFor {pred['party']}:")
        print(f"Section: {pred['section']}")
        print(f"Reason: {pred['reason']}")
        print(f"Confidence: {pred['confidence']:.2%}")

if __name__ == "__main__":
    main()

