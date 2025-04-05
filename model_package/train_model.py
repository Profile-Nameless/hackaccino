import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import LabelEncoder
import json
import PyPDF2
import re
import os
import tensorflow as tf
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.linear_model import SGDClassifier
from sklearn.utils.class_weight import compute_class_weight
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from transformers import EarlyStoppingCallback, IntervalStrategy
from datasets import Dataset
from tqdm.auto import tqdm

# Try to import XGBoost, but continue without it if not available
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not available. Install with: pip install xgboost")
    print("Continuing without XGBoost classifier...")

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

def extract_situations_from_pdf(pdf_path):
    """Extract situation-based examples from the PDF file"""
    print(f"Extracting situations from: {pdf_path}")
    situations = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"PDF has {len(pdf_reader.pages)} pages")
            
            current_situation = {
                'text': '',
                'section': '',
                'description': '',
                'punishment': ''
            }
            
            for page_num in range(len(pdf_reader.pages)):
                print(f"Processing page {page_num + 1}")
                text = pdf_reader.pages[page_num].extract_text()
                
                # Split text into paragraphs
                paragraphs = text.split('\n\n')
                
                for para in paragraphs:
                    # Look for situation patterns and legal references
                    if (re.search(r'case|situation|example|scenario|whereas|provided that|notwithstanding', para.lower()) or
                        re.search(r'section\s+\d+', para.lower())):
                        
                        # Extract the situation text
                        current_situation['text'] = para.strip()
                        
                        # Look for IPC section references
                        section_matches = re.finditer(r'section\s+(\d+[A-Z]?)', para, re.IGNORECASE)
                        sections = []
                        for match in section_matches:
                            sections.append(match.group(1))
                        
                        if sections:
                            current_situation['section'] = ','.join(sections)
                            
                        # Look for punishment details
                        if re.search(r'punish|imprison|fine|sentence|liable', para.lower()):
                            current_situation['punishment'] = para.strip()
                        
                        # Extract description
                        if re.search(r'whoever|any person|shall be|provided that', para.lower()):
                            current_situation['description'] = para.strip()
                        
                        # If we have both text and section, save the situation
                        if current_situation['text'] and current_situation['section']:
                            situations.append(current_situation.copy())
                            current_situation = {
                                'text': '',
                                'section': '',
                                'description': '',
                                'punishment': ''
                            }
    
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return []
    
    print(f"Extracted {len(situations)} situations from the PDF")
    return situations

def create_manual_training_set():
    """Create a comprehensive and high-quality manual training set for legal classification"""
    data = [
        # Core sections with multiple variations for better training
        # Section 302 - Murder
        {
            'text': 'The accused murdered the victim with premeditation by stabbing him multiple times.',
            'section': '302',
            'description': 'Murder',
            'punishment': 'Death, or imprisonment for life, and fine'
        },
        {
            'text': 'The accused killed the victim deliberately by shooting him in the head.',
            'section': '302',
            'description': 'Murder',
            'punishment': 'Death, or imprisonment for life, and fine'
        },
        {
            'text': 'After planning for several days, the accused poisoned the victim\'s food which resulted in death.',
            'section': '302',
            'description': 'Murder',
            'punishment': 'Death, or imprisonment for life, and fine'
        },
        
        # Section 376 - Rape
        {
            'text': 'The accused committed rape against the woman despite her resistance.',
            'section': '376',
            'description': 'Punishment for rape',
            'punishment': 'Rigorous imprisonment not less than 10 years, up to life, and fine'
        },
        {
            'text': 'The accused sexually assaulted the victim against her will and consent.',
            'section': '376',
            'description': 'Punishment for rape',
            'punishment': 'Rigorous imprisonment not less than 10 years, up to life, and fine'
        },
        {
            'text': 'The perpetrator forcibly engaged in sexual intercourse with the victim without her consent.',
            'section': '376',
            'description': 'Punishment for rape',
            'punishment': 'Rigorous imprisonment not less than 10 years, up to life, and fine'
        },
        
        # Section 420 - Cheating
        {
            'text': 'The accused cheated the victim by pretending to sell land that did not belong to him.',
            'section': '420',
            'description': 'Cheating and dishonestly inducing delivery of property',
            'punishment': 'Imprisonment up to 7 years and fine'
        },
        {
            'text': 'The accused fraudulently took money from investors for a non-existent business.',
            'section': '420',
            'description': 'Cheating and dishonestly inducing delivery of property',
            'punishment': 'Imprisonment up to 7 years and fine'
        },
        {
            'text': 'The accused deceived multiple people by collecting advance payments for products never delivered.',
            'section': '420',
            'description': 'Cheating and dishonestly inducing delivery of property',
            'punishment': 'Imprisonment up to 7 years and fine'
        },
        
        # Section 325 - Grievous Hurt
        {
            'text': 'The accused assaulted the victim causing grievous harm to the eye, resulting in permanent loss of vision.',
            'section': '325',
            'description': 'Voluntarily causing grievous hurt',
            'punishment': 'Imprisonment up to 7 years and fine'
        },
        {
            'text': 'The accused attacked the victim with a rod, breaking several bones and causing permanent disability.',
            'section': '325',
            'description': 'Voluntarily causing grievous hurt',
            'punishment': 'Imprisonment up to 7 years and fine'
        },
        {
            'text': 'The accused threw acid on the victim\'s face causing permanent disfigurement.',
            'section': '325',
            'description': 'Voluntarily causing grievous hurt',
            'punishment': 'Imprisonment up to 7 years and fine'
        }
    ]
    
    # Add more sections with their variations
    more_sections = [
        # Section 498A - Domestic Violence
        {
            'text': 'The husband subjected his wife to repeated mental and physical cruelty for bringing insufficient dowry.',
            'section': '498A',
            'description': 'Cruelty by husband or relatives',
            'punishment': 'Imprisonment up to 3 years and fine'
        },
        # Section 379 - Theft
        {
            'text': 'The accused stole a mobile phone from the victim\'s pocket in a crowded market.',
            'section': '379',
            'description': 'Punishment for theft',
            'punishment': 'Imprisonment up to 3 years, or fine, or both'
        },
        # Section 304A - Death by Negligence
        {
            'text': 'The doctor\'s extreme negligence during surgery resulted in the patient\'s death.',
            'section': '304A',
            'description': 'Causing death by negligence',
            'punishment': 'Imprisonment up to 2 years, or fine, or both'
        },
        # Section 306 - Abetment of Suicide
        {
            'text': 'The accused repeatedly harassed and humiliated the victim, driving them to commit suicide.',
            'section': '306',
            'description': 'Abetment of suicide',
            'punishment': 'Imprisonment up to 10 years and fine'
        },
        # Section 307 - Attempted Murder
        {
            'text': 'The accused fired a gun at the victim with intent to kill, but the victim survived with injuries.',
            'section': '307',
            'description': 'Attempt to murder',
            'punishment': 'Imprisonment up to 10 years and fine'
        }
    ]
    data.extend(more_sections)
    
    # Generate variations for richer training data
    variations = []
    prefixes = [
        "In a recent incident, ", 
        "The court found that ", 
        "According to the police report, ",
        "The prosecution alleged that ",
        "Evidence showed that ",
        "Witnesses testified that ",
        "Investigation revealed that ",
        "The victim reported that ",
        "Court documents state that ",
        "The accused was charged with "
    ]
    
    for case in data:
        for prefix in prefixes:
            var = case.copy()
            var['text'] = f"{prefix}{case['text'].lower()}"
            variations.append(var)
    
    # Add variations to data
    data.extend(variations)
    
    return pd.DataFrame(data)

def create_comprehensive_ipc_dataset():
    """Create a comprehensive dataset combining PDF extraction and manual examples"""
    # First, get manual training data
    df_manual = create_manual_training_set()
    print(f"Created {len(df_manual)} manual training examples")
    
    # Extract situations from PDFs
    pdf_paths = [
        r"C:\Users\LENOVO\Downloads\a2023-45.pdf",  # Situation-based book
        r"C:\Users\LENOVO\Downloads\Indian20Code%20Book.pdf"  # IPC book
    ]
    
    data = {
        'text': [],
        'section': [],
        'description': [],
        'punishment': []
    }
    
    all_situations = []
    for pdf_path in pdf_paths:
        print(f"\nProcessing PDF: {pdf_path}")
        situations = extract_situations_from_pdf(pdf_path)
        all_situations.extend(situations)
        print(f"Total situations so far: {len(all_situations)}")
    
    # Add extracted situations to dataset
    print("\nProcessing extracted situations...")
    for situation in all_situations:
        # Handle multiple sections if present
        sections = situation['section'].split(',')
        for section in sections:
            # Clean section numbers
            clean_section = section.strip()
            # Skip if section is not a valid number/code
            if not re.match(r'^\d+[A-Za-z]?$', clean_section):
                continue
                
            data['text'].append(situation['text'])
            data['section'].append(clean_section)
            data['description'].append(situation['description'])
            data['punishment'].append(situation['punishment'])
    
    # Convert to DataFrame
    df_extracted = pd.DataFrame(data)
    print(f"Extracted {len(df_extracted)} examples from PDFs")
    
    # Combine datasets
    df_combined = pd.concat([df_manual, df_extracted], ignore_index=True)
    
    # Remove duplicates and clean up
    df_combined = df_combined.drop_duplicates(subset=['text', 'section'])
    df_combined = df_combined[df_combined['section'].str.strip() != '']
    
    # Focus on the most frequently appearing section numbers
    section_counts = df_combined['section'].value_counts()
    
    # Keep top 30 sections, merge the rest to 'other'
    top_sections = section_counts.head(30).index.tolist()
    print(f"\nKeeping top {len(top_sections)} sections, out of {len(section_counts)} total")
    
    df_combined['section'] = df_combined['section'].apply(
        lambda x: x if x in top_sections else 'other'
    )
    
    # Make sure our manual training set sections are preserved
    manual_sections = df_manual['section'].unique().tolist()
    for section in manual_sections:
        if section not in top_sections:
            # Ensure at least manual examples are included
            section_rows = df_combined[df_combined['section'] == 'other']
            section_rows = section_rows[section_rows['text'].isin(df_manual[df_manual['section'] == section]['text'])]
            if not section_rows.empty:
                df_combined.loc[section_rows.index, 'section'] = section
                print(f"Preserved manual section: {section}")
    
    # Balance the dataset
    section_counts = df_combined['section'].value_counts()
    max_examples_per_class = min(50, section_counts.max())  # Limit to 50 examples per class
    
    balanced_data = []
    for section, count in section_counts.items():
        if count > max_examples_per_class:
            # Take all manual examples for this section
            manual_examples = df_combined[
                (df_combined['section'] == section) & 
                (df_combined['text'].isin(df_manual['text']))
            ]
            balanced_data.append(manual_examples)
            
            # Take random examples from extracted data to reach max_examples_per_class
            other_examples = df_combined[
                (df_combined['section'] == section) & 
                (~df_combined['text'].isin(df_manual['text']))
            ]
            remaining = max_examples_per_class - len(manual_examples)
            if remaining > 0 and len(other_examples) > 0:
                balanced_data.append(other_examples.sample(
                    min(remaining, len(other_examples)), 
                    random_state=42
                ))
        else:
            # Keep all examples for underrepresented classes
            balanced_data.append(df_combined[df_combined['section'] == section])
    
    df_balanced = pd.concat(balanced_data, ignore_index=True)
    
    print(f"\nFinal dataset size: {len(df_balanced)} examples")
    print(f"Unique sections covered: {df_balanced['section'].nunique()}")
    
    return df_balanced

def preprocess_text(text):
    """Preprocess text for transformer models"""
    # Basic cleaning
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
    
    return text

def create_balanced_dataset():
    """Create a balanced dataset with manual examples"""
    # Get manual high-quality examples
    df_manual = create_manual_training_set()
    print(f"Created {len(df_manual)} manual training examples")
    
    # Make sure the dataset is balanced across sections
    sections = df_manual['section'].unique()
    min_examples = df_manual.groupby('section').size().min()
    
    if min_examples < 5:
        print(f"Warning: Some sections have fewer than 5 examples. Training may be less effective.")
    
    # Get section distribution
    section_counts = df_manual['section'].value_counts()
    print("\nSection distribution in training data:")
    for section, count in section_counts.items():
        print(f"  Section {section}: {count} examples")
    
    return df_manual

def fine_tune_transformer_model():
    """Fine-tune a transformer model for legal classification with high accuracy"""
    print("Starting legal text classification training with transformer model...")
    
    # Check for required packages
    required_packages = []
    try:
        import transformers
    except ImportError:
        required_packages.append("transformers")
    
    try:
        import datasets
    except ImportError:
        required_packages.append("datasets")
    
    if required_packages:
        print("\nMissing required packages. Please install:")
        print(f"pip install {' '.join(required_packages)}")
        raise ImportError(f"Missing required packages: {', '.join(required_packages)}")
    
    # Create balanced dataset
    df = create_balanced_dataset()
    
    # Preprocess text
    print("\nPreprocessing text...")
    df['processed_text'] = df['text'].apply(preprocess_text)
    
    # Encode labels
    label_encoder = LabelEncoder()
    df['label'] = label_encoder.fit_transform(df['section'])
    
    # Split data
    train_df, eval_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df['label']
    )
    
    print(f"\nTraining with {len(train_df)} examples, evaluating on {len(eval_df)} examples")
    print(f"Number of classes: {len(label_encoder.classes_)}")
    
    # Convert to Hugging Face Datasets
    train_dataset = Dataset.from_pandas(train_df)
    eval_dataset = Dataset.from_pandas(eval_df)
    
    # Load model and tokenizer (use legal-specific BERT if available)
    model_name = "nlpaueb/legal-bert-small-uncased"  # Legal domain-specific model
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print(f"Loaded tokenizer: {model_name}")
    except:
        print(f"Could not load {model_name}, falling back to bert-base-uncased")
        model_name = "bert-base-uncased"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Tokenize datasets
    def tokenize_function(examples):
        return tokenizer(
            examples["processed_text"], 
            padding="max_length",
            truncation=True,
            max_length=256
        )
    
    print("\nTokenizing datasets...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_eval = eval_dataset.map(tokenize_function, batched=True)
    
    # Load pretrained model
    num_labels = len(label_encoder.classes_)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=num_labels
    )
    
    # Define training arguments
    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=15,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=100,
        weight_decay=0.01,
        learning_rate=5e-5,
        logging_dir="./logs",
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        fp16=torch.cuda.is_available(),  # Use mixed precision if GPU available
        report_to="none"
    )
    
    # Define metrics computation function
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        
        accuracy = accuracy_score(labels, predictions)
        precision = precision_score(labels, predictions, average='weighted', zero_division=0)
        recall = recall_score(labels, predictions, average='weighted', zero_division=0)
        f1 = f1_score(labels, predictions, average='weighted', zero_division=0)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    
    # Create Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )
    
    # Train model
    print("\nTraining transformer model (this may take a while)...")
    trainer.train()
    
    # Evaluate model
    print("\nEvaluating model...")
    eval_results = trainer.evaluate()
    
    print(f"\nEvaluation Results:")
    for metric, value in eval_results.items():
        print(f"  {metric}: {value:.4f}")
    
    # Create a prediction function
    def predict(text):
        # Preprocess
        processed_text = preprocess_text(text)
        
        # Tokenize
        inputs = tokenizer(
            processed_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256
        )
        
        # Move to GPU if available
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
            model.cuda()
        
        # Predict
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Get predicted class and confidence
        logits = outputs.logits
        probabilities = torch.nn.functional.softmax(logits, dim=-1)
        
        predicted_class = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0][predicted_class].item()
        
        # Map back to IPC section
        section = label_encoder.inverse_transform([predicted_class])[0]
        
        return section, confidence
    
    # Save components
    print("\nSaving model components...")
    
    # Save model and tokenizer
    model_dir = "./legal_model"
    os.makedirs(model_dir, exist_ok=True)
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)
    
    # Save label encoder
    with open('label_encoder.pkl', 'wb') as f:
        pickle.dump(label_encoder, f)
    
    # Save configuration
    config = {
        'model_type': model_name,
        'num_classes': len(label_encoder.classes_),
        'classes': label_encoder.classes_.tolist(),
        'accuracy': float(eval_results.get('eval_accuracy', 0))
    }
    
    with open('model_config.json', 'w') as f:
        json.dump(config, f)
    
    # Test model with a few examples
    print("\nTesting model with examples...")
    test_cases = [
        "The accused murdered the victim by stabbing him multiple times.",
        "The accused cheated investors by collecting money for a fake scheme.",
        "The husband repeatedly harassed his wife for not bringing enough dowry."
    ]
    
    for test_case in test_cases:
        section, confidence = predict(test_case)
        print(f"\nCase: {test_case}")
        print(f"Predicted IPC Section: {section} (Confidence: {confidence:.2%})")
    
    print("\nTraining completed!")
    print(f"Final model accuracy: {eval_results.get('eval_accuracy', 0):.2%}")
    
    return model, tokenizer, label_encoder, config

def predict_section(text, model_dir="./legal_model"):
    """Make a prediction using the saved transformer model"""
    # Load components
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    
    with open('label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)
    
    # Preprocess
    processed_text = preprocess_text(text)
    
    # Tokenize
    inputs = tokenizer(
        processed_text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=256
    )
    
    # Move to GPU if available
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
        model.cuda()
    
    # Predict
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get predicted class and confidence
    logits = outputs.logits
    probabilities = torch.nn.functional.softmax(logits, dim=-1)
    
    predicted_class = torch.argmax(probabilities, dim=-1).item()
    confidence = probabilities[0][predicted_class].item()
    
    # Map back to IPC section
    section = label_encoder.inverse_transform([predicted_class])[0]
    
    return section, confidence

def predict_section_rf(text, model_path='rf_classifier.pkl', vectorizer_path='tfidf_vectorizer.pkl', encoder_path='label_encoder.pkl'):
    """Make a prediction using the RandomForest model"""
    # Load components
    with open(model_path, 'rb') as f:
        clf = pickle.load(f)
    
    with open(vectorizer_path, 'rb') as f:
        vectorizer = pickle.load(f)
    
    with open(encoder_path, 'rb') as f:
        label_encoder = pickle.load(f)
    
    # Preprocess
    processed_text = preprocess_text(text)
    
    # Vectorize
    features = vectorizer.transform([processed_text]).toarray()
    
    # Predict
    prediction = clf.predict(features)[0]
    proba = clf.predict_proba(features)[0]
    confidence = proba[prediction]
    
    # Map to IPC section
    section = label_encoder.inverse_transform([prediction])[0]
    
    return section, confidence

if __name__ == "__main__":
    try:
        # Try the advanced transformer approach first
        try:
            model, tokenizer, label_encoder, config = fine_tune_transformer_model()
            print("\nSuccessfully trained transformer model!")
        except ImportError as e:
            print(f"\nCannot use transformer model: {str(e)}")
            print("Falling back to simpler RandomForest model...")
            
            # Create a simpler dataset
            df = create_manual_training_set()
            print(f"Using {len(df)} manual training examples")
            
            # Preprocess text
            df['processed_text'] = df['text'].apply(preprocess_text)
            
            # Use basic TF-IDF vectorization
            from sklearn.feature_extraction.text import TfidfVectorizer
            vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
            X = vectorizer.fit_transform(df['processed_text']).toarray()
            
            # Encode labels
            label_encoder = LabelEncoder()
            y = label_encoder.fit_transform(df['section'])
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train RandomForest
            clf = RandomForestClassifier(
                n_estimators=200, 
                class_weight='balanced',
                n_jobs=-1,
                random_state=42
            )
            clf.fit(X_train, y_train)
            
            # Evaluate
            y_pred = clf.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"\nRandom Forest accuracy: {accuracy:.2%}")
            
            # Save components
            with open('rf_classifier.pkl', 'wb') as f:
                pickle.dump(clf, f)
            
            with open('tfidf_vectorizer.pkl', 'wb') as f:
                pickle.dump(vectorizer, f)
                
            with open('label_encoder.pkl', 'wb') as f:
                pickle.dump(label_encoder, f)
            
            # Save config
            config = {
                'model_type': 'RandomForest',
                'num_classes': len(label_encoder.classes_),
                'classes': label_encoder.classes_.tolist(),
                'accuracy': float(accuracy)
            }
            
            with open('model_config.json', 'w') as f:
                json.dump(config, f)
                
            print("\nTraining completed! Model saved.")
            print("You can now use 'predict_section_rf()' for predictions.")
            
            # Define simple prediction function
            def predict_section_rf(text):
                processed_text = preprocess_text(text)
                features = vectorizer.transform([processed_text]).toarray()
                prediction = clf.predict(features)[0]
                proba = clf.predict_proba(features)[0]
                confidence = proba[prediction]
                section = label_encoder.inverse_transform([prediction])[0]
                return section, confidence
                
            # Test with example
            test_case = "The accused murdered the victim by stabbing him multiple times."
            section, confidence = predict_section_rf(test_case)
            print(f"\nTest case: {test_case}")
            print(f"Predicted IPC section: {section} (confidence: {confidence:.2%})")
            
    except Exception as e:
        print(f"Error during training: {str(e)}")
        import traceback
        traceback.print_exc() 