from small import AnalysisConfig, OfflinePipelineConfig, run_offline_analysis
from small.embedding_cache import SQLiteCacheConfig, SQLiteEmbeddingCache

from small.corpus import CorpusDocument


def test_offline_pipeline_cache_stats(tmp_path):
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return
    # Use deterministic provider to avoid external dependencies in tests.
    class DeterministicProvider:
        def embed_single(self, text: str) -> list[float]:
            value = sum(ord(ch) for ch in text) % 997
            return [value / 997, (value + 1) / 997]

        def embed_batch(self, texts: list[str]) -> list[list[float]]:
            return [self.embed_single(text) for text in texts]

        def dimension(self) -> int:
            return 2

        def max_tokens(self) -> int:
            return 1024

        def normalize(self) -> bool:
            return True

        def model_id(self) -> str:
            return "deterministic-test"

    provider = DeterministicProvider()

    cache = SQLiteEmbeddingCache(SQLiteCacheConfig(path=str(tmp_path / "emb.db"), compression="none"))
    docs = [
        CorpusDocument(id="d1", text="hello world", domain="policy"),
        CorpusDocument(id="d2", text="hello world", domain="policy"),
    ]
    weights = run_offline_analysis(docs, provider, cache, AnalysisConfig(clusters=2), OfflinePipelineConfig())
    assert len(weights) == 2
    stats = cache.stats()
    assert stats["sets"] >= 1
    cache.close()
