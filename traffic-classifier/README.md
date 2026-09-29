# AI-Based Encrypted Traffic Classification Pipeline

An end-to-end, reproducible XGBoost multiclass classification pipeline designed to classify encrypted network flows (such as IPsec VPN traffic) into fine-grained application categories based on statistical flow behavior features.

---

## 1. Dataset Overview
- **Source File**: `consolidated_traffic_data.csv`
- **Total Raw Samples**: 59,706 rows
- **Total Attributes**: 24 columns (23 flow features + 1 target class column)
- **Missing / Infinite Values**: 0 missing values, 0 infinite values.
- **De-duplication**: 18,719 exact duplicate rows (arising from zero-duration/single-packet probe flows) were removed to prevent data leakage across splits, leaving **40,987 clean flow samples**.

---

## 2. Target Variable & Classes
Target Column: `traffic_type`

The dataset contains **14 actual target classes** representing specific traffic and VPN application types:

| Target Class | Description |
| :--- | :--- |
| `BROWSING` | Standard Web Browsing (HTTP/HTTPS) |
| `VPN-BROWSING` | Web Browsing over VPN Tunnel |
| `VOIP` | Voice over IP (Calls/Audio) |
| `VPN-VOIP` | Voice over IP over VPN |
| `FT` | Standard File Transfer (FTP/SFTP) |
| `VPN-FT` | File Transfer over VPN |
| `P2P` | Peer-to-Peer Traffic (BitTorrent/eDonkey) |
| `VPN-P2P` | Peer-to-Peer Traffic over VPN |
| `CHAT` | Instant Messaging / Chat Traffic |
| `VPN-CHAT` | Instant Messaging over VPN |
| `MAIL` | Email Protocol Traffic (SMTP/IMAP/POP3) |
| `VPN-MAIL` | Email Traffic over VPN |
| `STREAMING` | Video / Audio Streaming Traffic |
| `VPN-STREAMING` | Video / Audio Streaming over VPN |

---

## 3. Features Used
All 23 flow metrics extracted from packet captures are retained as numerical predictor variables:

| Feature Name | Description |
| :--- | :--- |
| `duration` | Total duration of the network flow (in microseconds) |
| `total_fiat` | Sum of Forward Inter-Arrival Times |
| `total_biat` | Sum of Backward Inter-Arrival Times |
| `min_fiat`, `max_fiat`, `mean_fiat` | Minimum, Maximum, and Mean Forward Inter-Arrival Times |
| `min_biat`, `max_biat`, `mean_biat` | Minimum, Maximum, and Mean Backward Inter-Arrival Times |
| `flowPktsPerSecond` | Packet transmission rate (packets/sec) |
| `flowBytesPerSecond` | Byte throughput rate (bytes/sec) |
| `min_flowiat`, `max_flowiat`, `mean_flowiat`, `std_flowiat` | Overall flow inter-arrival time statistics |
| `min_active`, `mean_active`, `max_active`, `std_active` | Active flow period duration statistics |
| `min_idle`, `mean_idle`, `max_idle`, `std_idle` | Idle flow period duration statistics |

---

## 4. Column Audit & Data Leakage Prevention
- **Dropped Identifier Columns**: None present in the raw CSV. Explicit checks verified the absence of IP addresses (`src_ip`, `dst_ip`), MAC addresses, Flow IDs, or timestamps.
- **De-duplication**: 18,719 exact feature-and-label duplicate rows were removed. In network flow datasets, probe flows with identical 0-duration signatures can skew validation and cause data leakage if present in both train and test splits.
- **Sentinel Values**: Value `-1` in min/max/active/idle features represents undefined periods (e.g., single-packet flows). XGBoost naturally handles numerical sentinel values without artificial imputation.

---

## 5. Train / Validation / Test Splitting
- **Splitting Strategy**: Stratified random split with fixed seed (`random_state=42`).
- **Distribution**:
  - **Training Set (70%)**: 28,690 samples
  - **Validation Set (15%)**: 6,148 samples (used for XGBoost early stopping)
  - **Test Set (15%)**: 6,149 samples (untouched until final evaluation)

---

## 6. Model Training Procedure
- **Model**: `XGBClassifier` (`xgboost`)
- **Objective**: `multi:softprob`
- **Evaluation Metric**: `mlogloss`
- **Hyperparameters**:
  - `n_estimators`: 400
  - `max_depth`: 8
  - `learning_rate`: 0.08
  - `subsample`: 0.8
  - `colsample_bytree`: 0.8
  - `early_stopping_rounds`: 20
  - `tree_method`: `hist`

---

## 7. How to Run the Pipeline

### Interactive Demo Notebook
Open `notebooks/XGBoost_Preprocessing_Training_Demo.ipynb` in Jupyter or VS Code and run the cells from top to bottom. It walks through the dataset, preprocessing, training, and held-out test evaluation. It expects `consolidated_traffic_data.csv` in the repository root and saves demo outputs separately under `traffic-classifier/demo_artifacts/`.

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Inspect Dataset
```bash
python src/inspect_dataset.py --data-path ../consolidated_traffic_data.csv
```
Produces `reports/dataset_report.json`.

### Step 3: Preprocess Dataset
```bash
python src/preprocess.py --data-path ../consolidated_traffic_data.csv
```
Creates dataset splits in `data/processed/processed_data.npz`, label encoder in `models/label_encoder.joblib`, and schema config in `models/feature_schema.json`.

### Step 4: Train XGBoost Model
```bash
python src/train.py
```
Saves model artifacts to `models/xgboost_traffic_classifier.json` and metadata to `models/model_metadata.json`.

### Step 5: Evaluate on Test Set
```bash
python src/evaluate.py
```
Generates performance metrics, `reports/classification_report.json`, `reports/confusion_matrix.png`, `reports/feature_importance.png`, and optional `reports/shap_summary.png`.

### Step 6: Run Sample Inference
```bash
python src/predict.py --sample
```
Or with custom input JSON:
```bash
python src/predict.py --input sample.json
```

---

## 8. Expected Input Schema (JSON Format for Inference)
```json
{
  "duration": 143704195.0,
  "total_fiat": 143704195.0,
  "total_biat": 42106019.0,
  "min_fiat": 64.0,
  "min_biat": 20.0,
  "max_fiat": 101572528.0,
  "max_biat": 382847.0,
  "mean_fiat": 101674.9,
  "mean_biat": 53919.1,
  "flowPktsPerSecond": 8.54,
  "flowBytesPerSecond": 1610.0,
  "min_flowiat": 19.0,
  "max_flowiat": 101572528.0,
  "mean_flowiat": 117473.7,
  "std_flowiat": 137463.7,
  "min_active": -1.0,
  "mean_active": 0.0,
  "max_active": -1.0,
  "std_active": 0.0,
  "min_idle": -1.0,
  "mean_idle": 0.0,
  "max_idle": 101572528.0,
  "std_idle": 0.0
}
```

---

## 9. Limitations & Conceptual Scope
1. **Application Granularity**: The model predicts general traffic classes (e.g., `STREAMING`, `VOIP`, `BROWSING`). It does **not** identify specific service providers (such as YouTube, Netflix, or Skype) unless explicit sub-labels are provided in the training data.
2. **Encrypted Flow Dynamics**: Statistical features reflect flow timing and volume. If traffic patterns change due to aggressive packet padding or obfuscation, retrain with padded flow samples.
