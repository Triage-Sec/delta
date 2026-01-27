"""Small: Lossless Token Sequence Compression (LTSC)."""

from .compressor import compress, compress_python_source, decompress, decompress_with_dictionary
from .config import CompressionConfig
from .engine import CompressionEngine, default_engine
from .sequence import TokenSequence
from .serialization import SerializedOutput, serialize
from .training import TrainingExample, build_example, build_curriculum, generate_training_examples
from .vocab import VocabExtension, plan_vocab_extension
from .types import CompressionResult

__all__ = [
    "compress",
    "compress_python_source",
    "decompress",
    "decompress_with_dictionary",
    "CompressionConfig",
    "CompressionResult",
    "CompressionEngine",
    "TokenSequence",
    "default_engine",
    "SerializedOutput",
    "serialize",
    "TrainingExample",
    "build_example",
    "build_curriculum",
    "generate_training_examples",
    "VocabExtension",
    "plan_vocab_extension",
]
