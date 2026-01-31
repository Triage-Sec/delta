# @delta-ltsc/ml

[![npm](https://img.shields.io/npm/v/@delta-ltsc/ml)](https://www.npmjs.com/package/@delta-ltsc/ml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../../LICENSE)

Optional ML features for **Delta LTSC** - Pattern importance scoring, quality prediction, and adaptive region detection.

## Installation

```bash
npm install @delta-ltsc/ml @delta-ltsc/sdk
```

Note: `@delta-ltsc/sdk` is a required peer dependency.

## Features

- **Pattern Importance Scoring** - Determine which patterns are semantically important and should be preserved
- **Quality Prediction** - Predict if compression will degrade model performance before applying it
- **Region Detection** - Identify system prompts, user input, and context for adaptive compression strategies

## Pattern Importance

Score patterns to preserve semantically important content:

```typescript
import { PositionalImportanceScorer, filterByImportance } from '@delta-ltsc/ml';
import { discoverPatterns } from '@delta-ltsc/sdk';

const scorer = new PositionalImportanceScorer({ decayRate: 2.0 });
const patterns = await discoverPatterns(tokens);
const scores = await scorer.scorePatterns(tokens, patterns);

// Filter out high-importance patterns (preserve them from compression)
const safeToCompress = filterByImportance(patterns, scores, 0.8);
```

### Embedding-Based Scoring

For more accurate importance scoring using an embedding model:

```typescript
import { EmbeddingImportanceScorer } from '@delta-ltsc/ml';

const scorer = new EmbeddingImportanceScorer(embeddingProvider, {
  contextWindow: 5,
});

const scores = await scorer.scorePatterns(tokens, patterns);
```

## Quality Prediction

Predict if compressed output will maintain quality before committing:

```typescript
import { createQualityPredictor } from '@delta-ltsc/ml';
import { compress } from '@delta-ltsc/sdk';

const predictor = createQualityPredictor();
const result = await compress(tokens);
const prediction = await predictor.predict(result);

if (!prediction.acceptable) {
  console.log(`Recommendation: ${prediction.recommendation}`);
  // 'accept' | 'retry_conservative' | 'skip_compression'
}
```

### Quality Features

```typescript
console.log(prediction.features);
// {
//   compressionRatio: 0.65,
//   dictionaryOverhead: 0.15,
//   diversityReduction: 0.2,
//   averagePatternLength: 4.5,
//   patternCount: 12,
// }
```

## Region Detection

Detect semantic regions for adaptive compression strategies:

```typescript
import { detectRegions, RegionType, filterPatternsByRegion } from '@delta-ltsc/ml';

const regions = detectRegions(tokens, {
  systemMarkers: [[58, 71905, 60]], // [SYSTEM] token sequence
  retentionTargets: {
    [RegionType.SYSTEM]: 0.98,  // Minimal compression (preserve instructions)
    [RegionType.USER]: 0.85,    // Moderate compression
    [RegionType.CONTEXT]: 0.6,  // Aggressive compression (RAG content)
  },
});

// Filter patterns based on region constraints
const filtered = filterPatternsByRegion(patterns, regions, tokens);
```

### Region Types

| Region | Description | Default Retention |
|--------|-------------|-------------------|
| `SYSTEM` | System instructions | 98% (minimal compression) |
| `USER` | User input | 85% (moderate) |
| `CONTEXT` | Injected context/documents | 60% (aggressive) |
| `CODE` | Code blocks | 80% (moderate) |
| `UNKNOWN` | Default region | 75% |

## Custom Embedding Provider

Implement the `EmbeddingProvider` interface for your embedding model:

```typescript
import type { EmbeddingProvider } from '@delta-ltsc/ml';

class OpenAIEmbeddings implements EmbeddingProvider {
  async embed(tokens: readonly number[]): Promise<Float32Array> {
    const text = tokenizer.decode(tokens);
    const response = await openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: text,
    });
    return new Float32Array(response.data[0].embedding);
  }

  dimension(): number {
    return 1536;
  }
}

const scorer = new EmbeddingImportanceScorer(new OpenAIEmbeddings());
```

## API Reference

### Importance Scoring

| Export | Description |
|--------|-------------|
| `PositionalImportanceScorer` | Score patterns by position (earlier = more important) |
| `EmbeddingImportanceScorer` | Score patterns by contextual diversity |
| `CombinedImportanceScorer` | Combine positional and embedding scoring |
| `adjustPrioritiesByImportance()` | Adjust pattern priorities based on scores |
| `filterByImportance()` | Filter out high-importance patterns |

### Quality Prediction

| Export | Description |
|--------|-------------|
| `HeuristicQualityPredictor` | Rule-based quality prediction |
| `EmbeddingQualityPredictor` | Enhanced prediction with embedding similarity |
| `createQualityPredictor()` | Factory function for creating predictors |

### Region Detection

| Export | Description |
|--------|-------------|
| `detectRegions()` | Detect semantic regions in token sequence |
| `detectRegionsHeuristic()` | Simple heuristic-based detection |
| `filterPatternsByRegion()` | Filter patterns based on region constraints |
| `getRegionCompressionSettings()` | Get default settings for a region type |
| `RegionType` | Enum of available region types |

## License

MIT License - see [LICENSE](../../LICENSE) for details.

## Contributors

Built by [Triage Sec](https://triage-sec.com) - an applied team of researchers and engineers working towards building resiliency for AI systems.

- Nikhil Srivastava (University of California, Berkeley)
- Omansh Bainsla (Georgia Tech)
- Sahil Chatiwala (Georgia Tech)
