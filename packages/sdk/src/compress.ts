/**
 * High-level compression API.
 */

import { getWasm, isWasmInitialized, initWasm } from './wasm/loader.js';
import type { CompressionResultWasm } from './wasm/loader.js';
import { type CompressionConfig, mergeConfig, toWasmConfig, DEFAULT_CONFIG } from './config.js';
import {
  type CompressionResult,
  type TokenInput,
  type DiscoveredPattern,
  normalizeTokens,
} from './types.js';
import { loadStaticDictionary, type StaticDictionary } from './dictionaries/index.js';

/**
 * Compress a token sequence.
 *
 * @param tokens - The token sequence to compress (Array, Uint32Array, or similar)
 * @param config - Optional compression configuration
 * @returns Promise resolving to compression result
 *
 * @example
 * ```typescript
 * import { compress, decompress, initWasm } from '@small-ltsc/sdk';
 *
 * await initWasm();
 *
 * const tokens = [1, 2, 3, 1, 2, 3, 1, 2, 3];
 * const result = await compress(tokens);
 *
 * console.log(`Compressed ${result.originalLength} -> ${result.compressedLength}`);
 * console.log(`Ratio: ${(result.compressionRatio * 100).toFixed(1)}%`);
 * ```
 */
export async function compress(
  tokens: TokenInput,
  config?: CompressionConfig
): Promise<CompressionResult> {
  // Auto-initialize if not already done
  if (!isWasmInitialized()) {
    await initWasm();
  }

  const mergedConfig = mergeConfig(config);
  const inputTokens = normalizeTokens(tokens);

  // Handle static dictionary if specified
  let staticDictId: string | undefined;
  if (mergedConfig.staticDictionary) {
    if (typeof mergedConfig.staticDictionary === 'string') {
      // Load built-in dictionary (pre-load to validate it exists)
      await loadStaticDictionary(
        mergedConfig.staticDictionary as Parameters<typeof loadStaticDictionary>[0]
      );
      staticDictId = mergedConfig.staticDictionary;
      // TODO: Apply static dictionary patterns in WASM core
    } else {
      staticDictId = (mergedConfig.staticDictionary as StaticDictionary).id;
    }
  }

  // Check if streaming should be used
  if (inputTokens.length > mergedConfig.streamingThreshold) {
    return compressStreaming(inputTokens, mergedConfig, staticDictId);
  }

  // Direct compression
  const wasm = getWasm();
  const startTime = performance.now();

  const wasmConfig = toWasmConfig(mergedConfig);
  const wasmResult = wasm.compress(inputTokens, wasmConfig);

  const endTime = performance.now();

  return convertWasmResult(wasmResult, staticDictId, endTime - startTime);
}

/**
 * Internal streaming compression for large inputs.
 */
async function compressStreaming(
  tokens: Uint32Array,
  config: Required<Omit<CompressionConfig, 'staticDictionary'>> & {
    staticDictionary?: string | StaticDictionary;
  },
  staticDictId?: string
): Promise<CompressionResult> {
  const wasm = getWasm();
  const wasmConfig = toWasmConfig(config);

  const startTime = performance.now();

  // Create streaming compressor
  const compressor = new wasm.StreamingCompressor(wasmConfig);

  // Process in chunks
  const chunkSize = 32768;
  for (let i = 0; i < tokens.length; i += chunkSize) {
    const end = Math.min(i + chunkSize, tokens.length);
    const chunk = tokens.subarray(i, end);
    compressor.add_chunk(chunk);
  }

  // Finish and get result
  const wasmResult = compressor.finish();
  const endTime = performance.now();

  return convertWasmResult(wasmResult, staticDictId, endTime - startTime);
}

/**
 * Convert WASM result to SDK result format.
 */
function convertWasmResult(
  wasmResult: CompressionResultWasm,
  staticDictId: string | undefined,
  totalTimeMs: number
): CompressionResult {
  const serializedTokens = Array.from(wasmResult.getSerializedTokens());
  const dictionaryTokens = Array.from(wasmResult.getDictionaryTokens());
  const bodyTokens = Array.from(wasmResult.getBodyTokens());
  const originalTokens = Array.from(wasmResult.getOriginalTokens());

  // Build dictionary map from serialized tokens
  const dictionaryMap = buildDictionaryMap(dictionaryTokens);

  return {
    originalTokens,
    serializedTokens,
    dictionaryTokens,
    bodyTokens,
    originalLength: wasmResult.original_length,
    compressedLength: wasmResult.compressed_length,
    compressionRatio: wasmResult.compression_ratio,
    dictionaryMap,
    staticDictionaryId: staticDictId ?? wasmResult.getStaticDictionaryId() ?? undefined,
    metrics: {
      discoveryTimeMs: 0, // Not tracked individually in current implementation
      selectionTimeMs: 0,
      serializationTimeMs: 0,
      totalTimeMs,
      peakMemoryBytes: 0,
    },
  };
}

/**
 * Build dictionary map from serialized dictionary tokens.
 */
function buildDictionaryMap(
  dictionaryTokens: readonly number[]
): ReadonlyMap<number, readonly number[]> {
  const map = new Map<number, readonly number[]>();

  if (dictionaryTokens.length === 0) {
    return map;
  }

  const dictStart = DEFAULT_CONFIG.dictStartToken;
  const dictEnd = DEFAULT_CONFIG.dictEndToken;

  let pos = 0;

  // Find dictionary start
  while (pos < dictionaryTokens.length && dictionaryTokens[pos] !== dictStart) {
    pos++;
  }
  pos++; // Skip start token

  // Parse entries
  while (pos < dictionaryTokens.length && dictionaryTokens[pos] !== dictEnd) {
    const metaToken = dictionaryTokens[pos++];
    const length = dictionaryTokens[pos++];

    if (pos + length > dictionaryTokens.length) {
      break;
    }

    const definition = dictionaryTokens.slice(pos, pos + length);
    map.set(metaToken, definition);
    pos += length;
  }

  return map;
}

/**
 * Discover patterns in a token sequence without compressing.
 *
 * Useful for analysis, building static dictionaries, or understanding
 * what patterns would be compressed.
 *
 * @param tokens - The token sequence to analyze
 * @param minLength - Minimum pattern length (default: 2)
 * @param maxLength - Maximum pattern length (default: 8)
 * @returns Array of discovered patterns sorted by potential savings
 */
export async function discoverPatterns(
  tokens: TokenInput,
  minLength = 2,
  maxLength = 8
): Promise<DiscoveredPattern[]> {
  if (!isWasmInitialized()) {
    await initWasm();
  }

  const wasm = getWasm();
  const inputTokens = normalizeTokens(tokens);

  const result = wasm.discover_patterns(inputTokens, minLength, maxLength);

  // Parse result from WASM (returns JSON-serializable value)
  return result as DiscoveredPattern[];
}
