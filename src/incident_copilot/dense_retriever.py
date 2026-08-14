from sentence_transformers import SentenceTransformer

from .schemas import DocumentChunk, RetrievalResult

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class DenseRetriever:
    def __init__(
        self,
        chunks: list[DocumentChunk],
        model_name: str = DEFAULT_MODEL_NAME,
        device: str | None = "cuda",
    ) -> None:
        if not chunks:
            raise ValueError("DenseRetriever requires at least one chunk")
        self._chunks = list(chunks)
        self._model = SentenceTransformer(
            model_name,
            device=device,
        )

        documents = [
            " ".join(
                [
                    chunk.topic.replace("_", " "),
                    chunk.section,
                    chunk.content,
                ]
            )
            for chunk in self._chunks
        ]

        self._document_embeddings = self._model.encode_document(
            documents,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("Query must not be empty")

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        query_embedding = self._model.encode_query(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        scores = self._document_embeddings @ query_embedding

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