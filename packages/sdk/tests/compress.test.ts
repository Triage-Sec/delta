/**
 * Tests for compression and decompression APIs.
 */

import { describe, it, expect, beforeAll, vi } from 'vitest';
import {
  compress,
  decompress,
  discoverPatterns,
  extractDictionary,
  extractBody,
  isCompressed,
  type CompressionConfig,
} from '../src/index.js';

// Mock the WASM module for testing without actual WASM
vi.mock('../src/wasm/loader.js', () => {
  let initialized = false;

  return {
    initWasm: vi.fn(async () => {
      initialized = true;
    }),
    isWasmInitialized: vi.fn(() => initialized),
    getWasm: vi.fn(() => ({
      compress: vi.fn((tokens: Uint32Array, config: unknown) => {
        // Simple mock compression
        const result = {
          original_length: tokens.length,
          compressed_length: tokens.length,
          compression_ratio: 1.0,
          getSerializedTokens: () => tokens,
          getDictionaryTokens: () => new Uint32Array([]),
          getBodyTokens: () => tokens,
          getOriginalTokens: () => tokens,
          getStaticDictionaryId: () => null,
        };
        return result;
      }),
      decompress: vi.fn((tokens: Uint32Array, config: unknown) => tokens),
      discover_patterns: vi.fn(() => []),
      version: vi.fn(() => '0.1.0'),
      StreamingCompressor: vi.fn().mockImplementation(() => ({
        add_chunk: vi.fn(),
        finish: vi.fn(() => ({
          original_length: 0,
          compressed_length: 0,
          compression_ratio: 1.0,
          getSerializedTokens: () => new Uint32Array([]),
          getDictionaryTokens: () => new Uint32Array([]),
          getBodyTokens: () => new Uint32Array([]),
          getOriginalTokens: () => new Uint32Array([]),
          getStaticDictionaryId: () => null,
        })),
        memory_usage: vi.fn(() => 0),
      })),
    })),
    resetWasm: vi.fn(() => {
      initialized = false;
    }),
  };
});

describe('compress', () => {
  it('should compress simple repeated pattern', async () => {
    const tokens = [1, 2, 3, 1, 2, 3, 1, 2, 3];
    const result = await compress(tokens);

    expect(result).toBeDefined();
    expect(result.originalLength).toBe(9);
    expect(typeof result.compressionRatio).toBe('number');
  });

  it('should accept array input', async () => {
    const tokens = [1, 2, 3, 4, 5];
    const result = await compress(tokens);
    expect(result.originalTokens).toEqual(tokens);
  });

  it('should accept Uint32Array input', async () => {
    const tokens = new Uint32Array([1, 2, 3, 4, 5]);
    const result = await compress(tokens);
    expect(result.originalLength).toBe(5);
  });

  it('should respect configuration options', async () => {
    const tokens = [1, 2, 3, 1, 2, 3];
    const config: CompressionConfig = {
      minSubsequenceLength: 3,
      maxSubsequenceLength: 6,
      selectionMode: 'greedy',
      verify: true,
    };

    const result = await compress(tokens, config);
    expect(result).toBeDefined();
  });

  it('should handle empty input', async () => {
    const tokens: number[] = [];
    const result = await compress(tokens);
    expect(result.originalLength).toBe(0);
  });
});

describe('decompress', () => {
  it('should decompress to original tokens', async () => {
    const tokens = [1, 2, 3, 1, 2, 3];
    const compressed = await compress(tokens);
    const restored = await decompress(compressed.serializedTokens);

    expect(restored).toEqual(Array.from(tokens));
  });

  it('should handle uncompressed input', async () => {
    const tokens = [1, 2, 3, 4, 5];
    const restored = await decompress(tokens);
    expect(restored).toEqual(tokens);
  });
});

describe('discoverPatterns', () => {
  it('should discover patterns in token sequence', async () => {
    const tokens = [1, 2, 3, 1, 2, 3, 1, 2, 3];
    const patterns = await discoverPatterns(tokens);

    expect(Array.isArray(patterns)).toBe(true);
  });

  it('should respect length bounds', async () => {
    const tokens = [1, 2, 3, 1, 2, 3, 1, 2, 3];
    const patterns = await discoverPatterns(tokens, 2, 4);

    expect(Array.isArray(patterns)).toBe(true);
  });
});

describe('extractDictionary', () => {
  it('should extract dictionary from compressed tokens', async () => {
    // Simulated compressed format: [DICT_START, META, LEN, DEF..., DICT_END, BODY...]
    const dictStart = 0xfffffff0;
    const dictEnd = 0xfffffff1;
    const metaToken = 0xffff0000;

    const tokens = [
      dictStart,
      metaToken,
      3, // length
      1, 2, 3, // definition
      dictEnd,
      metaToken, // body
      4, 5,
    ];

    const dictionary = await extractDictionary(tokens);

    expect(dictionary.size).toBe(1);
    expect(dictionary.get(metaToken)).toEqual([1, 2, 3]);
  });

  it('should return empty map for uncompressed input', async () => {
    const tokens = [1, 2, 3, 4, 5];
    const dictionary = await extractDictionary(tokens);
    expect(dictionary.size).toBe(0);
  });
});

describe('extractBody', () => {
  it('should extract body from compressed tokens', () => {
    const dictStart = 0xfffffff0;
    const dictEnd = 0xfffffff1;

    const tokens = [
      dictStart,
      0xffff0000,
      2,
      1, 2,
      dictEnd,
      100, 101, 102, // body
    ];

    const body = extractBody(tokens);
    expect(body).toEqual([100, 101, 102]);
  });

  it('should return all tokens if no dictionary', () => {
    const tokens = [1, 2, 3, 4, 5];
    const body = extractBody(tokens);
    expect(body).toEqual(tokens);
  });
});

describe('isCompressed', () => {
  it('should detect compressed format', () => {
    const dictStart = 0xfffffff0;
    const tokens = [dictStart, 0xffff0000, 2, 1, 2, 0xfffffff1, 100];

    expect(isCompressed(tokens)).toBe(true);
  });

  it('should return false for uncompressed', () => {
    const tokens = [1, 2, 3, 4, 5];
    expect(isCompressed(tokens)).toBe(false);
  });
});
