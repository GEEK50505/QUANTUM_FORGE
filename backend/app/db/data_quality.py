"""
Data Quality Assurance Module for ML-Ready Data
================================================

Provides data validation, quality scoring, and ML readiness assessment for:
- Quantum chemistry calculations (xTB results)
- Molecular properties
- Extracted features
- Batch processing results

Features:
- Multi-dimensional quality scoring (completeness, validity, consistency, uniqueness)
- Outlier detection (IQR, z-score, statistical methods)
- Data lineage and provenance tracking
- Confidence interval computation
- ML dataset split management
- Feature extraction versioning
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """Data quality dimensions based on ISO 8601 standards"""
    COMPLETENESS = "completeness"      # Fraction of non-null fields
    VALIDITY = "validity"              # Values within acceptable ranges
    CONSISTENCY = "consistency"         # Internal cross-field consistency
    UNIQUENESS = "uniqueness"          # No duplicate records
    ACCURACY = "accuracy"              # Correctness vs ground truth
    TIMELINESS = "timeliness"          # Data freshness


class AnomalyType(Enum):
    """Types of data anomalies detected"""
    OUTLIER = "outlier"                        # Statistical outlier
    DUPLICATE = "duplicate"                    # Exact/near duplicate
    IMPOSSIBLE_VALUE = "impossible_value"      # Physically impossible value
    DISTRIBUTION_SHIFT = "distribution_shift"  # Out-of-distribution
    MISSING_DATA = "missing_data"              # Too many missing values


class AnomalySeverity(Enum):
    """Severity levels for detected anomalies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QualityMetrics:
    """Container for all quality metrics for a data entity"""
    entity_id: int
    entity_type: str
    completeness_score: float  # 0-1
    validity_score: float      # 0-1
    consistency_score: float   # 0-1
    uniqueness_score: float    # 0-1
    overall_quality_score: float  # 0-1 (weighted average)
    
    is_outlier: bool = False
    is_suspicious: bool = False
    has_missing_values: bool = False
    failed_validation: bool = False
    
    missing_fields: List[str] = None
    data_source: str = None
    validation_method: str = None
    notes: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'completeness_score': self.completeness_score,
            'validity_score': self.validity_score,
            'consistency_score': self.consistency_score,
            'uniqueness_score': self.uniqueness_score,
            'overall_quality_score': self.overall_quality_score,
            'is_outlier': self.is_outlier,
            'is_suspicious': self.is_suspicious,
            'has_missing_values': self.has_missing_values,
            'failed_validation': self.failed_validation,
            'missing_fields': self.missing_fields or [],
            'data_source': self.data_source,
            'validation_method': self.validation_method,
            'notes': self.notes,
        }


@dataclass
class Anomaly:
    """Detected data anomaly"""
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    detection_method: str
    entity_type: str
    entity_ids: List[int]
    
    detected_value: Optional[float] = None
    expected_value_range: Optional[Dict[str, float]] = None  # {min, max, mean, std}
    z_score: Optional[float] = None
    percentile: Optional[float] = None
    
    action_taken: str = "flagged"  # flagged, excluded, corrected, pending_review
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            'anomaly_type': self.anomaly_type.value,
            'severity': self.severity.value,
            'detection_method': self.detection_method,
            'detected_entity_type': self.entity_type,
            'detected_entity_ids': self.entity_ids,
            'detected_value': self.detected_value,
            'expected_value_range': self.expected_value_range,
            'z_score': self.z_score,
            'percentile': self.percentile,
            'action_taken': self.action_taken,
            'resolution_notes': self.resolution_notes,
        }


class QualityAssessor:
    """Comprehensive data quality assessment engine"""
    
    # Valid ranges for quantum chemistry properties
    VALID_RANGES = {
        'energy': (-float('inf'), 0),  # Should be negative
        'gap': (0, 50),  # eV, reasonable for organic molecules
        'dipole_moment': (0, 20),  # Debye
        'charges': (-2, 2),  # Atomic units
        'forces': (0, 100),  # kcal/mol/Angstrom
        'homo': (-50, 0),  # eV
        'lumo': (-20, 20),  # eV
        'wall_time_seconds': (0, 3600),  # Less than 1 hour typical
    }
    
    def __init__(self):
        """Initialize quality assessor with default parameters"""
        self.z_score_threshold = 3.0  # Standard outlier threshold
        self.iqr_multiplier = 1.5     # Interquartile range multiplier
        
    # ========================================================================
    # COMPLETENESS ASSESSMENT
    # ========================================================================
    
    def assess_completeness(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
        optional_fields: Optional[List[str]] = None
    ) -> Tuple[float, List[str]]:
        """
        Assess data completeness.
        
        Args:
            data: Dictionary of data values
            required_fields: List of required fields (must be non-null)
            optional_fields: List of optional fields
            
        Returns:
            (completeness_score: 0-1, missing_fields: list)
        """
        optional_fields = optional_fields or []
        all_fields = required_fields + optional_fields
        missing_fields = []
        
        # Check required fields
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        # Calculate score based on total fields
        total_fields = len(all_fields)
        if total_fields == 0:
            completeness = 1.0
        else:
            present_fields = sum(
                1 for field in all_fields 
                if field in data and data[field] is not None
            )
            completeness = present_fields / total_fields
        
        return completeness, missing_fields
    
    # ========================================================================
    # VALIDITY ASSESSMENT
    # ========================================================================
    
    def assess_validity(
        self,
        data: Dict[str, Any],
        valid_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
        custom_validators: Optional[Dict[str, callable]] = None
    ) -> Tuple[float, List[str]]:
        """
        Assess data validity against ranges and constraints.
        
        Args:
            data: Dictionary of data values
            valid_ranges: Dict mapping field names to (min, max) tuples
            custom_validators: Dict mapping field names to validator functions
            
        Returns:
            (validity_score: 0-1, invalid_fields: list)
        """
        valid_ranges = valid_ranges or self.VALID_RANGES
        custom_validators = custom_validators or {}
        
        invalid_fields = []
        total_checks = 0
        
        # Check ranges
        for field, (min_val, max_val) in valid_ranges.items():
            if field in data and data[field] is not None:
                value = data[field]
                
                # Skip list/array values
                if isinstance(value, (list, tuple)):
                    continue
                
                total_checks += 1
                try:
                    if not (min_val <= value <= max_val):
                        invalid_fields.append(f"{field}={value} (range: {min_val}-{max_val})")
                except TypeError:
                    # Skip if comparison fails due to type mismatch
                    pass
        
        # Check custom validators
        for field, validator in custom_validators.items():
            if field in data and data[field] is not None:
                total_checks += 1
                try:
                    if not validator(data[field]):
                        invalid_fields.append(f"{field}={data[field]} (custom validation failed)")
                except TypeError:
                    pass
        
        validity = 1.0 - (len(invalid_fields) / total_checks) if total_checks > 0 else 1.0
        
        return validity, invalid_fields
    
    # ========================================================================
    # CONSISTENCY ASSESSMENT
    # ========================================================================
    
    def assess_consistency(
        self,
        data: Dict[str, Any],
        consistency_rules: Optional[List[Tuple[str, str, callable]]] = None
    ) -> Tuple[float, List[str]]:
        """
        Assess internal data consistency (cross-field relationships).
        
        Args:
            data: Dictionary of data values
            consistency_rules: List of (field1, field2, check_function) tuples
                               where check_function(val1, val2) returns bool
            
        Returns:
            (consistency_score: 0-1, violations: list)
        """
        if consistency_rules is None:
            # Default rules for quantum chemistry data
            consistency_rules = [
                ('gap', 'homo', lambda g, h: isinstance(g, (int, float)) and isinstance(h, (int, float)) and g > 0),
                ('gap', 'lumo', lambda g, l: isinstance(g, (int, float)) and isinstance(l, (int, float)) and g > 0),
                ('homo', 'lumo', lambda h, l: isinstance(h, (int, float)) and isinstance(l, (int, float)) and h < l),
                ('energy', 'gap', lambda e, g: isinstance(e, (int, float)) and isinstance(g, (int, float)) and e < 0 and g >= 0),
            ]
        
        violations = []
        total_checks = 0
        
        for field1, field2, check_func in consistency_rules:
            if field1 in data and field2 in data:
                if data[field1] is not None and data[field2] is not None:
                    total_checks += 1
                    try:
                        if not check_func(data[field1], data[field2]):
                            violations.append(
                                f"{field1}({data[field1]}) vs {field2}({data[field2]})"
                            )
                    except (TypeError, ValueError):
                        # Skip checks that fail due to type mismatch
                        pass
        
        consistency = 1.0 - (len(violations) / total_checks) if total_checks > 0 else 1.0
        
        return consistency, violations
    
    # ========================================================================
    # UNIQUENESS ASSESSMENT
    # ========================================================================
    
    def assess_uniqueness(
        self,
        data_batch: List[Dict[str, Any]],
        key_fields: Optional[List[str]] = None
    ) -> Tuple[float, List[str]]:
        """
        Assess uniqueness in a batch of records (check for duplicates).
        
        Args:
            data_batch: List of data dictionaries
            key_fields: Fields to use for duplicate detection
            
        Returns:
            (uniqueness_score: 0-1, duplicates: list)
        """
        if not data_batch or len(data_batch) < 2:
            return 1.0, []
        
        key_fields = key_fields or ['smiles', 'formula']  # For molecules
        
        seen = {}
        duplicates = []
        
        for idx, data in enumerate(data_batch):
            # Create key from specified fields
            key_parts = []
            for field in key_fields:
                if field in data:
                    key_parts.append(str(data[field]))
            
            if not key_parts:
                continue
                
            key = tuple(key_parts)
            
            if key in seen:
                duplicates.append(f"record {idx} duplicates record {seen[key]}")
            else:
                seen[key] = idx
        
        uniqueness = 1.0 - (len(duplicates) / len(data_batch)) if data_batch else 1.0
        
        return uniqueness, duplicates
    
    # ========================================================================
    # OUTLIER DETECTION
    # ========================================================================
    
    def detect_outliers_iqr(
        self,
        values: np.ndarray,
        multiplier: float = 1.5
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Detect outliers using Interquartile Range (IQR) method.
        
        Args:
            values: Array of numerical values
            multiplier: IQR multiplier (1.5 for outliers, 3.0 for extreme)
            
        Returns:
            (outlier_mask: boolean array, bounds: {lower, upper, q1, q3, iqr})
        """
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        outlier_mask = (values < lower_bound) | (values > upper_bound)
        
        bounds = {
            'q1': float(q1),
            'q3': float(q3),
            'iqr': float(iqr),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
        }
        
        return outlier_mask, bounds
    
    def detect_outliers_zscore(
        self,
        values: np.ndarray,
        threshold: float = 3.0
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Detect outliers using Z-score method.
        
        Args:
            values: Array of numerical values
            threshold: Z-score threshold (3.0 = 99.7% confidence)
            
        Returns:
            (outlier_mask: boolean array, stats: {mean, std, z_scores})
        """
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return np.zeros(len(values), dtype=bool), {'mean': mean, 'std': std}
        
        z_scores = np.abs((values - mean) / std)
        outlier_mask = z_scores > threshold
        
        stats = {
            'mean': float(mean),
            'std': float(std),
            'threshold': threshold,
            'outlier_count': int(np.sum(outlier_mask)),
        }
        
        return outlier_mask, stats
    
    # ========================================================================
    # COMPREHENSIVE QUALITY ASSESSMENT
    # ========================================================================
    
    def assess_calculation_quality(
        self,
        calc_data: Dict[str, Any],
        calc_id: int,
        computation_metadata: Optional[Dict[str, Any]] = None
    ) -> QualityMetrics:
        """
        Comprehensive quality assessment for a calculation result.
        
        Args:
            calc_data: Calculation data dictionary
            calc_id: Database ID of calculation
            computation_metadata: Metadata about the computation
            
        Returns:
            QualityMetrics object with all quality dimensions
        """
        computation_metadata = computation_metadata or {}
        
        # Required fields for calculations
        required_fields = ['energy', 'gap', 'homo', 'lumo']
        optional_fields = ['dipole_moment', 'charges', 'forces', 'convergence_energy']
        
        # DEBUG: Log input data
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"assess_calculation_quality input: {calc_data}")
        
        # Assess completeness
        completeness, missing = self.assess_completeness(
            calc_data, required_fields, optional_fields
        )
        logger.debug(f"  Completeness: {completeness:.2f}, Missing: {missing}")
        
        # Assess validity
        validity, invalid = self.assess_validity(calc_data)
        logger.debug(f"  Validity: {validity:.2f}, Invalid: {invalid}")
        
        # Assess consistency
        consistency, violations = self.assess_consistency(calc_data)
        logger.debug(f"  Consistency: {consistency:.2f}, Violations: {violations}")
        
        # Uniqueness (simplified for single record)
        uniqueness = 1.0
        
        # Calculate overall score (weighted average)
        weights = {
            'completeness': 0.25,
            'validity': 0.35,
            'consistency': 0.30,
            'uniqueness': 0.10,
        }
        
        overall = (
            completeness * weights['completeness'] +
            validity * weights['validity'] +
            consistency * weights['consistency'] +
            uniqueness * weights['uniqueness']
        )
        logger.debug(f"  Overall: {overall:.2f} (comp={completeness:.2f}, val={validity:.2f}, cons={consistency:.2f})")
        
        # Detect outliers/suspicious values
        is_outlier = False
        is_suspicious = False
        
        if 'gap' in calc_data and calc_data['gap'] is not None:
            if calc_data['gap'] < 0.1 or calc_data['gap'] > 20:
                is_suspicious = True
            if calc_data['gap'] < 0 or calc_data['gap'] > 30:
                is_outlier = True
        
        # Create metrics object
        metrics = QualityMetrics(
            entity_id=calc_id,
            entity_type='calculations',
            completeness_score=completeness,
            validity_score=validity,
            consistency_score=consistency,
            uniqueness_score=uniqueness,
            overall_quality_score=overall,
            is_outlier=is_outlier,
            is_suspicious=is_suspicious,
            has_missing_values=len(missing) > 0,
            failed_validation=len(invalid) > 0,
            missing_fields=missing or None,
            data_source=computation_metadata.get('xtb_version', 'unknown'),
            validation_method='multi_dimensional_assessment',
            notes=f"Issues: {len(invalid)} validity violations, {len(violations)} consistency violations"
        )
        
        return metrics
    
    def should_exclude_from_ml(
        self,
        metrics: QualityMetrics,
        quality_threshold: float = 0.8,
        max_missing_fraction: float = 0.1
    ) -> Tuple[bool, str]:
        """
        Determine if data should be excluded from ML dataset.
        
        Args:
            metrics: QualityMetrics object
            quality_threshold: Minimum acceptable quality score
            max_missing_fraction: Maximum fraction of missing fields
            
        Returns:
            (should_exclude: bool, reason: str)
        """
        reasons = []
        
        if metrics.overall_quality_score < quality_threshold:
            reasons.append(f"Quality score {metrics.overall_quality_score:.3f} < {quality_threshold}")
        
        if metrics.is_outlier:
            reasons.append("Detected as statistical outlier")
        
        if metrics.failed_validation:
            reasons.append("Failed validation constraints")
        
        if metrics.missing_fields and len(metrics.missing_fields) > 0:
            missing_frac = len(metrics.missing_fields) / 10  # Approximate
            if missing_frac > max_missing_fraction:
                reasons.append(f"Too many missing fields ({len(metrics.missing_fields)})")
        
        should_exclude = len(reasons) > 0
        reason = " | ".join(reasons) if reasons else "Data quality acceptable"
        
        return should_exclude, reason


class ConfidenceIntervalCalculator:
    """Compute confidence intervals for predictions and measurements"""
    
    @staticmethod
    def compute_bootstrap_ci(
        values: np.ndarray,
        confidence: float = 0.95,
        n_bootstrap: int = 1000
    ) -> Dict[str, float]:
        """
        Compute confidence interval using bootstrap method.
        
        Args:
            values: Array of observed values
            confidence: Confidence level (0.95 = 95% CI)
            n_bootstrap: Number of bootstrap samples
            
        Returns:
            {'lower': value, 'upper': value, 'mean': value, 'std': value}
        """
        mean = np.mean(values)
        std = np.std(values)
        
        bootstrap_means = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(values, size=len(values), replace=True)
            bootstrap_means.append(np.mean(sample))
        
        alpha = 1 - confidence
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        return {
            'lower': float(np.percentile(bootstrap_means, lower_percentile)),
            'upper': float(np.percentile(bootstrap_means, upper_percentile)),
            'mean': float(mean),
            'std': float(std),
        }
    
    @staticmethod
    def compute_uncertainty_from_error(
        errors: np.ndarray,
        confidence: float = 0.95
    ) -> Dict[str, float]:
        """
        Compute uncertainty from prediction errors.
        
        Args:
            errors: Array of prediction errors
            confidence: Confidence level
            
        Returns:
            {'uncertainty': margin, 'mse': mean_squared_error}
        """
        mse = np.mean(errors ** 2)
        rmse = np.sqrt(mse)
        
        # Z-score for confidence level
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence, 1.96)
        
        uncertainty = z * rmse
        
        return {
            'uncertainty': float(uncertainty),
            'rmse': float(rmse),
            'mse': float(mse),
            'confidence_level': confidence,
        }


# Module exports
__all__ = [
    'QualityAssessor',
    'ConfidenceIntervalCalculator',
    'QualityMetrics',
    'Anomaly',
    'AnomalyType',
    'AnomalySeverity',
    'QualityDimension',
]
