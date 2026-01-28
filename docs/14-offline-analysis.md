# Offline Analysis Pipeline

## Embedding Providers

Supported providers (offline only):

- HuggingFace/Sentence-Transformers (default: BAAI/bge-large-en-v1.5)
- Ollama (default: nomic-embed-text)
- OpenAI (text-embedding-3-small / 3-large)
- Voyage (experimental)
- Cohere (experimental)

Providers are pluggable via `EmbeddingProvider`.

## Caching

SQLite cache with optional zstd compression and float16/float32 precision.

Cache key = sha256(provider + model + normalized text + dimensions + version).

Redis cache is available for distributed workloads (optional).

## Corpus Format

Primary format: JSONL with schema:

```
{"id": "...", "text": "...", "domain": "code|policy|documentation|natural_language", "language": "..."}
```

Directory loaders and manifests are supported.

## Static Dictionary Builder

- Preprocess corpus (dedup, tokenize, filter)
- Compute document weights with embeddings + clustering
- Rank patterns by weighted savings
- Emit dictionary artifacts for runtime use
