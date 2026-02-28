from prometheus_client import Counter, Histogram, Gauge, Info

REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds",
    "Request latency in seconds",
    labelnames=["method", "endpoint", "status"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total request count",
    labelnames=["method", "endpoint", "status"],
)

PAPERS_LOADED = Gauge(
    "api_papers_loaded_total",
    "Number of papers currently loaded in the store",
)

SEARCH_QUERIES = Counter(
    "api_search_queries_total",
    "Total number of search queries executed",
)

SEARCH_LATENCY = Histogram(
    "api_search_duration_seconds",
    "Search query latency in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

INDEX_SIZE = Gauge(
    "api_index_dimensions",
    "Embedding dimensions in the search index",
)

APP_INFO = Info(
    "api",
    "Paper Analyzer API info",
)
