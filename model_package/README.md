# Legal Case Analysis Model Package

This package contains a machine learning model and supporting scripts for analyzing legal cases based on the Indian Penal Code (IPC).

## Contents

- `analyze_case.py` - Main script for interactive case analysis
- `test_model.py` - Script for testing the model with different inputs
- `train_model.py` - Script for training or retraining the model
- `predict_ipc.py` - Utility script for predicting IPC sections from input text
- `model_config.json` - Configuration file for the model
- `rf_classifier.pkl` - Trained RandomForest model for classification
- `tfidf_vectorizer.pkl` - TF-IDF vectorizer for text preprocessing
- `label_encoder.pkl` - Label encoder for mapping classes to IPC sections
- `requirements.txt` - Required Python packages
- `test_input.txt` - Sample input for testing
- `ipc_sec_dataset.csv` - Dataset used for training the model

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Make sure all model files are in the same directory as the scripts.

## Usage

### Interactive Analysis

Run the analyze_case.py script to interactively analyze legal cases:

```
python analyze_case.py
```

Example inputs:
- "Person A hit Person B because Person B robbed Person A"
- "The accused stole a laptop from the office"
- "Person A murdered Person B by stabbing multiple times"
- "Employer failed to pay minimum wage"

### Testing with Pre-defined Examples

Run the test_model.py script to test the model with built-in examples:

```
python test_model.py
```

### Direct Command Line Testing

Test a specific case directly from the command line:

```
python test_model.py "The accused stole a laptop from the office"
```

### Retraining the Model

If you want to retrain the model with new data:

1. Update the ipc_sec_dataset.csv file with new examples
2. Run the training script:
   ```
   python train_model.py
   ```

## Model Output

The model provides:
- The identified IPC section
- Confidence score
- Detailed explanations of the applicable section
- Special considerations for cases like self-defense or labor law
- Recommendations based on confidence level

## Notes

- The model was trained on a specific dataset of legal cases and IPC sections
- For complex legal cases, consult with a legal professional
- The analysis is meant to be a guide, not definitive legal advice 