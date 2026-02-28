import json
import logging
import os
import re
from typing import Optional

import requests
import xmltodict

from services.ingestor.arxiv_client import ArxivClient
from services.ingestor.config import Config

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(self, config: type[Config], arxiv_client: ArxivClient):
        self.config = config
        self.arxiv_client = arxiv_client
        self._blob_client = None

    def _get_blob_client(self):
        if self._blob_client is None and self.config.UPLOAD_TO_BLOB:
            from shared.blob_client import BlobClient
            self._blob_client = BlobClient(
                connection_string=self.config.AZURE_CONNECTION_STRING,
                container_name=self.config.AZURE_CONTAINER_NAME,
            )
        return self._blob_client

    def download_papers(self, category: str, max_results: int) -> None:
        """Download papers from arXiv, save locally, and optionally upload to Azure Blob."""
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)

        xml_data = self.arxiv_client.search_papers(category, max_results)
        if not xml_data:
            return

        metadata_list = self._parse_metadata(xml_data)
        for metadata in metadata_list:
            safe_title = self._safe_filename(metadata["title"])
            self._download_pdf(metadata["pdf_url"], safe_title)
            self._save_metadata(metadata, safe_title)

    def _download_pdf(self, pdf_url: str, safe_title: str) -> None:
        """Download a single PDF, skipping if it exceeds the size limit."""
        try:
            response = requests.get(
                pdf_url, stream=True, timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            content_length = int(response.headers.get("Content-Length", 0))
            if content_length > self.config.MAX_FILE_SIZE_MB * 1024 * 1024:
                logger.warning(f"Skipping {safe_title}: exceeds {self.config.MAX_FILE_SIZE_MB}MB")
                return

            file_path = os.path.join(self.config.OUTPUT_DIR, f"{safe_title}.pdf")
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded {file_path}")

            blob = self._get_blob_client()
            if blob:
                blob.upload_file(file_path, f"ingested/{safe_title}.pdf")

        except requests.RequestException as e:
            logger.error(f"Error downloading PDF: {e}")

    def _save_metadata(self, metadata: dict, safe_title: str) -> None:
        """Save paper metadata locally and optionally to Azure Blob."""
        meta_path = os.path.join(self.config.OUTPUT_DIR, f"{safe_title}.meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.info(f"Saved metadata: {meta_path}")

        blob = self._get_blob_client()
        if blob:
            blob.upload_json(metadata, f"ingested/{safe_title}.meta.json")

    def _parse_metadata(self, xml_data: str) -> list[dict]:
        """Parse arXiv XML response into structured metadata dicts."""
        try:
            data_dict = xmltodict.parse(xml_data)
            entries = data_dict["feed"].get("entry", [])
            if isinstance(entries, dict):
                entries = [entries]

            results = []
            for entry in entries:
                authors = self._extract_list(entry, "author", "name")
                categories = self._extract_list(entry, "category", "@term")
                pdf_url = self._extract_pdf_url(entry.get("link", []))

                arxiv_id = entry.get("id", "")
                paper_id = arxiv_id.split("/")[-1] if arxiv_id else ""

                results.append({
                    "paper_id": paper_id,
                    "title": entry.get("title", "").replace("\n", " ").strip(),
                    "authors": authors,
                    "abstract": entry.get("summary", "").replace("\n", " ").strip(),
                    "categories": categories,
                    "pdf_url": pdf_url,
                    "published": entry.get("published", ""),
                    "source": "arxiv",
                })
            return results
        except Exception as e:
            logger.error(f"Error parsing metadata: {e}")
            return []

    @staticmethod
    def _extract_list(entry: dict, key: str, subkey: str) -> list[str]:
        raw = entry.get(key, [])
        if isinstance(raw, dict):
            raw = [raw]
        return [item.get(subkey, "") for item in raw if isinstance(item, dict)]

    @staticmethod
    def _extract_pdf_url(links: list) -> str:
        for link in links:
            if isinstance(link, dict) and link.get("@title") == "pdf":
                return link.get("@href", "")
        if len(links) > 1 and isinstance(links[1], dict):
            return links[1].get("@href", "")
        return ""

    @staticmethod
    def _safe_filename(title: str) -> str:
        safe = re.sub(r"[^\w\s-]", "", title)
        safe = re.sub(r"\s+", "_", safe).strip("_")
        return safe[:200]
