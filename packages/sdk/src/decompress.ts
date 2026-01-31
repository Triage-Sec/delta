/**
 * High-level decompression API.
 */

import { getWasm, isWasmInitialized, initWasm } from './wasm/loader.js';
import { type DecompressionConfig, DEFAULT_CONFIG } from './config.js';
import { type TokenInput, normalizeTokens } from './types.js';

/**
 * Decompress a compressed token sequence.
 *
 * @param tokens - The compressed token sequence
 * @param config - Optional decompression configuration
 * @returns Promise resolving to the original token sequence
 *
 * @example
 * ```typescript
 * import { compress, decompress, initWasm } from '@delta-ltsc/sdk';
 *
 * await initWasm();
 *
 * const tokens = [1, 2, 3, 1, 2, 3, 1, 2, 3];
 * const result = await compress(tokens);
 * const restored = await decompress(result.serializedTokens);
 *
 * console.assert(JSON.stringify(tokens) === JSON.stringify(restored));
 * ```
 */
export async function decompress(
  tokens: TokenInput,
  config?: DecompressionConfig
): Promise<readonly number[]> {
  // Auto-initialize if not already done
  if (!isWasmInitialized()) {
    await initWasm();
  }

  const wasm = getWasm();
  const inputTokens = normalizeTokens(tokens);

  const wasmConfig = {
    dict_start_token: config?.dictStartToken ?? DEFAULT_CONFIG.dictStartToken,
    dict_end_token: config?.dictEndToken ?? DEFAULT_CONFIG.dictEndToken,
  };

  const result = wasm.decompress(inputTokens, wasmConfig);
  return Array.from(result);
}

/**
 * Extract the dictionary from a compressed token sequence.
 *
 * @param tokens - The compressed token sequence
 * @param config - Optional decompression configuration
 * @returns Map of meta-tokens to their definitions
 */
export async function extractDictionary(
  tokens: TokenInput,
  config?: DecompressionConfig
): Promise<ReadonlyMap<number, readonly number[]>> {
  const inputTokens = normalizeTokens(tokens);
  const dictStart = config?.dictStartToken ?? DEFAULT_CONFIG.dictStartToken;
  const dictEnd = config?.dictEndToken ?? DEFAULT_CONFIG.dictEndToken;

  const map = new Map<number, readonly number[]>();

  // Find dictionary start
  const startIdx = inputTokens.indexOf(dictStart);
  if (startIdx === -1) {
    return map;
  }

  let pos = startIdx + 1;

  // Parse entries
  while (pos < inputTokens.length && inputTokens[pos] !== dictEnd) {
    const metaToken = inputTokens[pos++];
    const length = inputTokens[pos++];

    if (pos + length > inputTokens.length) {
      break;
    }

    const definition = Array.from(inputTokens.slice(pos, pos + length));
    map.set(metaToken, definition);
    pos += length;
  }

  return map;
}

/**
 * Extract the body tokens from a compressed sequence (without decompression).
 *
 * @param tokens - The compressed token sequence
 * @param config - Optional decompression configuration
 * @returns Body tokens with meta-token references
 */
export function extractBody(
  tokens: TokenInput,
  config?: DecompressionConfig
): readonly number[] {
  const inputTokens = normalizeTokens(tokens);
  const dictEnd = config?.dictEndToken ?? DEFAULT_CONFIG.dictEndToken;

  // Find dictionary end
  const endIdx = inputTokens.indexOf(dictEnd);
  if (endIdx === -1) {
    // No dictionary section - return all tokens
    return Array.from(inputTokens);
  }

  // Body is everything after the dictionary end token
  return Array.from(inputTokens.slice(endIdx + 1));
}

/**
 * Check if a token sequence appears to be compressed.
 *
 * Looks for the dictionary start token marker.
 *
 * @param tokens - The token sequence to check
 * @param config - Optional decompression configuration
 * @returns True if the sequence contains a dictionary section
 */
export function isCompressed(
  tokens: TokenInput,
  config?: DecompressionConfig
): boolean {
  const inputTokens = normalizeTokens(tokens);
  const dictStart = config?.dictStartToken ?? DEFAULT_CONFIG.dictStartToken;
  return inputTokens.includes(dictStart);
}
