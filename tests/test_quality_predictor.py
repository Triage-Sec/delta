"""Tests for compression quality prediction."""

import pytest
from small.quality_predictor import (
    QualityPrediction,
    CompressionQualityPredictor,
    create_predictor,
    evaluate_compression_quality,
)
from small.types import CompressionResult


def _make_result(
    original_len: int,
    compressed_len: int,
    num_patterns: int = 3,
) -> CompressionResult:
    """Create a mock CompressionResult for testing."""
    original_tokens = tuple(range(original_len))
    compressed_tokens = list(range(compressed_len))
    
    # Create mock dictionary
    dictionary_map = {}
    meta_tokens = []
    for i in range(num_patterns):
        meta = f"<MT_{i}>"
        dictionary_map[meta] = (f"a{i}", f"b{i}", f"c{i}")
        meta_tokens.append(meta)
    
    # Estimate dictionary tokens
    dict_tokens = ["<Dict>"]
    for meta, seq in dictionary_map.items():
        dict_tokens.extend([meta] + list(seq))
    dict_tokens.append("</Dict>")
    
    return CompressionResult(
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        serialized_tokens=compressed_tokens,
        dictionary_tokens=dict_tokens,
        body_tokens=compressed_tokens,
        dictionary_map=dictionary_map,
        meta_tokens_used=tuple(meta_tokens),
        original_length=original_len,
        compressed_length=compressed_len,
    )


def test_quality_prediction_structure():
    pred = QualityPrediction(
        predicted_degradation=0.05,
        confidence=0.7,
        recommendation="compress",
        suggested_max_ratio=0.8,
        risk_factors=("High compression",),
    )
    
    assert pred.predicted_degradation == 0.05
    assert pred.confidence == 0.7
    assert pred.recommendation == "compress"
    assert pred.suggested_max_ratio == 0.8
    assert len(pred.risk_factors) == 1


def test_predictor_low_compression():
    tokens = list(range(100))
    result = _make_result(100, 90, num_patterns=2)  # 10% compression
    
    predictor = CompressionQualityPredictor()
    prediction = predictor.predict(tokens, result)
    
    # Low compression should have low degradation
    assert prediction.predicted_degradation < 0.1
    assert prediction.recommendation in ("compress", "partial")


def test_predictor_high_compression():
    tokens = list(range(100))
    result = _make_result(100, 30, num_patterns=10)  # 70% compression
    
    predictor = CompressionQualityPredictor()
    prediction = predictor.predict(tokens, result)
    
    # Very aggressive compression should have higher degradation
    assert prediction.predicted_degradation > 0.01


def test_predictor_task_types():
    tokens = list(range(100))
    result = _make_result(100, 50, num_patterns=5)
    
    # Code tasks should be more sensitive
    code_predictor = CompressionQualityPredictor(task_type="code")
    code_pred = code_predictor.predict(tokens, result)
    
    # General tasks should be less sensitive
    general_predictor = CompressionQualityPredictor(task_type="general")
    general_pred = general_predictor.predict(tokens, result)
    
    # Code should have higher predicted degradation
    assert code_pred.predicted_degradation >= general_pred.predicted_degradation


def test_predictor_conservative_mode():
    tokens = list(range(100))
    result = _make_result(100, 60, num_patterns=4)
    
    normal_predictor = CompressionQualityPredictor(conservative=False)
    conservative_predictor = CompressionQualityPredictor(conservative=True)
    
    normal_pred = normal_predictor.predict(tokens, result)
    conservative_pred = conservative_predictor.predict(tokens, result)
    
    # Conservative should predict higher degradation
    assert conservative_pred.predicted_degradation >= normal_pred.predicted_degradation


def test_should_compress_method():
    tokens = list(range(100))
    result = _make_result(100, 85, num_patterns=2)  # Mild compression
    
    predictor = CompressionQualityPredictor()
    
    # Should compress with high threshold
    assert predictor.should_compress(tokens, result, max_degradation=0.2)


def test_create_predictor():
    # Test factory function
    predictor = create_predictor("code")
    assert predictor.task_type == "code"
    
    predictor = create_predictor("general")
    assert predictor.task_type == "general"


def test_evaluate_compression_quality():
    tokens = list(range(100))
    result = _make_result(100, 70, num_patterns=5)
    
    metrics = evaluate_compression_quality(tokens, result)
    
    assert "compression_ratio" in metrics
    assert "dict_overhead_ratio" in metrics
    assert "effective_compression" in metrics
    assert metrics["compression_ratio"] == 0.7


def test_predictor_recommendation_compress():
    tokens = list(range(100))
    result = _make_result(100, 90, num_patterns=2)  # Light compression
    
    predictor = CompressionQualityPredictor()
    prediction = predictor.predict(tokens, result)
    
    # Should recommend compress for light compression
    assert prediction.recommendation == "compress"


def test_predictor_no_compression():
    tokens = list(range(10))
    result = _make_result(10, 10, num_patterns=0)  # No compression
    
    predictor = CompressionQualityPredictor()
    prediction = predictor.predict(tokens, result)
    
    # No compression = no degradation
    assert prediction.predicted_degradation < 0.05


def test_risk_factors_identified():
    tokens = list(range(100))
    result = _make_result(100, 25, num_patterns=20)  # Very aggressive
    
    predictor = CompressionQualityPredictor()
    prediction = predictor.predict(tokens, result)
    
    # Should identify aggressive compression as risk
    assert len(prediction.risk_factors) > 0
