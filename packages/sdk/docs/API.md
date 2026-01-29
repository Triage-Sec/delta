# API Reference

Complete API documentation for `@small-ltsc/sdk`.

## Table of Contents

- [Initialization](#initialization)
- [Compression](#compression)
- [Decompression](#decompression)
- [Streaming](#streaming)
- [Workers](#workers)
- [Dictionaries](#dictionaries)
- [Types](#types)

---

## Initialization

### `initWasm()`

Initialize the WASM module. Must be called before using compression functions.

```typescript
async function initWasm(): Promise<void>
```

**Notes:**
- Idempotent - safe to call multiple times
- Auto-called by `compress`/`decompress` if not initialized
- Call explicitly for faster first compression

**Example:**
```typescript
import { initWasm, isWasmInitialized } from '@small-ltsc/sdk';

await initWasm();
console.log(isWasmInitialized()); // true
```

### `isWasmInitialized()`

Check if WASM is initialized.

```typescript
function isWasmInitialized(): boolean
```

### `getWasmVersion()`

Get the version of the WASM core.

```typescript
function getWasmVersion(): string
```

---

## Compression

### `compress()`

Compress a token sequence.

```typescript
async function compress(
  tokens: TokenInput,
  config?: CompressionConfig
): Promise<CompressionResult>
```

**Parameters:**
- `tokens` - Array of token IDs (`number[]`, `Uint32Array`, or `readonly number[]`)
- `config` - Optional configuration object

**Returns:** `CompressionResult` object

**Example:**
```typescript
const result = await compress([1, 2, 3, 1, 2, 3], {
  maxSubsequenceLength: 6,
  verify: true,
});

console.log(result.compressionRatio); // 0.67
```

### `discoverPatterns()`

Discover compressible patterns without compressing.

```typescript
async function discoverPatterns(
  tokens: TokenInput,
  minLength?: number,
  maxLength?: number
): Promise<DiscoveredPattern[]>
```

**Parameters:**
- `tokens` - Token sequence to analyze
- `minLength` - Minimum pattern length (default: 2)
- `maxLength` - Maximum pattern length (default: 8)

**Example:**
```typescript
const patterns = await discoverPatterns(tokens, 2, 6);
for (const p of patterns) {
  console.log(`Pattern: ${p.pattern}, Count: ${p.count}`);
}
```

---

## Decompression

### `decompress()`

Decompress a compressed token sequence.

```typescript
async function decompress(
  tokens: TokenInput,
  config?: DecompressionConfig
): Promise<readonly number[]>
```

**Example:**
```typescript
const compressed = await compress(tokens);
const restored = await decompress(compressed.serializedTokens);
```

### `extractDictionary()`

Extract the dictionary from compressed tokens.

```typescript
async function extractDictionary(
  tokens: TokenInput,
  config?: DecompressionConfig
): Promise<ReadonlyMap<number, readonly number[]>>
```

### `extractBody()`

Extract body tokens without decompressing.

```typescript
function extractBody(
  tokens: TokenInput,
  config?: DecompressionConfig
): readonly number[]
```

### `isCompressed()`

Check if tokens appear to be compressed.

```typescript
function isCompressed(
  tokens: TokenInput,
  config?: DecompressionConfig
): boolean
```

---

## Streaming

### `createStreamingCompressor()`

Create a streaming compressor for large inputs.

```typescript
async function createStreamingCompressor(
  config?: CompressionConfig
): Promise<StreamingCompressor>
```

**Returns:** `StreamingCompressor` instance

### `StreamingCompressor`

Interface for streaming compression.

```typescript
interface StreamingCompressor {
  addChunk(tokens: TokenInput): Promise<void>;
  finish(): Promise<CompressionResult>;
  memoryUsage(): number;
  isFinished(): boolean;
}
```

**Example:**
```typescript
const compressor = await createStreamingCompressor();

await compressor.addChunk(chunk1);
await compressor.addChunk(chunk2);

const result = await compressor.finish();
```

### `compressStream()`

Compress an async iterable of token chunks.

```typescript
async function compressStream(
  tokenStream: AsyncIterable<TokenInput>,
  config?: CompressionConfig
): Promise<CompressionResult>
```

**Example:**
```typescript
async function* generateChunks() {
  yield [1, 2, 3];
  yield [1, 2, 3];
}

const result = await compressStream(generateChunks());
```

---

## Workers

### `createWorkerPool()`

Create a pool of workers for parallel compression.

```typescript
async function createWorkerPool(
  workerCount?: number
): Promise<WorkerPool>
```

**Parameters:**
- `workerCount` - Number of workers (default: `navigator.hardwareConcurrency`)

### `WorkerPool`

Interface for worker pool.

```typescript
interface WorkerPool {
  compress(tokens: TokenInput, config?: CompressionConfig): Promise<CompressionResult>;
  decompress(tokens: TokenInput, config?: DecompressionConfig): Promise<readonly number[]>;
  terminate(): void;
  size(): number;
}
```

**Example:**
```typescript
const pool = await createWorkerPool(4);

const results = await Promise.all([
  pool.compress(tokens1),
  pool.compress(tokens2),
  pool.compress(tokens3),
]);

pool.terminate();
```

### `compressInWorker()`

Single-use worker compression helper.

```typescript
async function compressInWorker(
  tokens: TokenInput,
  config?: CompressionConfig
): Promise<CompressionResult>
```

---

## Dictionaries

### `loadStaticDictionary()`

Load a built-in static dictionary.

```typescript
async function loadStaticDictionary(
  id: StaticDictionaryId
): Promise<StaticDictionary>
```

**Available IDs:**
- `'python-v1'`
- `'typescript-v1'`
- `'markdown-v1'`
- `'json-v1'`
- `'sql-v1'`

### `createStaticDictionary()`

Create a custom static dictionary.

```typescript
function createStaticDictionary(
  id: string,
  patterns: number[][],
  startMetaToken?: number
): StaticDictionary
```

**Example:**
```typescript
const myDict = createStaticDictionary('my-dict', [
  [1, 2, 3],
  [4, 5, 6, 7],
]);

const result = await compress(tokens, {
  staticDictionary: myDict,
});
```

### `listStaticDictionaries()`

List available built-in dictionaries.

```typescript
function listStaticDictionaries(): StaticDictionaryId[]
```

---

## Types

### `CompressionConfig`

```typescript
interface CompressionConfig {
  minSubsequenceLength?: number;      // Default: 2
  maxSubsequenceLength?: number;      // Default: 8
  selectionMode?: 'greedy' | 'optimal' | 'beam';  // Default: 'greedy'
  beamWidth?: number;                 // Default: 8
  hierarchicalEnabled?: boolean;      // Default: true
  hierarchicalMaxDepth?: number;      // Default: 3
  staticDictionary?: string | StaticDictionary;
  streamingThreshold?: number;        // Default: 50000
  maxMemoryMb?: number;               // Default: 256
  verify?: boolean;                   // Default: false
  dictStartToken?: number;            // Default: 0xFFFFFFF0
  dictEndToken?: number;              // Default: 0xFFFFFFF1
  nextMetaToken?: number;             // Default: 0xFFFF0000
}
```

### `CompressionResult`

```typescript
interface CompressionResult {
  readonly originalTokens: readonly number[];
  readonly serializedTokens: readonly number[];
  readonly dictionaryTokens: readonly number[];
  readonly bodyTokens: readonly number[];
  readonly originalLength: number;
  readonly compressedLength: number;
  readonly compressionRatio: number;
  readonly dictionaryMap: ReadonlyMap<number, readonly number[]>;
  readonly staticDictionaryId?: string;
  readonly metrics?: CompressionMetrics;
}
```

### `CompressionMetrics`

```typescript
interface CompressionMetrics {
  readonly discoveryTimeMs: number;
  readonly selectionTimeMs: number;
  readonly serializationTimeMs: number;
  readonly totalTimeMs: number;
  readonly peakMemoryBytes: number;
}
```

### `DiscoveredPattern`

```typescript
interface DiscoveredPattern {
  readonly pattern: readonly number[];
  readonly length: number;
  readonly positions: readonly number[];
  readonly count: number;
}
```

### `StaticDictionary`

```typescript
interface StaticDictionary {
  id: string;
  version: string;
  name: string;
  description: string;
  entries: Map<number, readonly number[]>;
  patterns: Map<string, number>;
}
```

### `TokenInput`

```typescript
type TokenInput = readonly number[] | number[] | Uint32Array;
```

---

## Constants

### `DEFAULT_CONFIG`

Default configuration values.

```typescript
const DEFAULT_CONFIG: Required<Omit<CompressionConfig, 'staticDictionary'>> = {
  minSubsequenceLength: 2,
  maxSubsequenceLength: 8,
  selectionMode: 'greedy',
  beamWidth: 8,
  hierarchicalEnabled: true,
  hierarchicalMaxDepth: 3,
  streamingThreshold: 50000,
  maxMemoryMb: 256,
  verify: false,
  dictStartToken: 0xFFFFFFF0,
  dictEndToken: 0xFFFFFFF1,
  nextMetaToken: 0xFFFF0000,
};
```

### `VERSION`

SDK version string.

```typescript
const VERSION: string = '0.1.0';
```
