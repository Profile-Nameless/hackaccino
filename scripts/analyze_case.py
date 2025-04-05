import tensorflow as tf
import numpy as np
import json
import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

def preprocess_text(text):
    """Clean and preprocess text"""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters but keep spaces between words
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def analyze_case(case_text):
    """Analyze a legal case and identify relevant IPC sections with detailed explanation"""
    try:
        # Load the RandomForest model and its components
        with open('rf_classifier.pkl', 'rb') as f:
            clf = pickle.load(f)
        
        with open('tfidf_vectorizer.pkl', 'rb') as f:
            vectorizer = pickle.load(f)
            
        with open('label_encoder.pkl', 'rb') as f:
            label_encoder = pickle.load(f)
            
        with open('model_config.json', 'r') as f:
            config = json.load(f)
        
        # Preprocess the case text
        processed_text = preprocess_text(case_text)
        
        # Vectorize the text
        text_vector = vectorizer.transform([processed_text])
        
        # Get prediction and confidence
        prediction = clf.predict(text_vector)[0]
        probabilities = clf.predict_proba(text_vector)[0]
        
        # Get the IPC section from the prediction
        section = label_encoder.inverse_transform([prediction])[0]
        
        # Find maximum probability directly instead of using index lookup
        confidence = np.max(probabilities) * 100
        
        # Extract parties involved
        parties = extract_parties(case_text)
        
        # Create the analysis result
        result = {
            "case_text": case_text,
            "predicted_section": section,
            "confidence": confidence,
            "parties": parties,
            "explanation": get_section_explanation(section, case_text),
            "recommendations": get_recommendations(confidence)
        }
        
        return result
    except Exception as e:
        return {
            "case_text": case_text,
            "error": str(e),
            "message": "An error occurred during analysis. Please check if all model files are available."
        }

def extract_parties(text):
    parties = []
    person_pattern = r'(person\s+[A-Za-z]|[A-Za-z]+\s+[A-Za-z]+)'
    matches = re.findall(person_pattern, text, re.IGNORECASE)
    
    for match in matches:
        if match.lower() not in ['person a', 'person b', 'person c']:
            if match.lower() not in [p.lower() for p in parties]:
                parties.append(match)
    
    # Add standard parties if detected
    if re.search(r'person\s+a', text, re.IGNORECASE):
        parties.append("Person A")
    if re.search(r'person\s+b', text, re.IGNORECASE):
        parties.append("Person B")
    if re.search(r'person\s+c', text, re.IGNORECASE):
        parties.append("Person C")
    
    return parties

def get_section_explanation(section, case_text):
    # Check for special case scenarios
    if "self-defense" in case_text.lower() or "self defense" in case_text.lower():
        return get_self_defense_explanation(case_text)
    elif "minimum wage" in case_text.lower() or "labor" in case_text.lower() or "employer" in case_text.lower():
        return get_labor_law_explanation(case_text)
    
    # General section explanations
    if section == "302":
        return """Murder:
- Punishment: Death or imprisonment for life, and fine
- For proving murder, the prosecution must establish intention to cause death
- The case must show premeditation or intention to cause bodily injury sufficient to cause death"""
    
    elif section == "304":
        return """Culpable Homicide Not Amounting to Murder:
- Punishment: Imprisonment for life, or up to 10 years, and fine
- Applies when death is caused without the intention to cause death
- May apply when the act is done with the knowledge that it is likely to cause death"""
    
    elif section == "304A":
        return """Death by Negligence:
- Punishment: Imprisonment up to 2 years, or fine, or both
- Applies when death is caused by a rash or negligent act
- No intention to cause death or knowledge that the act would likely cause death"""
    
    elif section == "308":
        return """Attempt to Commit Culpable Homicide:
- Punishment: Imprisonment up to 3 years, or fine, or both
- Applies when an act is done with the intention of causing culpable homicide
- The attempt does not result in death"""
    
    elif section == "319":
        return """Hurt:
- Punishment: Imprisonment up to 1 year, or fine up to 1,000 rupees, or both
- Causing bodily pain, disease, or infirmity to any person
- Includes physical injury that causes pain"""
    
    elif section == "320":
        return """Grievous Hurt:
- Punishment: Imprisonment up to 7 years, and fine
- Includes emasculation, permanent privation of sight or hearing, fracture or dislocation of bones, or any hurt which endangers life"""
    
    elif section == "376":
        return """Rape:
- Punishment: Rigorous imprisonment for a term not less than 7 years, may extend to life, and fine
- Sexual intercourse without consent or with consent obtained under fear, threat, or false promises"""
    
    elif section == "379":
        return """Theft:
- Punishment: Imprisonment up to 3 years, or fine, or both
- Involves dishonestly taking property without consent
- Must be done with the intention to permanently deprive the owner of the property"""
    
    elif section == "392":
        return """Robbery:
- Punishment: Rigorous imprisonment up to 10 years, and fine
- Theft with the use of force or fear of force
- Includes attempt to cause death, hurt, or wrongful restraint to commit theft"""
    
    elif section == "420":
        return """Cheating and Dishonestly Inducing Delivery of Property:
- Punishment: Imprisonment up to 7 years and fine
- Involves fraudulent or deceptive practices resulting in wrongful gain
- Must show intention to defraud from the beginning"""
    
    elif section == "499":
        return """Defamation:
- Punishment: Simple imprisonment up to 2 years, or fine, or both
- Making or publishing imputations concerning any person with intent to harm their reputation
- Exceptions include truth for public good, fair comment on public conduct, etc."""
    
    elif section == "300":
        return """Definition of Murder:
- When the act is done with the intention of causing death
- When the act is done with the intention of causing bodily injury likely to cause death
- When the act is done with the knowledge that it is likely to cause death"""
    
    elif section == "100":
        return """Right of Private Defence of the Body Extending to Causing Death:
- No punishment as it is a defense, not an offense
- Applies when there is reasonable apprehension of death or grievous hurt
- The threat must be immediate and not avoidable by other means
- Force used must be proportionate to the threat"""
    
    elif section == "76":
        return """Act Done by a Person Bound by Law:
- No offense if the act is done by a person who is bound by law to do it
- The person must believe in good faith that they are bound by law to do the act"""
    
    elif section == "79":
        return """Act Done by a Person Justified by Law:
- No offense if the act is justified by law
- The person must believe in good faith that they are justified by law to do the act"""
    
    else:
        return f"Section {section} of the Indian Penal Code"

def get_self_defense_explanation(case_text):
    return """It depends on the circumstances. If Person B kills Person A in self-defense to protect himself, then Person B would NOT be considered guilty of murder or culpable homicide.

This scenario is covered under Section 100 of IPC (Right of Private Defence of the Body Extending to Causing Death):
- This allows a person to cause death in self-defense when there is reasonable apprehension of death or grievous hurt
- For self-defense to be valid, the threat must be immediate and not avoidable by other means
- The force used must be proportionate to the threat

If the case involves excessive force beyond what was necessary for self-defense, Person B may be guilty of culpable homicide not amounting to murder under Section 304.

If death occurred due to actions taken as part of legitimate self-defense, Person B would not be considered guilty at all."""

def get_labor_law_explanation(case_text):
    return """Failure to pay minimum wage is primarily a violation under labor laws, specifically:

1. The Minimum Wages Act, 1948:
   - Section 22: Imprisonment up to 6 months or fine up to 500 rupees, or both
   - Employers are legally obligated to pay at least the minimum wage as notified

2. Under the Indian Penal Code, it may be considered:
   - Section 420 (Cheating): If the employer induced work with no intention to pay
   - May also be considered as criminal breach of trust in certain circumstances

The employee can:
1. File a complaint with the Labor Commissioner
2. File a civil suit for recovery of wages
3. In egregious cases, file a criminal complaint for cheating

The exact penalty depends on:
- Whether this was a systematic practice
- Number of employees affected
- Duration of non-payment
- Whether there was deceit involved"""

def get_recommendations(confidence):
    if confidence > 80:
        return """Recommendations:
- Strong confidence in legal analysis
- Recommended to proceed with legal proceedings under the identified section
- Document all evidence thoroughly"""
    elif confidence > 60:
        return """Recommendations:
- Moderate confidence in legal analysis
- Further investigation and evidence gathering recommended
- Consider consulting a legal expert for case-specific advice"""
    else:
        return """Recommendations:
- Low confidence in automated analysis
- Consult legal experts for detailed evaluation
- Consider gathering more case details and evidence
- Complex case may involve multiple legal provisions"""

def main():
    print("\nLegal Case Analyzer")
    print("===================")
    print("\nEnter your case description below (type 'quit' to exit):")
    print("Example: 'Person A attacked Person B causing grievous injury'")
    print("Example: 'The accused stole a laptop from the office'")
    print("Example: 'Person A murdered Person B by stabbing multiple times'")
    
    while True:
        print("\n> ", end="")
        user_input = input().strip()
        
        if user_input.lower() == 'quit':
            break
            
        if not user_input:
            print("Please enter a case description.")
            continue
            
        result = analyze_case(user_input)
        
        print("\nLegal Case Analysis")
        print("==================================================")
        
        print("\nCase Description:")
        print(result.get("case_text", "N/A"))
        
        if "error" in result:
            print("\nError:", result["error"])
            print("Message:", result["message"])
            continue
            
        print("\nLegal Analysis:")
        print("--------------------------------------------------")
        
        if result.get("parties"):
            print("\nParties Involved:")
            for party in result["parties"]:
                print(f"- {party}")
        
        print(f"\nApplicable IPC Section: {result['predicted_section']} (Confidence: {result['confidence']:.1f}%)")
        
        print("\n" + result["explanation"])
        
        print("\n" + result["recommendations"])

if __name__ == "__main__":
    main() 