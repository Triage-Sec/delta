# @small-ltsc/sdk

[![npm](https://img.shields.io/npm/v/@small-ltsc/sdk)](https://www.npmjs.com/package/@small-ltsc/sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../../LICENSE)

TypeScript SDK for **Small LTSC** - Lossless Token Sequence Compression for LLMs.

Reduce LLM inference costs by compressing repetitive token patterns in prompts while maintaining perfect reconstruction. Achieve 30-60% compression on structured inputs with a format that fine-tuned models can understand.

## Features

- **Lossless compression** - Perfect round-trip reconstruction guaranteed
- **High performance** - Rust/WASM core with O(n log n) suffix array algorithms
- **Cross-platform** - Works in browsers, Node.js, Deno, and edge runtimes
- **Streaming support** - Handle inputs of any size with constant memory
- **Worker threads** - Non-blocking compression for large inputs
- **Static dictionaries** - Pre-built patterns for Python, TypeScript, SQL, and more
- **TypeScript-first** - Full type safety and IntelliSense support

## Installation

```bash
npm install @small-ltsc/sdk
```

## Quick Start

```typescript
import { compress, decompress, initWasm } from '@small-ltsc/sdk';

// Initialize WASM module (required once)
await initWasm();

// Compress tokens
const tokens = [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3];
const result = await compress(tokens);

console.log(`Compressed: ${result.originalLength} → ${result.compressedLength} tokens`);
console.log(`Savings: ${((1 - result.compressionRatio) * 100).toFixed(1)}%`);

// Decompress (lossless)
const restored = await decompress(result.serializedTokens);
console.assert(JSON.stringify(tokens) === JSON.stringify(restored));
```

## Configuration

```typescript
const result = await compress(tokens, {
  // Pattern discovery
  minSubsequenceLength: 2,    // Minimum pattern length (default: 2)
  maxSubsequenceLength: 8,    // Maximum pattern length (default: 8)
  
  // Selection algorithm
  selectionMode: 'greedy',    // 'greedy' | 'optimal' | 'beam'
  
  // Hierarchical compression
  hierarchicalEnabled: true,  // Allow patterns of patterns
  hierarchicalMaxDepth: 3,    // Maximum nesting depth
  
  // Verification
  verify: true,               // Enable round-trip verification
});
```

## Static Dictionaries

Use pre-built dictionaries for domain-specific compression:

```typescript
const result = await compress(pythonCodeTokens, {
  staticDictionary: 'python-v1',
});
```

Available dictionaries: `python-v1`, `typescript-v1`, `markdown-v1`, `json-v1`, `sql-v1`

## Streaming

For large inputs that exceed memory constraints:

```typescript
import { createStreamingCompressor } from '@small-ltsc/sdk';

const compressor = await createStreamingCompressor();

for await (const chunk of tokenStream) {
  await compressor.addChunk(chunk);
}

const result = await compressor.finish();
```

## Worker Threads

Non-blocking compression for UI responsiveness:

```typescript
import { createWorkerPool } from '@small-ltsc/sdk';

const pool = await createWorkerPool(4);
const result = await pool.compress(tokens);
pool.terminate();
```

## Browser Usage

```html
<script type="module">
  import { compress, initWasm } from 'https://esm.sh/@small-ltsc/sdk';
  
  await initWasm();
  const result = await compress([1, 2, 3, 1, 2, 3]);
  console.log('Compression ratio:', result.compressionRatio);
</script>
```

## API Reference

### Core Functions

| Function | Description |
|----------|-------------|
| `compress(tokens, config?)` | Compress a token sequence |
| `decompress(tokens, config?)` | Decompress to original tokens |
| `discoverPatterns(tokens, minLen?, maxLen?)` | Find patterns without compressing |

### Streaming

| Function | Description |
|----------|-------------|
| `createStreamingCompressor(config?)` | Create a streaming compressor instance |
| `compressStream(asyncIterable, config?)` | Compress an async iterable stream |

### Workers

| Function | Description |
|----------|-------------|
| `createWorkerPool(count?)` | Create a pool of worker threads |
| `compressInWorker(tokens, config?)` | Single-use worker compression |

### Dictionaries

| Function | Description |
|----------|-------------|
| `loadStaticDictionary(id)` | Load a built-in dictionary |
| `createStaticDictionary(id, patterns)` | Create a custom dictionary |

### Utilities

| Function | Description |
|----------|-------------|
| `initWasm()` | Initialize the WASM module |
| `isWasmInitialized()` | Check initialization status |
| `extractDictionary(tokens)` | Extract dictionary from compressed tokens |
| `isCompressed(tokens)` | Check if tokens are in compressed format |

## Documentation

- [Quick Start Guide](./docs/QUICKSTART.md)
- [API Reference](./docs/API.md)
- [Main Repository](https://github.com/triage-sec/small)

## Optional ML Features

For pattern importance scoring and quality prediction:

```bash
npm install @small-ltsc/ml
```

```typescript
import { HeuristicQualityPredictor } from '@small-ltsc/ml';

const predictor = new HeuristicQualityPredictor();
const prediction = await predictor.predict(compressionResult);

if (!prediction.acceptable) {
  console.log(`Recommendation: ${prediction.recommendation}`);
}
```

## License

MIT License - see [LICENSE](../../LICENSE) for details.

## Contributors

Built by [Triage Sec](https://triage-sec.com) - an applied team of researchers and engineers working towards building resiliency for AI systems.

- Nikhil Srivastava (University of California, Berkeley)
- Omansh Bainsla (Georgia Tech)
- Sahil Chatiwala (Georgia Tech)
