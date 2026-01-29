/**
 * Tests for streaming compression API.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  createStreamingCompressor,
  compressStream,
  processInChunks,
} from '../src/streaming.js';

// Mock the WASM module
vi.mock('../src/wasm/loader.js', () => {
  let initialized = false;

  const mockCompressor = {
    add_chunk: vi.fn(),
    finish: vi.fn(() => ({
      original_length: 15,
      compressed_length: 10,
      compression_ratio: 0.67,
      getSerializedTokens: () => new Uint32Array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
      getDictionaryTokens: () => new Uint32Array([]),
      getBodyTokens: () => new Uint32Array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
      getOriginalTokens: () => new Uint32Array([1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3]),
      getStaticDictionaryId: () => null,
    })),
    memory_usage: vi.fn(() => 1024),
  };

  return {
    initWasm: vi.fn(async () => {
      initialized = true;
    }),
    isWasmInitialized: vi.fn(() => initialized),
    getWasm: vi.fn(() => ({
      StreamingCompressor: vi.fn().mockImplementation(() => mockCompressor),
    })),
  };
});

describe('createStreamingCompressor', () => {
  it('should create a streaming compressor', async () => {
    const compressor = await createStreamingCompressor();

    expect(compressor).toBeDefined();
    expect(typeof compressor.addChunk).toBe('function');
    expect(typeof compressor.finish).toBe('function');
    expect(typeof compressor.memoryUsage).toBe('function');
    expect(typeof compressor.isFinished).toBe('function');
  });

  it('should accept configuration', async () => {
    const compressor = await createStreamingCompressor({
      maxSubsequenceLength: 10,
      selectionMode: 'optimal',
    });

    expect(compressor).toBeDefined();
  });

  it('should track finished state', async () => {
    const compressor = await createStreamingCompressor();

    expect(compressor.isFinished()).toBe(false);

    await compressor.addChunk([1, 2, 3]);
    expect(compressor.isFinished()).toBe(false);

    await compressor.finish();
    expect(compressor.isFinished()).toBe(true);
  });

  it('should prevent adding chunks after finish', async () => {
    const compressor = await createStreamingCompressor();

    await compressor.addChunk([1, 2, 3]);
    await compressor.finish();

    await expect(compressor.addChunk([4, 5, 6])).rejects.toThrow(
      'Cannot add chunks to a finished compressor'
    );
  });

  it('should prevent finishing twice', async () => {
    const compressor = await createStreamingCompressor();

    await compressor.addChunk([1, 2, 3]);
    await compressor.finish();

    await expect(compressor.finish()).rejects.toThrow(
      'Compressor has already been finished'
    );
  });
});

describe('compressStream', () => {
  it('should compress async iterable of chunks', async () => {
    async function* tokenGenerator() {
      yield [1, 2, 3, 1, 2, 3];
      yield [1, 2, 3];
      yield [1, 2, 3, 1, 2, 3];
    }

    const result = await compressStream(tokenGenerator());

    expect(result).toBeDefined();
    expect(typeof result.compressionRatio).toBe('number');
  });
});

describe('processInChunks', () => {
  it('should process tokens in chunks', async () => {
    const tokens = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const chunkSize = 3;
    const chunks: Uint32Array[] = [];

    await processInChunks(tokens, chunkSize, async (chunk, index) => {
      chunks.push(chunk);
      return chunk.length;
    });

    expect(chunks.length).toBe(4); // 10 tokens / 3 per chunk = 4 chunks
    expect(chunks[0].length).toBe(3);
    expect(chunks[3].length).toBe(1); // Last chunk has 1 token
  });

  it('should provide correct indices', async () => {
    const tokens = [1, 2, 3, 4, 5, 6];
    const indices: number[] = [];

    await processInChunks(tokens, 2, async (chunk, index) => {
      indices.push(index);
      return index;
    });

    expect(indices).toEqual([0, 2, 4]);
  });
});
