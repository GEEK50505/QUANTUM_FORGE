# ML Data Quality & Governance Guide

## Overview

Quantum Forge implements **enterprise-grade data quality assurance** specifically designed for AI/ML model training. This ensures that all data stored in Supabase meets strict quality standards for reproducible, reliable machine learning models.

## 🎯 Core Principles

### 1. **Multi-Dimensional Quality Assessment**

Data quality is evaluated across five key dimensions:

```
┌─────────────────────────────────────────────┐
│        OVERALL QUALITY SCORE (0-1)          │
├─────────────────────────────────────────────┤
│ • Completeness (25%)    [non-null fields]   │
│ • Validity     (35%)    [value ranges]      │
│ • Consistency  (30%)    [cross-field rules] │
│ • Uniqueness   (10%)    [no duplicates]     │
│ • Accuracy     (via)    [confidence int.]   │
└─────────────────────────────────────────────┘
```

### 2. **ML-Ready Certification**

Data must meet a minimum quality threshold before it's usable for training:

- **Quality Score ≥ 0.80** (80% threshold)
- **No failed validations** (all constraints met)
- **Completeness ≥ 0.70** (at least 70% of fields populated)
- **Not flagged as outlier** (or outlier documented with reason)

### 3. **Full Data Provenance Tracking**

Every data point knows its origin:

```
Data Point → Lineage → Software Version → Algorithm Version → Git Commit
                          ↓
                    Processing Parameters
                          ↓
                    Validation Timestamp
                          ↓
                    Approval Status
```

## 📊 Database Schema: Quality Tables

### 1. **data_quality_metrics** - Quality Score Storage

```sql
CREATE TABLE data_quality_metrics (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(50),       -- "calculations", "molecules", "properties"
    entity_id INTEGER,             -- Reference to actual data
    
    -- Quality Scores (0-1)
    completeness_score DOUBLE PRECISION,
    validity_score DOUBLE PRECISION,
    consistency_score DOUBLE PRECISION,
    uniqueness_score DOUBLE PRECISION,
    overall_quality_score DOUBLE PRECISION,
    
    -- Quality Flags
    is_outlier BOOLEAN,            -- Statistical outlier detected
    is_suspicious BOOLEAN,         -- Unusual but not outlier
    has_missing_values BOOLEAN,
    failed_validation BOOLEAN,
    
    -- Data Issues
    missing_fields TEXT[],         -- ["dipole_moment", "charges"]
    data_source VARCHAR(100),      -- "xTB_6.7.1"
    validation_method VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE
);
```

**Query Examples:**

```python
# Find all high-quality data ready for ML
high_quality = client.get(
    "data_quality_metrics",
    filters={"overall_quality_score": (0.8, 1.0)},
    order_by="overall_quality_score.desc"
)

# Find problematic data
problematic = client.get(
    "data_quality_metrics",
    filters={"failed_validation": True}
)

# Track quality by data source
xtb_quality = client.get(
    "data_quality_metrics",
    filters={"data_source": "xTB_6.7.1"},
    select="overall_quality_score"
)
```

### 2. **data_lineage** - Provenance Tracking

```sql
CREATE TABLE data_lineage (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(50),       -- "calculations"
    entity_id INTEGER,             -- Calculation ID
    
    -- Source Information
    source_type VARCHAR(50),       -- "computation", "transformation"
    source_reference TEXT,         -- File path, URL, or ID
    
    -- Versioning
    software_version VARCHAR(100), -- "xTB_6.7.1"
    algorithm_version VARCHAR(100),-- "gfn2-xtb"
    schema_version INTEGER,        -- Track schema changes
    
    -- Processing
    processing_parameters JSONB,   -- {"method": "gfn2", "solvent": "water"}
    processing_time_seconds DOUBLE PRECISION,
    
    -- Approval
    validated_by VARCHAR(100),
    validation_timestamp TIMESTAMP WITH TIME ZONE,
    approved_for_ml BOOLEAN,       -- ✓ ML-ready flag
    
    -- Dependencies
    depends_on_ids INTEGER[]       -- Parent entity IDs
);
```

**Query Example - Track data provenance:**

```python
# Get lineage for a calculation
lineage = client.get(
    "data_lineage",
    filters={
        "entity_type": "calculations",
        "entity_id": 42
    }
)
# Shows: xTB version, method used, parameters, approval status, git commit

# Find all data approved for ML
approved_data = client.get(
    "data_lineage",
    filters={"approved_for_ml": True}
)
```

### 3. **ml_dataset_splits** - Train/Test/Validation Management

```sql
CREATE TABLE ml_dataset_splits (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    
    -- Dataset Info
    dataset_name VARCHAR(255),     -- "benzene_calculations_v2"
    version INTEGER DEFAULT 1,
    
    -- Split Configuration
    train_fraction DOUBLE PRECISION,       -- 0.7 (70%)
    validation_fraction DOUBLE PRECISION,  -- 0.15 (15%)
    test_fraction DOUBLE PRECISION,        -- 0.15 (15%)
    
    -- Statistics
    total_samples INTEGER,
    train_samples INTEGER,
    validation_samples INTEGER,
    test_samples INTEGER,
    
    -- Stratification & Reproducibility
    stratified_by VARCHAR(100),    -- "band_gap"
    random_seed INTEGER,           -- For exact reproducibility
    
    -- Filter Criteria
    filter_criteria JSONB,         -- {"min_gap": 0.5, "max_gap": 5.0}
    quality_threshold DOUBLE PRECISION  -- 0.8 (only quality data)
);
```

**Create dataset with 70/15/15 split:**

```python
# Create balanced dataset
dataset = client.insert("ml_dataset_splits", {
    "dataset_name": "water_calculations_balanced",
    "version": 1,
    "train_fraction": 0.7,
    "validation_fraction": 0.15,
    "test_fraction": 0.15,
    "stratified_by": "band_gap",
    "random_seed": 42,  # Reproducible split
    "filter_criteria": {
        "min_gap": 0.5,
        "max_gap": 10.0,
        "element": "water"
    },
    "quality_threshold": 0.80  # Only high-quality data
})
```

### 4. **ml_dataset_assignments** - Link Data to Splits

```sql
CREATE TABLE ml_dataset_assignments (
    id BIGSERIAL PRIMARY KEY,
    calculation_id INTEGER,
    dataset_split_id INTEGER,
    
    -- Assignment Type
    split_type VARCHAR(20),  -- "train", "validation", "test"
    
    -- Quality Checks
    quality_checked BOOLEAN,
    quality_check_timestamp TIMESTAMP WITH TIME ZONE,
    quality_issues TEXT[],
    
    -- Cross-Validation
    fold_number INTEGER  -- For k-fold cross-validation
);
```

**Query data split assignments:**

```python
# Get training data for a dataset
training_set = client.get(
    "ml_dataset_assignments",
    filters={
        "dataset_split_id": 1,
        "split_type": "train"
    }
)

# Get validation fold 3 only
val_fold_3 = client.get(
    "ml_dataset_assignments",
    filters={
        "dataset_split_id": 1,
        "split_type": "validation",
        "fold_number": 3
    }
)
```

### 5. **feature_extraction_log** - ML Feature Versioning

```sql
CREATE TABLE feature_extraction_log (
    id BIGSERIAL PRIMARY KEY,
    
    -- Feature Set Info
    feature_set_name VARCHAR(255),    -- "molecular_descriptors"
    feature_set_version VARCHAR(50),  -- "v1.0", "v2.1-beta"
    
    -- Extraction Details
    extraction_method VARCHAR(100),   -- "molecular_descriptors"
    feature_count INTEGER,            -- Number of features
    feature_names TEXT[],             -- ["gap", "dipole", "homo_energy"]
    
    -- Applied To
    calculation_ids INTEGER[],
    dataset_split_id INTEGER,
    
    -- Quality Metrics
    missing_features_count INTEGER,
    invalid_features_count INTEGER,
    feature_correlation JSONB,        -- {"gap": {"dipole": 0.75}}
    
    -- Versioning
    depends_on_version VARCHAR(100),  -- Previous version
    changes_from_previous TEXT,
    
    extraction_timestamp TIMESTAMP WITH TIME ZONE
);
```

### 6. **model_training_log** - ML Model Tracking

```sql
CREATE TABLE model_training_log (
    id BIGSERIAL PRIMARY KEY,
    
    -- Model Info
    model_name VARCHAR(255),          -- "gap_predictor_v1"
    model_version VARCHAR(50),        -- "1.0.0"
    model_type VARCHAR(100),          -- "neural_network"
    
    -- Dataset & Features
    dataset_split_id INTEGER,         -- Which dataset was used
    feature_extraction_id BIGINT,     -- Which features were used
    
    -- Training Parameters
    hyperparameters JSONB,  -- {"learning_rate": 0.001, "batch_size": 32}
    training_config JSONB,  -- {"optimizer": "adam", "loss": "mse"}
    
    -- Results
    train_loss DOUBLE PRECISION,
    validation_loss DOUBLE PRECISION,
    test_loss DOUBLE PRECISION,
    
    train_r2 DOUBLE PRECISION,
    validation_r2 DOUBLE PRECISION,
    test_r2 DOUBLE PRECISION,
    
    train_mae DOUBLE PRECISION,
    validation_mae DOUBLE PRECISION,
    test_mae DOUBLE PRECISION,
    
    -- Reproducibility
    code_commit_hash VARCHAR(50),     -- Git commit
    framework VARCHAR(50),            -- "pytorch", "tensorflow"
    framework_version VARCHAR(50),
    
    training_duration_seconds DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE
);
```

**Query model performance:**

```python
# Get best performing models by test R²
best_models = client.get(
    "model_training_log",
    filters={"test_r2": (0.85, 1.0)},
    order_by="test_r2.desc"
)

# Track performance across versions
versions = client.get(
    "model_training_log",
    filters={"model_name": "gap_predictor"},
    order_by="created_at.desc"
)
```

### 7. **data_anomalies** - Outlier & Anomaly Tracking

```sql
CREATE TABLE data_anomalies (
    id BIGSERIAL PRIMARY KEY,
    
    -- Anomaly Info
    anomaly_type VARCHAR(50),  -- "outlier", "duplicate", "impossible_value"
    severity VARCHAR(20),      -- "low", "medium", "high", "critical"
    
    -- Detection
    detection_method VARCHAR(100),     -- "iqr", "isolation_forest", "statistical"
    detected_entity_type VARCHAR(50),
    detected_entity_ids INTEGER[],
    
    -- Statistical Details
    detected_value DOUBLE PRECISION,
    expected_value_range JSONB,        -- {"min": 0.5, "max": 5.0, "mean": 2.5}
    z_score DOUBLE PRECISION,
    percentile DOUBLE PRECISION,
    
    -- Resolution
    action_taken VARCHAR(100),  -- "flagged", "excluded", "corrected"
    resolution_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE
);
```

## 🔍 Data Quality Assessment in Python

### Basic Quality Check

```python
from backend.app.db.data_quality import QualityAssessor, QualityMetrics

assessor = QualityAssessor()

# Assess a calculation result
calc_data = {
    'energy': -10.5243,
    'gap': 2.34,
    'homo': -7.2,
    'lumo': -4.86,
    'dipole_moment': 1.85,
    'forces': 0.0012
}

metrics = assessor.assess_calculation_quality(
    calc_data=calc_data,
    calc_id=42,
    computation_metadata={'xtb_version': '6.7.1'}
)

print(f"Overall Quality Score: {metrics.overall_quality_score:.2%}")
# Output: Overall Quality Score: 94.32%

print(f"ML Ready: {not metrics.is_outlier and metrics.overall_quality_score > 0.8}")
# Output: ML Ready: True
```

### Outlier Detection

```python
import numpy as np

# Detect outliers in band gap values
band_gaps = np.array([1.2, 1.5, 1.3, 1.4, 15.0, 1.6, 1.4])  # 15.0 is outlier

outlier_mask, bounds = assessor.detect_outliers_iqr(band_gaps)

print(f"Outliers detected: {np.where(outlier_mask)[0].tolist()}")
# Output: Outliers detected: [4]

print(f"Valid range: {bounds['lower_bound']:.2f} to {bounds['upper_bound']:.2f}")
# Output: Valid range: 0.35 to 2.65
```

### Confidence Intervals

```python
from backend.app.db.data_quality import ConfidenceIntervalCalculator

calculator = ConfidenceIntervalCalculator()

# Compute 95% confidence interval for energies
energies = np.array([-10.52, -10.53, -10.51, -10.54, -10.52])

ci = calculator.compute_bootstrap_ci(energies, confidence=0.95, n_bootstrap=1000)

print(f"Energy: {ci['mean']:.4f} ± {(ci['upper'] - ci['lower'])/2:.4f}")
# Output: Energy: -10.5240 ± 0.0125
```

## 📋 ML Dataset Workflow

### Step 1: Create ML Dataset

```python
# Define a dataset split for model training
dataset = client.insert("ml_dataset_splits", {
    "dataset_name": "quantum_properties_v2",
    "version": 2,
    "train_fraction": 0.70,
    "validation_fraction": 0.15,
    "test_fraction": 0.15,
    "stratified_by": "band_gap",
    "random_seed": 42,
    "filter_criteria": {
        "quality_threshold": 0.80,
        "min_molecules": 3,
        "max_molecules": 50
    }
})

dataset_id = dataset[0]['id']
```

### Step 2: Assign Data to Splits

```python
# Get all high-quality calculations
quality_calcs = client.get(
    "data_quality_metrics",
    filters={"overall_quality_score": (0.80, 1.0)},
    select="entity_id"
)

calculation_ids = [q['entity_id'] for q in quality_calcs]

# Randomly assign to train/val/test (with seed for reproducibility)
np.random.seed(42)
n = len(calculation_ids)
shuffled = np.random.permutation(calculation_ids)

train_idx = int(0.7 * n)
val_idx = int(0.85 * n)

assignments = []
for i, calc_id in enumerate(shuffled):
    if i < train_idx:
        split_type = "train"
    elif i < val_idx:
        split_type = "validation"
    else:
        split_type = "test"
    
    assignments.append({
        "calculation_id": calc_id,
        "dataset_split_id": dataset_id,
        "split_type": split_type
    })

# Bulk insert
client.insert_many("ml_dataset_assignments", assignments)
```

### Step 3: Extract Features

```python
# Log feature extraction
feature_log = client.insert("feature_extraction_log", {
    "feature_set_name": "quantum_descriptors",
    "feature_set_version": "v1.0",
    "extraction_method": "molecular_descriptors",
    "feature_count": 7,
    "feature_names": ["gap", "homo", "lumo", "dipole", "energy", "forces", "charges"],
    "calculation_ids": calculation_ids,
    "dataset_split_id": dataset_id,
    "extraction_timestamp": datetime.now().isoformat()
})
```

### Step 4: Train Model

```python
# Log model training
training = client.insert("model_training_log", {
    "model_name": "gap_predictor",
    "model_version": "1.0.0",
    "model_type": "neural_network",
    "dataset_split_id": dataset_id,
    "feature_extraction_id": feature_log[0]['id'],
    "hyperparameters": {
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100
    },
    "train_loss": 0.0234,
    "validation_loss": 0.0301,
    "test_loss": 0.0289,
    "train_r2": 0.945,
    "validation_r2": 0.931,
    "test_r2": 0.938,
    "train_mae": 0.12,
    "validation_mae": 0.18,
    "test_mae": 0.17,
    "code_commit_hash": "abc123def456",
    "framework": "pytorch",
    "framework_version": "2.0.0"
})
```

## 🚀 Integration with xTB Runner

### Modified xTB Runner with Quality Assessment

```python
from backend.app.db.supabase_client import get_supabase_client
from backend.app.db.data_quality import QualityAssessor

client = get_supabase_client()
assessor = QualityAssessor()

def run_xtb_with_quality(molecule_id: int, smiles: str) -> Dict:
    """Run xTB calculation and store with quality metrics"""
    
    # 1. Run xTB calculation
    calc_result = run_xtb(smiles)  # Your existing xTB wrapper
    
    # 2. Assess quality
    metrics = assessor.assess_calculation_quality(
        calc_data=calc_result,
        calc_id=molecule_id,
        computation_metadata={'xtb_version': '6.7.1'}
    )
    
    # 3. Store calculation
    calc = client.insert("calculations", {
        "molecule_id": molecule_id,
        "energy": calc_result['energy'],
        "gap": calc_result['gap'],
        "homo": calc_result['homo'],
        "lumo": calc_result['lumo'],
        "quality_score": metrics.overall_quality_score,
        "is_ml_ready": metrics.overall_quality_score > 0.8
    })
    
    # 4. Store quality metrics
    client.insert("data_quality_metrics", metrics.to_dict())
    
    # 5. Store lineage
    client.insert("data_lineage", {
        "entity_type": "calculations",
        "entity_id": calc[0]['id'],
        "source_type": "computation",
        "software_version": "xTB_6.7.1",
        "algorithm_version": "gfn2-xtb",
        "processing_parameters": {"method": "gfn2", "opt_level": "normal"},
        "approved_for_ml": metrics.overall_quality_score > 0.8
    })
    
    return calc[0]
```

## ✅ Quality Checklist for ML Models

Before using data for ML model training:

- [ ] **Data Quality Score ≥ 0.80** on all records
- [ ] **Completeness ≥ 0.70** (70% of fields populated)
- [ ] **No failed validations** (all constraints met)
- [ ] **Lineage documented** (source, version, parameters)
- [ ] **Approved for ML** (approved_for_ml = true in lineage)
- [ ] **Outliers identified** and handled (documented in anomalies)
- [ ] **Dataset splits created** with fixed random seed
- [ ] **Features extracted & logged** with versioning
- [ ] **Feature correlations analyzed** (watch for multicollinearity)
- [ ] **No duplicates** detected (uniqueness = 1.0)

## 📊 Quality Metrics Reference

### Quality Score Interpretation

| Score | Interpretation | ML Readiness |
|-------|----------------|--------------|
| 0.95+ | Excellent | ✅ Highly recommended |
| 0.85-0.94 | Very Good | ✅ Ready for production |
| 0.80-0.84 | Good | ⚠️ Use with caution |
| 0.70-0.79 | Fair | ❌ Not recommended |
| <0.70 | Poor | ❌ Exclude from models |

### Validation Constraints

```
Energy:              Must be negative (eV)
Band Gap (gap):      0 < gap < 50 eV
HOMO:                -50 < HOMO < 0 eV
LUMO:                -20 < LUMO < 20 eV
Dipole Moment:       0 < dipole < 20 Debye
Charges:             -2 < charge < 2 (au)
Forces:              0 < force < 100 kcal/mol/Å
Wall Time:           0 < time < 3600 seconds
```

## 🔗 Next Steps

1. **Deploy schema** using `backend/scripts/schema_extensions_phase1.sql`
2. **Update xTB runner** to compute quality scores
3. **Implement anomaly detection** pipeline
4. **Build ML dataset API** endpoints
5. **Create monitoring dashboard** for data quality
