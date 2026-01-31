"""Advanced usage example demonstrating ML integration features."""

from delta import (
    compress, 
    decompress, 
    CompressionConfig,
    detect_regions,
    filter_candidates_by_region,
    create_default_scorer,
    adjust_candidate_priorities,
    create_predictor,
    RegionType,
)
from delta.discovery_sa import discover_candidates_sa
from delta.subsumption import prune_subsumed_candidates


def demonstrate_region_detection():
    """Show region-aware compression."""
    print("=" * 60)
    print("Region-Aware Compression")
    print("=" * 60)
    
    # Simulated prompt with different regions
    tokens = [
        "[SYSTEM]", "You", "are", "a", "helpful", "assistant", ".",
        "[USER]", "What", "is", "the", "capital", "of", "France", "?",
        "[CONTEXT]", "The", "capital", "of", "France", "is", "Paris", ".",
        "The", "capital", "of", "Germany", "is", "Berlin", ".",
        "The", "capital", "of", "Italy", "is", "Rome", ".",
    ]
    
    # Detect regions
    regions = detect_regions(tokens)
    
    print("\nDetected regions:")
    for region in regions:
        region_tokens = tokens[region.start:region.end]
        print(f"  {region.region_type.value:10s} [{region.start:2d}-{region.end:2d}]: "
              f"{' '.join(str(t) for t in region_tokens[:5])}...")
    
    # Compress with region awareness
    config = CompressionConfig(verify=True)
    candidates = discover_candidates_sa(tokens, config)
    
    print(f"\nCandidates before region filter: {len(candidates)}")
    
    filtered = filter_candidates_by_region(candidates, regions, tokens)
    
    print(f"Candidates after region filter:  {len(filtered)}")
    
    # Show which patterns are in which regions
    for cand in filtered[:3]:
        pos = cand.positions[0]
        for region in regions:
            if region.start <= pos < region.end:
                print(f"  {list(cand.subsequence)} in {region.region_type.value} "
                      f"(priority boost: {region.priority_boost:+d})")
                break


def demonstrate_importance_scoring():
    """Show pattern importance scoring."""
    print("\n" + "=" * 60)
    print("Pattern Importance Scoring")
    print("=" * 60)
    
    # Tokens with patterns at different positions
    tokens = (
        ["important", "system", "config"] * 3 +   # Early (important)
        ["data", "item", "value"] * 10 +           # Middle (less important)
        ["footer", "info", "end"] * 3              # Late (less important)
    )
    
    config = CompressionConfig(verify=True)
    candidates = discover_candidates_sa(tokens, config)
    
    # Score patterns
    scorer = create_default_scorer()
    scores = scorer.score_patterns(tokens, candidates)
    
    print("\nPattern importance scores (position + frequency + length):")
    for cand, score in sorted(zip(candidates, scores), key=lambda x: -x[1])[:5]:
        avg_pos = sum(cand.positions) / len(cand.positions)
        print(f"  {list(cand.subsequence)[:3]}... "
              f"score={score:.2f} "
              f"count={len(cand.positions)} "
              f"avg_pos={avg_pos:.0f}")
    
    # Adjust priorities
    adjusted = adjust_candidate_priorities(candidates, scores, importance_weight=0.5)
    
    print("\nPriority adjustments (low importance = higher compression priority):")
    for orig, adj in zip(candidates[:3], adjusted[:3]):
        print(f"  {list(orig.subsequence)[:3]}... "
              f"priority: {orig.priority} -> {adj.priority}")


def demonstrate_subsumption():
    """Show cross-pattern subsumption analysis."""
    print("\n" + "=" * 60)
    print("Subsumption Analysis")
    print("=" * 60)
    
    # Create patterns with subsumption relationships
    tokens = ["a", "b", "c", "d"] * 10 + ["a", "b"] * 5
    
    config = CompressionConfig(verify=True)
    candidates = discover_candidates_sa(tokens, config)
    
    print(f"\nCandidates before pruning: {len(candidates)}")
    for cand in candidates[:5]:
        print(f"  {list(cand.subsequence)} (count={len(cand.positions)})")
    
    # Prune subsumed patterns
    pruned = prune_subsumed_candidates(candidates, config)
    
    print(f"\nCandidates after pruning:  {len(pruned)}")
    for cand in pruned[:5]:
        print(f"  {list(cand.subsequence)} (count={len(cand.positions)})")


def demonstrate_quality_prediction():
    """Show compression quality prediction."""
    print("\n" + "=" * 60)
    print("Quality Prediction")
    print("=" * 60)
    
    # Different inputs for different predictions
    test_cases = [
        ("Light compression", ["hello", "world"] * 5),
        ("Heavy compression", ["x", "y", "z"] * 50),
        ("Code-like", ["def", "foo", "(", ")", ":"] * 10),
    ]
    
    config = CompressionConfig()
    
    for name, tokens in test_cases:
        result = compress(tokens, config)
        
        # Predict quality for different task types
        print(f"\n{name} ({len(tokens)} tokens -> {result.compressed_length}):")
        
        for task in ["general", "code", "creative"]:
            predictor = create_predictor(task)
            prediction = predictor.predict(tokens, result)
            
            print(f"  {task:10s}: "
                  f"degradation={prediction.predicted_degradation:.1%} "
                  f"recommendation={prediction.recommendation}")
            
            if prediction.risk_factors:
                for factor in prediction.risk_factors[:2]:
                    print(f"              - {factor}")


def demonstrate_full_pipeline():
    """Show complete ML-enhanced compression pipeline."""
    print("\n" + "=" * 60)
    print("Full ML-Enhanced Pipeline")
    print("=" * 60)
    
    # Realistic prompt
    tokens = [
        "[SYSTEM]", "You", "are", "an", "expert", "assistant", ".",
        "[USER]", "Explain", "the", "following", "code", ":",
        "```",
        "def", "calculate", "(", "x", ")", ":",
        "return", "x", "*", "2",
        "def", "process", "(", "x", ")", ":",
        "return", "x", "*", "2",
        "def", "transform", "(", "x", ")", ":",
        "return", "x", "*", "2",
        "```",
    ]
    
    config = CompressionConfig(verify=True)
    
    # Step 1: Discover candidates
    print("\n1. Discovery")
    candidates = discover_candidates_sa(tokens, config)
    print(f"   Found {len(candidates)} candidates")
    
    # Step 2: Prune subsumed
    print("\n2. Subsumption pruning")
    candidates = prune_subsumed_candidates(candidates, config)
    print(f"   Reduced to {len(candidates)} candidates")
    
    # Step 3: Region filtering
    print("\n3. Region filtering")
    regions = detect_regions(tokens)
    candidates = filter_candidates_by_region(candidates, regions, tokens)
    print(f"   After region filter: {len(candidates)} candidates")
    
    # Step 4: Importance scoring
    print("\n4. Importance scoring")
    scorer = create_default_scorer()
    scores = scorer.score_patterns(tokens, candidates)
    candidates = adjust_candidate_priorities(candidates, scores)
    print(f"   Priorities adjusted")
    
    # Step 5: Compress
    print("\n5. Compression")
    result = compress(tokens, config)
    print(f"   {result.original_length} -> {result.compressed_length} tokens")
    print(f"   Ratio: {result.compressed_length / result.original_length:.1%}")
    
    # Step 6: Quality check
    print("\n6. Quality prediction")
    predictor = create_predictor("code")
    prediction = predictor.predict(tokens, result)
    print(f"   Predicted degradation: {prediction.predicted_degradation:.1%}")
    print(f"   Recommendation: {prediction.recommendation}")
    
    # Step 7: Verify
    print("\n7. Verification")
    restored = decompress(result.serialized_tokens, config)
    print(f"   Lossless: {restored == tokens}")


def main():
    demonstrate_region_detection()
    demonstrate_importance_scoring()
    demonstrate_subsumption()
    demonstrate_quality_prediction()
    demonstrate_full_pipeline()


if __name__ == "__main__":
    main()
