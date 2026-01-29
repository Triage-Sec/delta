/**
 * Tests for configuration module.
 */

import { describe, it, expect } from 'vitest';
import {
  DEFAULT_CONFIG,
  mergeConfig,
  toWasmConfig,
  type CompressionConfig,
} from '../src/config.js';

describe('DEFAULT_CONFIG', () => {
  it('should have sensible defaults', () => {
    expect(DEFAULT_CONFIG.minSubsequenceLength).toBe(2);
    expect(DEFAULT_CONFIG.maxSubsequenceLength).toBe(8);
    expect(DEFAULT_CONFIG.selectionMode).toBe('greedy');
    expect(DEFAULT_CONFIG.beamWidth).toBe(8);
    expect(DEFAULT_CONFIG.hierarchicalEnabled).toBe(true);
    expect(DEFAULT_CONFIG.hierarchicalMaxDepth).toBe(3);
    expect(DEFAULT_CONFIG.verify).toBe(false);
  });
});

describe('mergeConfig', () => {
  it('should return defaults when no config provided', () => {
    const config = mergeConfig();
    expect(config).toEqual(expect.objectContaining(DEFAULT_CONFIG));
  });

  it('should merge user config with defaults', () => {
    const userConfig: CompressionConfig = {
      minSubsequenceLength: 3,
      maxSubsequenceLength: 10,
    };

    const config = mergeConfig(userConfig);

    expect(config.minSubsequenceLength).toBe(3);
    expect(config.maxSubsequenceLength).toBe(10);
    expect(config.selectionMode).toBe('greedy'); // Default
  });

  it('should override all specified fields', () => {
    const userConfig: CompressionConfig = {
      minSubsequenceLength: 4,
      maxSubsequenceLength: 12,
      selectionMode: 'optimal',
      beamWidth: 16,
      hierarchicalEnabled: false,
      verify: true,
    };

    const config = mergeConfig(userConfig);

    expect(config.minSubsequenceLength).toBe(4);
    expect(config.maxSubsequenceLength).toBe(12);
    expect(config.selectionMode).toBe('optimal');
    expect(config.beamWidth).toBe(16);
    expect(config.hierarchicalEnabled).toBe(false);
    expect(config.verify).toBe(true);
  });
});

describe('toWasmConfig', () => {
  it('should convert SDK config to WASM format', () => {
    const config: CompressionConfig = {
      minSubsequenceLength: 3,
      maxSubsequenceLength: 10,
      selectionMode: 'optimal',
      verify: true,
    };

    const wasmConfig = toWasmConfig(config);

    expect(wasmConfig.min_subsequence_length).toBe(3);
    expect(wasmConfig.max_subsequence_length).toBe(10);
    expect(wasmConfig.selection_mode).toBe('optimal');
    expect(wasmConfig.verify).toBe(true);
  });

  it('should handle undefined values', () => {
    const config: CompressionConfig = {};
    const wasmConfig = toWasmConfig(config);

    expect(wasmConfig.min_subsequence_length).toBeUndefined();
    expect(wasmConfig.max_subsequence_length).toBeUndefined();
  });
});
