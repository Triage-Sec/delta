/**
 * WASM module exports.
 */

export {
  initWasm,
  initWasmFromModule,
  initWasmFromBytes,
  getWasm,
  isWasmInitialized,
  resetWasm,
  getWasmVersion,
} from './loader.js';

export type {
  WasmExports,
  CompressionResultWasm,
  StreamingCompressorWasm,
} from './loader.js';
