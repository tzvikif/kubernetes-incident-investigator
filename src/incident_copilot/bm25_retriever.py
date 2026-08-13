import re

from rank_bm25 import BM25Okapi

from .schemas import DocumentChunk, RetrievalResult


def tokenize(text: str) -> list[str]:
    """Normalize text into tokens for lexical retrieval."""
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25Retriever:
    def __init__(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            raise ValueError("BM25Retriever requires at least one chunk")

        self._chunks = list(chunks)

        tokenized_corpus = [
            tokenize(
                " ".join(
                    [
                        chunk.topic.replace("_", " "),
                        chunk.section,
                        chunk.content,
                    ]
                )
            )
            for chunk in self._chunks
        ]

        self._index = BM25Okapi(tokenized_corpus)

    def retrieve(self, query: str, top_k: int = 3,) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("Query must not be empty")

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        query_tokens = tokenize(query)
        scores = self._index.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(self._chunks)),
            key=lambda index: scores[index],
            reverse=True,
        )[:top_k]

        return [
            RetrievalResult(
                chunk=self._chunks[index],
                score=float(scores[index]),
                rank=rank,
            )
            for rank, index in enumerate(ranked_indices, start=1)
        ]