/**
 * WASM module loader with cross-platform support.
 *
 * Handles loading the WebAssembly module in browser, Node.js, and Deno environments.
 */

// Deno global type declaration
declare const Deno: { version: { deno: string } } | undefined;

// Type definitions for the WASM exports
export interface WasmExports {
  memory: WebAssembly.Memory;
  compress: (tokens: Uint32Array, config: unknown) => CompressionResultWasm;
  decompress: (tokens: Uint32Array, config: unknown) => Uint32Array;
  discover_patterns: (
    tokens: Uint32Array,
    minLength: number,
    maxLength: number
  ) => unknown;
  version: () => string;
  StreamingCompressor: new (config: unknown) => StreamingCompressorWasm;
}

export interface CompressionResultWasm {
  compression_ratio: number;
  tokens_saved: number;
  original_length: number;
  compressed_length: number;
  getSerializedTokens: () => Uint32Array;
  getDictionaryTokens: () => Uint32Array;
  getBodyTokens: () => Uint32Array;
  getOriginalTokens: () => Uint32Array;
  getStaticDictionaryId: () => string | null;
}

export interface StreamingCompressorWasm {
  add_chunk: (tokens: Uint32Array) => void;
  finish: () => CompressionResultWasm;
  memory_usage: () => number;
}

// Global state
let wasmModule: WebAssembly.Module | null = null;
let wasmInstance: WasmExports | null = null;
let initPromise: Promise<void> | null = null;

/**
 * Detect the current runtime environment.
 */
function detectEnvironment(): 'browser' | 'node' | 'deno' {
  if (typeof Deno !== 'undefined') {
    return 'deno';
  }
  if (typeof window !== 'undefined' && typeof window.document !== 'undefined') {
    return 'browser';
  }
  if (
    typeof process !== 'undefined' &&
    process.versions &&
    process.versions.node
  ) {
    return 'node';
  }
  return 'browser'; // Default fallback
}

/**
 * Load WASM bytes based on environment.
 */
async function loadWasmBytes(): Promise<ArrayBuffer> {
  const env = detectEnvironment();

  // Get the path to the WASM file
  // This will be populated during the build process
  const wasmPath = new URL('./small_ltsc_core_bg.wasm', import.meta.url);

  switch (env) {
    case 'browser': {
      const response = await fetch(wasmPath);
      if (!response.ok) {
        throw new Error(`Failed to fetch WASM: ${response.statusText}`);
      }
      return response.arrayBuffer();
    }

    case 'node': {
      // Dynamic import for Node.js fs module
      const { readFile } = await import('node:fs/promises');
      const { fileURLToPath } = await import('node:url');
      const path = fileURLToPath(wasmPath);
      const buffer = await readFile(path);
      return buffer.buffer.slice(
        buffer.byteOffset,
        buffer.byteOffset + buffer.byteLength
      );
    }

    case 'deno': {
      // Deno can use fetch for local files
      const response = await fetch(wasmPath);
      if (!response.ok) {
        throw new Error(`Failed to fetch WASM: ${response.statusText}`);
      }
      return response.arrayBuffer();
    }

    default:
      throw new Error(`Unsupported environment: ${env}`);
  }
}

/**
 * Create import object for WASM instantiation.
 */
function createImports(): WebAssembly.Imports {
  return {
    env: {
      // Logging functions for debugging
      console_log: (ptr: number, len: number) => {
        // In production, this would decode the string from memory
        console.log('[WASM]', ptr, len);
      },
    },
    wbg: {
      // wasm-bindgen imports will be added here during build
      __wbindgen_throw: (ptr: number, len: number) => {
        throw new Error(`WASM error at ${ptr} len ${len}`);
      },
    },
  };
}

/**
 * Initialize the WASM module.
 *
 * This function is idempotent - calling it multiple times will only
 * initialize once.
 *
 * @throws Error if WASM loading fails
 */
export async function initWasm(): Promise<void> {
  if (wasmInstance) {
    return; // Already initialized
  }

  if (initPromise) {
    return initPromise; // Initialization in progress
  }

  initPromise = (async () => {
    try {
      const wasmBytes = await loadWasmBytes();
      wasmModule = await WebAssembly.compile(wasmBytes);
      const imports = createImports();
      const instance = await WebAssembly.instantiate(wasmModule, imports);
      wasmInstance = instance.exports as unknown as WasmExports;
    } catch (error) {
      initPromise = null; // Allow retry on failure
      throw error;
    }
  })();

  return initPromise;
}

/**
 * Initialize from pre-compiled WASM module.
 *
 * Useful for environments where the WASM is bundled differently.
 *
 * @param module - Pre-compiled WebAssembly.Module
 */
export async function initWasmFromModule(
  module: WebAssembly.Module
): Promise<void> {
  if (wasmInstance) {
    return;
  }

  wasmModule = module;
  const imports = createImports();
  const instance = await WebAssembly.instantiate(module, imports);
  wasmInstance = instance.exports as unknown as WasmExports;
}

/**
 * Initialize from WASM bytes.
 *
 * @param bytes - WASM binary as ArrayBuffer or Uint8Array
 */
export async function initWasmFromBytes(
  bytes: ArrayBuffer | Uint8Array
): Promise<void> {
  if (wasmInstance) {
    return;
  }

  const buffer = bytes instanceof Uint8Array
    ? new Uint8Array(bytes).buffer
    : bytes;
  wasmModule = await WebAssembly.compile(buffer as ArrayBuffer);
  const imports = createImports();
  const instance = await WebAssembly.instantiate(wasmModule, imports);
  wasmInstance = instance.exports as unknown as WasmExports;
}

/**
 * Get the initialized WASM exports.
 *
 * @throws Error if WASM is not initialized
 */
export function getWasm(): WasmExports {
  if (!wasmInstance) {
    throw new Error(
      'WASM not initialized. Call initWasm() first and await its completion.'
    );
  }
  return wasmInstance;
}

/**
 * Check if WASM is initialized.
 */
export function isWasmInitialized(): boolean {
  return wasmInstance !== null;
}

/**
 * Reset the WASM instance (mainly for testing).
 */
export function resetWasm(): void {
  wasmInstance = null;
  wasmModule = null;
  initPromise = null;
}

/**
 * Get WASM module version.
 */
export function getWasmVersion(): string {
  const wasm = getWasm();
  return wasm.version();
}

// Types are already exported at their interface declarations above
