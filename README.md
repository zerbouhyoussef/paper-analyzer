# Academic & Research Paper Analyzer

AI-powered pipeline for collecting, processing, and analyzing academic research papers.

## Features
- Automated paper collection from arXiv
- PDF text extraction with OCR fallback
- Data quality validation
- AI-powered summarization and topic extraction
- Hybrid search (full-text + vector) via Azure AI Search
- PDF and metadata storage in Azure Blob Storage
- Interactive web interface

## Tech Stack
- **Storage**: Azure Blob Storage (PDFs and metadata)
- **Search**: Azure AI Search (hybrid full-text + vector)
- **AI**: OpenAI API (summarization, topic extraction)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Backend**: Python, FastAPI
- **Frontend**: Streamlit
- **Orchestration**: Docker Compose
- **IaC**: Terraform (Azure)
- **Monitoring**: Prometheus + Grafana

## Architecture

```
arXiv --> Ingestor --> Extractor --> Validator --> Enricher --> API --> UI
              |                                       |          |
              v                                       v          v
        Azure Blob Storage                    Azure AI Search  Prometheus/Grafana
        (PDFs + metadata)                  (index + hybrid search)
```

## Services

| Service     | Description                              | Azure Integration       |
|-------------|------------------------------------------|--------------------------|
| Ingestor    | Downloads papers from arXiv              | Uploads to Blob Storage  |
| Extractor   | Extracts text from PDFs (pymupdf + OCR)  | -                        |
| Validator   | Validates text quality                   | -                        |
| Enricher    | AI summarization + embeddings            | Indexes to AI Search     |
| API         | FastAPI backend with search              | Queries AI Search        |
| UI          | Streamlit frontend                       | -                        |

## Setup

1. Copy `.env.example` to `.env` and fill in values
2. Install dependencies: `pip install -r requirements.txt`
3. Run locally: `make run-pipeline`
4. Run with Docker: `make docker-up`

### Azure Resources (optional)

Set `AZURE_CONNECTION_STRING` for Blob Storage and `AZURE_SEARCH_ENDPOINT` + `AZURE_SEARCH_API_KEY` for AI Search.
Without these, the pipeline works locally with file-based storage and in-memory vector search.

### Terraform Deployment

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars  # fill in values
make tf-init
make tf-plan
make tf-apply
```

## License
MIT
