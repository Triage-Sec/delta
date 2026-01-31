/**
 * Worker thread support for non-blocking compression.
 *
 * Provides utilities for running compression in Web Workers (browser)
 * or Worker threads (Node.js) to avoid blocking the main thread.
 */

import type { CompressionConfig, DecompressionConfig } from './config.js';
import type { CompressionResult, TokenInput } from './types.js';

/**
 * Message types for worker communication.
 */
export type WorkerRequest =
  | { type: 'compress'; requestId: string; tokens: number[]; config?: CompressionConfig }
  | { type: 'decompress'; requestId: string; tokens: number[]; config?: DecompressionConfig }
  | { type: 'init' };

export type WorkerResponse =
  | { type: 'compress'; requestId: string; result: CompressionResult; error: null }
  | { type: 'compress'; requestId: string; result: null; error: string }
  | { type: 'decompress'; requestId: string; result: readonly number[]; error: null }
  | { type: 'decompress'; requestId: string; result: null; error: string }
  | { type: 'init'; success: boolean; error: string | null };

/**
 * Pending request tracking.
 */
interface PendingRequest<T> {
  resolve: (value: T) => void;
  reject: (error: Error) => void;
}

/**
 * Worker pool for parallel compression.
 */
export interface WorkerPool {
  /**
   * Compress tokens using a worker.
   */
  compress(tokens: TokenInput, config?: CompressionConfig): Promise<CompressionResult>;

  /**
   * Decompress tokens using a worker.
   */
  decompress(tokens: TokenInput, config?: DecompressionConfig): Promise<readonly number[]>;

  /**
   * Terminate all workers in the pool.
   */
  terminate(): void;

  /**
   * Get the number of workers in the pool.
   */
  size(): number;
}

/**
 * Create a worker pool for parallel compression.
 *
 * @param workerCount - Number of workers to create (default: navigator.hardwareConcurrency or 4)
 * @returns Worker pool instance
 *
 * @example
 * ```typescript
 * import { createWorkerPool } from '@delta-ltsc/sdk';
 *
 * const pool = await createWorkerPool(4);
 *
 * // Compress without blocking main thread
 * const result = await pool.compress(tokens);
 *
 * // Clean up when done
 * pool.terminate();
 * ```
 */
export async function createWorkerPool(workerCount?: number): Promise<WorkerPool> {
  const count = workerCount ?? (typeof navigator !== 'undefined' ? navigator.hardwareConcurrency : 4) ?? 4;

  // Detect environment
  const isNode =
    typeof process !== 'undefined' &&
    process.versions &&
    process.versions.node;

  if (isNode) {
    return createNodeWorkerPool(count);
  } else {
    return createBrowserWorkerPool(count);
  }
}

/**
 * Create a browser-based worker pool.
 */
async function createBrowserWorkerPool(count: number): Promise<WorkerPool> {
  const workers: Worker[] = [];
  const pendingRequests = new Map<string, PendingRequest<unknown>>();
  let nextWorkerIndex = 0;

  // Worker script as a blob URL
  const workerScript = `
    let wasm = null;

    self.onmessage = async function(event) {
      const request = event.data;

      if (request.type === 'init') {
        try {
          const { initWasm } = await import('@delta-ltsc/sdk/wasm');
          await initWasm();
          self.postMessage({ type: 'init', success: true, error: null });
        } catch (error) {
          self.postMessage({ type: 'init', success: false, error: String(error) });
        }
        return;
      }

      if (request.type === 'compress') {
        try {
          const { compress } = await import('@delta-ltsc/sdk');
          const result = await compress(request.tokens, request.config);
          self.postMessage({ type: 'compress', requestId: request.requestId, result, error: null });
        } catch (error) {
          self.postMessage({ type: 'compress', requestId: request.requestId, result: null, error: String(error) });
        }
        return;
      }

      if (request.type === 'decompress') {
        try {
          const { decompress } = await import('@delta-ltsc/sdk');
          const result = await decompress(request.tokens, request.config);
          self.postMessage({ type: 'decompress', requestId: request.requestId, result, error: null });
        } catch (error) {
          self.postMessage({ type: 'decompress', requestId: request.requestId, result: null, error: String(error) });
        }
        return;
      }
    };
  `;

  const blob = new Blob([workerScript], { type: 'application/javascript' });
  const workerUrl = URL.createObjectURL(blob);

  // Create workers
  for (let i = 0; i < count; i++) {
    const worker = new Worker(workerUrl, { type: 'module' });

    worker.onmessage = (event: MessageEvent<WorkerResponse>) => {
      const response = event.data;

      if (response.type === 'init') {
        return;
      }

      const pending = pendingRequests.get(response.requestId);
      if (!pending) return;

      pendingRequests.delete(response.requestId);

      if (response.error) {
        pending.reject(new Error(response.error));
      } else {
        pending.resolve(response.result);
      }
    };

    // Initialize worker
    worker.postMessage({ type: 'init' });
    workers.push(worker);
  }

  // Get next worker (round-robin)
  const getWorker = (): Worker => {
    const worker = workers[nextWorkerIndex];
    nextWorkerIndex = (nextWorkerIndex + 1) % workers.length;
    return worker;
  };

  // Generate request ID
  const generateId = (): string => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  return {
    compress(tokens: TokenInput, config?: CompressionConfig): Promise<CompressionResult> {
      return new Promise((resolve, reject) => {
        const requestId = generateId();
        pendingRequests.set(requestId, { resolve, reject } as PendingRequest<unknown>);

        const worker = getWorker();
        worker.postMessage({
          type: 'compress',
          requestId,
          tokens: Array.from(tokens as ArrayLike<number>),
          config,
        });
      });
    },

    decompress(tokens: TokenInput, config?: DecompressionConfig): Promise<readonly number[]> {
      return new Promise((resolve, reject) => {
        const requestId = generateId();
        pendingRequests.set(requestId, { resolve, reject } as PendingRequest<unknown>);

        const worker = getWorker();
        worker.postMessage({
          type: 'decompress',
          requestId,
          tokens: Array.from(tokens as ArrayLike<number>),
          config,
        });
      });
    },

    terminate(): void {
      workers.forEach((w) => w.terminate());
      workers.length = 0;
      URL.revokeObjectURL(workerUrl);
    },

    size(): number {
      return workers.length;
    },
  };
}

/**
 * Create a Node.js-based worker pool.
 */
async function createNodeWorkerPool(count: number): Promise<WorkerPool> {
  // Import worker_threads dynamically
  const { Worker } = await import('node:worker_threads');

  const workers: InstanceType<typeof Worker>[] = [];
  const pendingRequests = new Map<string, PendingRequest<unknown>>();
  let nextWorkerIndex = 0;

  // Worker script for Node.js
  const workerScript = `
    const { parentPort } = require('worker_threads');

    parentPort.on('message', async (request) => {
      if (request.type === 'init') {
        try {
          const { initWasm } = await import('@delta-ltsc/sdk/wasm');
          await initWasm();
          parentPort.postMessage({ type: 'init', success: true, error: null });
        } catch (error) {
          parentPort.postMessage({ type: 'init', success: false, error: String(error) });
        }
        return;
      }

      if (request.type === 'compress') {
        try {
          const { compress } = await import('@delta-ltsc/sdk');
          const result = await compress(request.tokens, request.config);
          parentPort.postMessage({ type: 'compress', requestId: request.requestId, result, error: null });
        } catch (error) {
          parentPort.postMessage({ type: 'compress', requestId: request.requestId, result: null, error: String(error) });
        }
        return;
      }

      if (request.type === 'decompress') {
        try {
          const { decompress } = await import('@delta-ltsc/sdk');
          const result = await decompress(request.tokens, request.config);
          parentPort.postMessage({ type: 'decompress', requestId: request.requestId, result, error: null });
        } catch (error) {
          parentPort.postMessage({ type: 'decompress', requestId: request.requestId, result: null, error: String(error) });
        }
        return;
      }
    });
  `;

  // Create workers
  for (let i = 0; i < count; i++) {
    const worker = new Worker(workerScript, { eval: true });

    worker.on('message', (response: WorkerResponse) => {
      if (response.type === 'init') {
        return;
      }

      const pending = pendingRequests.get(response.requestId);
      if (!pending) return;

      pendingRequests.delete(response.requestId);

      if (response.error) {
        pending.reject(new Error(response.error));
      } else {
        pending.resolve(response.result);
      }
    });

    // Initialize worker
    worker.postMessage({ type: 'init' });
    workers.push(worker);
  }

  const getWorker = () => {
    const worker = workers[nextWorkerIndex];
    nextWorkerIndex = (nextWorkerIndex + 1) % workers.length;
    return worker;
  };

  const generateId = (): string => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  return {
    compress(tokens: TokenInput, config?: CompressionConfig): Promise<CompressionResult> {
      return new Promise((resolve, reject) => {
        const requestId = generateId();
        pendingRequests.set(requestId, { resolve, reject } as PendingRequest<unknown>);

        const worker = getWorker();
        worker.postMessage({
          type: 'compress',
          requestId,
          tokens: Array.from(tokens as ArrayLike<number>),
          config,
        });
      });
    },

    decompress(tokens: TokenInput, config?: DecompressionConfig): Promise<readonly number[]> {
      return new Promise((resolve, reject) => {
        const requestId = generateId();
        pendingRequests.set(requestId, { resolve, reject } as PendingRequest<unknown>);

        const worker = getWorker();
        worker.postMessage({
          type: 'decompress',
          requestId,
          tokens: Array.from(tokens as ArrayLike<number>),
          config,
        });
      });
    },

    terminate(): void {
      workers.forEach((w) => w.terminate());
      workers.length = 0;
    },

    size(): number {
      return workers.length;
    },
  };
}

/**
 * Compress tokens in a worker (single-use helper).
 *
 * Creates a temporary worker, runs compression, and terminates.
 * For multiple compressions, use createWorkerPool instead.
 *
 * @param tokens - Token sequence to compress
 * @param config - Optional compression configuration
 * @returns Promise resolving to compression result
 */
export async function compressInWorker(
  tokens: TokenInput,
  config?: CompressionConfig
): Promise<CompressionResult> {
  const pool = await createWorkerPool(1);

  try {
    return await pool.compress(tokens, config);
  } finally {
    pool.terminate();
  }
}

/**
 * Decompress tokens in a worker (single-use helper).
 */
export async function decompressInWorker(
  tokens: TokenInput,
  config?: DecompressionConfig
): Promise<readonly number[]> {
  const pool = await createWorkerPool(1);

  try {
    return await pool.decompress(tokens, config);
  } finally {
    pool.terminate();
  }
}
