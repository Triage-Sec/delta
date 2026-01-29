/**
 * Tests for type utilities.
 */

import { describe, it, expect } from 'vitest';
import { normalizeTokens, isTokenSeq } from '../src/types.js';

describe('normalizeTokens', () => {
  it('should handle array input', () => {
    const tokens = [1, 2, 3, 4, 5];
    const normalized = normalizeTokens(tokens);

    expect(normalized).toBeInstanceOf(Uint32Array);
    expect(Array.from(normalized)).toEqual(tokens);
  });

  it('should pass through Uint32Array', () => {
    const tokens = new Uint32Array([1, 2, 3, 4, 5]);
    const normalized = normalizeTokens(tokens);

    expect(normalized).toBe(tokens);
  });

  it('should handle empty array', () => {
    const normalized = normalizeTokens([]);
    expect(normalized.length).toBe(0);
  });

  it('should handle large arrays', () => {
    const tokens = Array.from({ length: 10000 }, (_, i) => i);
    const normalized = normalizeTokens(tokens);

    expect(normalized.length).toBe(10000);
    expect(normalized[0]).toBe(0);
    expect(normalized[9999]).toBe(9999);
  });
});

describe('isTokenSeq', () => {
  it('should accept Uint32Array', () => {
    expect(isTokenSeq(new Uint32Array([1, 2, 3]))).toBe(true);
  });

  it('should accept number array', () => {
    expect(isTokenSeq([1, 2, 3])).toBe(true);
  });

  it('should accept empty array', () => {
    expect(isTokenSeq([])).toBe(true);
  });

  it('should reject non-integer values', () => {
    expect(isTokenSeq([1.5, 2, 3])).toBe(false);
  });

  it('should reject negative values', () => {
    expect(isTokenSeq([-1, 2, 3])).toBe(false);
  });

  it('should reject strings', () => {
    expect(isTokenSeq(['1', '2', '3'])).toBe(false);
  });

  it('should reject mixed arrays', () => {
    expect(isTokenSeq([1, '2', 3])).toBe(false);
  });

  it('should reject non-arrays', () => {
    expect(isTokenSeq('123')).toBe(false);
    expect(isTokenSeq(123)).toBe(false);
    expect(isTokenSeq(null)).toBe(false);
    expect(isTokenSeq(undefined)).toBe(false);
    expect(isTokenSeq({})).toBe(false);
  });
});
