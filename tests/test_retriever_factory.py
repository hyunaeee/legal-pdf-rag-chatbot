import pytest

from app.retrieval import InMemoryRetriever
from app.retriever_factory import create_retriever
from app.settings import Settings


def test_memory_retriever_is_default() -> None:
    retriever = create_retriever(Settings())
    assert isinstance(retriever, InMemoryRetriever)


def test_unknown_retrieval_backend_fails_fast() -> None:
    settings = Settings(retrieval_backend="unknown")

    with pytest.raises(ValueError, match="Unsupported retrieval backend"):
        create_retriever(settings)
