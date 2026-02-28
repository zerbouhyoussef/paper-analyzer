import logging
import os
from typing import Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient as AzureSearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchFieldDataType as DT,
)
from azure.search.documents.models import VectorizedQuery

logger = logging.getLogger(__name__)

INDEX_NAME = "papers"
VECTOR_DIMENSIONS = 384


class SearchClient:
    """Azure AI Search client for indexing and querying papers."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        index_name: str = INDEX_NAME,
    ):
        self._endpoint = endpoint or os.getenv("AZURE_SEARCH_ENDPOINT", "")
        self._api_key = api_key or os.getenv("AZURE_SEARCH_API_KEY", "")
        self._index_name = index_name

        if not self._endpoint or not self._api_key:
            raise ValueError("AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY are required")

        self._credential = AzureKeyCredential(self._api_key)
        self._ensure_index()

    def _ensure_index(self) -> None:
        """Create the search index if it doesn't exist."""
        index_client = SearchIndexClient(self._endpoint, self._credential)
        try:
            index_client.get_index(self._index_name)
            logger.info(f"Search index '{self._index_name}' exists")
        except Exception:
            index = self._build_index_schema()
            index_client.create_index(index)
            logger.info(f"Created search index '{self._index_name}'")

    def _build_index_schema(self) -> SearchIndex:
        fields = [
            SimpleField(name="paper_id", type=SearchFieldDataType.String, key=True, filterable=True),
            SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="abstract", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="clean_text", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SimpleField(name="authors", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
            SimpleField(name="topics", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True, facetable=True),
            SearchableField(name="research_question", type=SearchFieldDataType.String),
            SearchableField(name="methodology", type=SearchFieldDataType.String),
            SearchableField(name="contributions", type=SearchFieldDataType.String),
            SearchableField(name="limitations", type=SearchFieldDataType.String),
            SimpleField(name="key_findings", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
            SimpleField(name="enriched_at", type=SearchFieldDataType.DateTimeOffset, sortable=True),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=VECTOR_DIMENSIONS,
                vector_search_profile_name="default-profile",
            ),
        ]

        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="default-algorithm")],
            profiles=[VectorSearchProfile(name="default-profile", algorithm_configuration_name="default-algorithm")],
        )

        return SearchIndex(name=self._index_name, fields=fields, vector_search=vector_search)

    def _get_search_client(self) -> AzureSearchClient:
        return AzureSearchClient(self._endpoint, self._index_name, self._credential)

    def index_paper(self, document: dict) -> None:
        """Index or update a single paper document."""
        client = self._get_search_client()
        client.upload_documents(documents=[document])
        logger.info(f"Indexed paper: {document.get('paper_id')}")

    def index_papers(self, documents: list[dict]) -> int:
        """Batch-index multiple paper documents. Returns count indexed."""
        if not documents:
            return 0
        client = self._get_search_client()
        result = client.upload_documents(documents=documents)
        succeeded = sum(1 for r in result if r.succeeded)
        logger.info(f"Indexed {succeeded}/{len(documents)} papers")
        return succeeded

    def search_text(self, query: str, top_k: int = 5) -> list[dict]:
        """Full-text search across paper fields."""
        client = self._get_search_client()
        results = client.search(
            search_text=query,
            select=["paper_id", "title", "authors", "abstract", "topics",
                    "research_question", "methodology", "key_findings",
                    "contributions", "limitations"],
            top=top_k,
        )
        return [{"score": r["@search.score"], **{k: v for k, v in r.items() if k != "@search.score"}} for r in results]

    def search_vector(self, embedding: list[float], top_k: int = 5) -> list[dict]:
        """Vector similarity search using a pre-computed embedding."""
        client = self._get_search_client()
        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=top_k,
            fields="embedding",
        )
        results = client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["paper_id", "title", "authors", "abstract", "topics",
                    "research_question", "methodology", "key_findings",
                    "contributions", "limitations"],
            top=top_k,
        )
        return [{"score": r["@search.score"], **{k: v for k, v in r.items() if k != "@search.score"}} for r in results]

    def search_hybrid(self, query: str, embedding: list[float], top_k: int = 5) -> list[dict]:
        """Hybrid search combining full-text and vector similarity."""
        client = self._get_search_client()
        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=top_k,
            fields="embedding",
        )
        results = client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["paper_id", "title", "authors", "abstract", "topics",
                    "research_question", "methodology", "key_findings",
                    "contributions", "limitations"],
            top=top_k,
        )
        return [{"score": r["@search.score"], **{k: v for k, v in r.items() if k != "@search.score"}} for r in results]

    def get_document(self, paper_id: str) -> Optional[dict]:
        """Retrieve a single document by paper_id."""
        client = self._get_search_client()
        try:
            return client.get_document(key=paper_id)
        except Exception:
            return None

    def delete_document(self, paper_id: str) -> None:
        """Delete a document from the index."""
        client = self._get_search_client()
        client.delete_documents(documents=[{"paper_id": paper_id}])
        logger.info(f"Deleted paper from index: {paper_id}")

    def get_document_count(self) -> int:
        """Return the number of documents in the index."""
        client = self._get_search_client()
        return client.get_document_count()
