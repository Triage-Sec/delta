//! Configuration module for WASM exports.
//!
//! Provides configuration structures that can be passed from JavaScript.

use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;

/// WASM-specific configuration for memory and performance tuning.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[wasm_bindgen]
pub struct WasmConfig {
    /// Maximum memory usage in MB (default: 256)
    pub max_memory_mb: usize,
    /// Chunk size for streaming processing (default: 32768)
    pub chunk_size: usize,
    /// Enable streaming for inputs above threshold (default: 50000)
    pub streaming_threshold: usize,
}

impl Default for WasmConfig {
    fn default() -> Self {
        Self {
            max_memory_mb: 256,
            chunk_size: 32768,
            streaming_threshold: 50000,
        }
    }
}

#[wasm_bindgen]
impl WasmConfig {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        Self::default()
    }
}

/// Configuration passed from JavaScript for compression.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct JsCompressionConfig {
    /// Minimum pattern length
    pub min_subsequence_length: Option<usize>,
    /// Maximum pattern length
    pub max_subsequence_length: Option<usize>,
    /// Selection mode: "greedy", "optimal", "beam"
    pub selection_mode: Option<String>,
    /// Beam width for beam search
    pub beam_width: Option<usize>,
    /// Enable hierarchical compression
    pub hierarchical_enabled: Option<bool>,
    /// Maximum hierarchical depth
    pub hierarchical_max_depth: Option<usize>,
    /// Enable verification
    pub verify: Option<bool>,
    /// Dict start token ID
    pub dict_start_token: Option<u32>,
    /// Dict end token ID
    pub dict_end_token: Option<u32>,
    /// Next meta-token ID to use
    pub next_meta_token: Option<u32>,
}

impl JsCompressionConfig {
    /// Merge with default compression config.
    pub fn merge_with_defaults(&self) -> crate::types::CompressionConfig {
        let mut config = crate::types::CompressionConfig::default();

        if let Some(v) = self.min_subsequence_length {
            config.min_subsequence_length = v;
        }
        if let Some(v) = self.max_subsequence_length {
            config.max_subsequence_length = v;
        }
        if let Some(ref v) = self.selection_mode {
            config.selection_mode = v.clone();
        }
        if let Some(v) = self.beam_width {
            config.beam_width = v;
        }
        if let Some(v) = self.hierarchical_enabled {
            config.hierarchical_enabled = v;
        }
        if let Some(v) = self.hierarchical_max_depth {
            config.hierarchical_max_depth = v;
        }
        if let Some(v) = self.verify {
            config.verify = v;
        }
        if let Some(v) = self.dict_start_token {
            config.dict_start_token = v;
        }
        if let Some(v) = self.dict_end_token {
            config.dict_end_token = v;
        }

        config
    }
}
