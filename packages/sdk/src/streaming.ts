/**
 * Streaming compression API for large inputs.
 *
 * Provides a chunk-based interface for compressing token sequences
 * that are too large to fit in memory at once.
 */

import { getWasm, isWasmInitialized, initWasm } from './wasm/loader.js';
import type { StreamingCompressorWasm } from './wasm/loader.js';
import { type CompressionConfig, mergeConfig, toWasmConfig } from './config.js';
import {
  type CompressionResult,
  type TokenInput,
  normalizeTokens,
} from './types.js';

/**
 * Streaming compressor for processing large token sequences.
 *
 * @example
 * ```typescript
 * import { createStreamingCompressor, initWasm } from '@delta-ltsc/sdk';
 *
 * await initWasm();
 *
 * const compressor = createStreamingCompressor({
 *   maxSubsequenceLength: 8,
 * });
 *
 * // Add chunks as they become available
 * for await (const chunk of tokenStream) {
 *   await compressor.addChunk(chunk);
 * }
 *
 * // Finish and get result
 * const result = await compressor.finish();
 * ```
 */
export interface StreamingCompressor {
  /**
   * Add a chunk of tokens to the compressor.
   *
   * @param tokens - Chunk of tokens to add
   */
  addChunk(tokens: TokenInput): Promise<void>;

  /**
   * Finish compression and return the result.
   *
   * After calling finish(), the compressor cannot be reused.
   *
   * @returns Promise resolving to compression result
   */
  finish(): Promise<CompressionResult>;

  /**
   * Get the current memory usage in bytes.
   */
  memoryUsage(): number;

  /**
   * Check if the compressor has been finished.
   */
  isFinished(): boolean;
}

/**
 * Create a new streaming compressor.
 *
 * @param config - Optional compression configuration
 * @returns Streaming compressor instance
 */
export async function createStreamingCompressor(
  config?: CompressionConfig
): Promise<StreamingCompressor> {
  if (!isWasmInitialized()) {
    await initWasm();
  }

  const mergedConfig = mergeConfig(config);
  const wasmConfig = toWasmConfig(mergedConfig);

  const wasm = getWasm();
  const wasmCompressor = new wasm.StreamingCompressor(wasmConfig);

  return new StreamingCompressorImpl(wasmCompressor, mergedConfig);
}

/**
 * Internal implementation of StreamingCompressor.
 */
class StreamingCompressorImpl implements StreamingCompressor {
  private compressor: StreamingCompressorWasm;
  private config: Required<Omit<CompressionConfig, 'staticDictionary'>>;
  private finished = false;
  private totalChunks = 0;
  private totalTokens = 0;

  constructor(
    compressor: StreamingCompressorWasm,
    config: Required<Omit<CompressionConfig, 'staticDictionary'>>
  ) {
    this.compressor = compressor;
    this.config = config;
  }

  async addChunk(tokens: TokenInput): Promise<void> {
    if (this.finished) {
      throw new Error('Cannot add chunks to a finished compressor');
    }

    const normalizedTokens = normalizeTokens(tokens);
    this.compressor.add_chunk(normalizedTokens);
    this.totalChunks++;
    this.totalTokens += normalizedTokens.length;
  }

  async finish(): Promise<CompressionResult> {
    if (this.finished) {
      throw new Error('Compressor has already been finished');
    }

    this.finished = true;

    const startTime = performance.now();
    const wasmResult = this.compressor.finish();
    const endTime = performance.now();

    const serializedTokens = Array.from(wasmResult.getSerializedTokens());
    const dictionaryTokens = Array.from(wasmResult.getDictionaryTokens());
    const bodyTokens = Array.from(wasmResult.getBodyTokens());
    const originalTokens = Array.from(wasmResult.getOriginalTokens());

    // Build dictionary map
    const dictionaryMap = new Map<number, readonly number[]>();
    const dictStart = this.config.dictStartToken;
    const dictEnd = this.config.dictEndToken;

    let pos = 0;
    while (pos < dictionaryTokens.length && dictionaryTokens[pos] !== dictStart) {
      pos++;
    }
    pos++;

    while (pos < dictionaryTokens.length && dictionaryTokens[pos] !== dictEnd) {
      const metaToken = dictionaryTokens[pos++];
      const length = dictionaryTokens[pos++];
      if (pos + length > dictionaryTokens.length) break;
      const definition = dictionaryTokens.slice(pos, pos + length);
      dictionaryMap.set(metaToken, definition);
      pos += length;
    }

    return {
      originalTokens,
      serializedTokens,
      dictionaryTokens,
      bodyTokens,
      originalLength: wasmResult.original_length,
      compressedLength: wasmResult.compressed_length,
      compressionRatio: wasmResult.compression_ratio,
      dictionaryMap,
      staticDictionaryId: undefined,
      metrics: {
        discoveryTimeMs: 0,
        selectionTimeMs: 0,
        serializationTimeMs: 0,
        totalTimeMs: endTime - startTime,
        peakMemoryBytes: this.memoryUsage(),
      },
    };
  }

  memoryUsage(): number {
    return this.compressor.memory_usage();
  }

  isFinished(): boolean {
    return this.finished;
  }
}

/**
 * Process a token stream with streaming compression.
 *
 * Convenience function that handles creating the compressor and
 * processing an async iterable of token chunks.
 *
 * @param tokenStream - Async iterable of token chunks
 * @param config - Optional compression configuration
 * @returns Promise resolving to compression result
 */
export async function compressStream(
  tokenStream: AsyncIterable<TokenInput>,
  config?: CompressionConfig
): Promise<CompressionResult> {
  const compressor = await createStreamingCompressor(config);

  for await (const chunk of tokenStream) {
    await compressor.addChunk(chunk);
  }

  return compressor.finish();
}

/**
 * Process tokens in chunks with a callback.
 *
 * @param tokens - Full token sequence
 * @param chunkSize - Size of each chunk
 * @param callback - Callback for each chunk
 */
export async function processInChunks<T>(
  tokens: TokenInput,
  chunkSize: number,
  callback: (chunk: Uint32Array, index: number) => Promise<T>
): Promise<T[]> {
  const normalized = normalizeTokens(tokens);
  const results: T[] = [];

  for (let i = 0; i < normalized.length; i += chunkSize) {
    const end = Math.min(i + chunkSize, normalized.length);
    const chunk = normalized.subarray(i, end);
    const result = await callback(chunk, i);
    results.push(result);
  }

  return results;
}
