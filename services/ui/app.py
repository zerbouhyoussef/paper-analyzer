import os
from typing import Optional
from urllib.parse import quote

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Paper Analyzer", page_icon="📄", layout="wide")


def fetch(endpoint: str) -> Optional[dict | list]:
    """Call the API and return parsed JSON, or None on failure."""
    try:
        resp = requests.get(f"{API_URL}{endpoint}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"API error: {e}")
        return None


def render_summary(summary: dict) -> None:
    """Render a paper's AI summary in the UI."""
    st.subheader("AI Summary")
    st.markdown(f"**Research Question:** {summary['research_question']}")
    st.markdown(f"**Methodology:** {summary['methodology']}")
    st.markdown("**Key Findings:**")
    for finding in summary.get("key_findings", []):
        st.markdown(f"- {finding}")
    st.markdown(f"**Contributions:** {summary['contributions']}")
    st.markdown(f"**Limitations:** {summary['limitations']}")


st.title("Paper Analyzer")
st.markdown("Browse and search AI-analyzed academic papers from arXiv.")

tab_browse, tab_search = st.tabs(["Browse Papers", "Semantic Search"])

with tab_browse:
    papers = fetch("/papers/")
    if papers:
        for paper in papers:
            with st.expander(f"**{paper['title']}**"):
                if paper.get("topics"):
                    st.caption(" | ".join(paper["topics"]))

                detail = fetch(f"/papers/{paper['paper_id']}")
                if detail:
                    if detail.get("authors"):
                        st.markdown(f"**Authors:** {', '.join(detail['authors'])}")
                    if detail.get("abstract"):
                        st.markdown(f"**Abstract:** {detail['abstract']}")
                    if detail.get("summary"):
                        render_summary(detail["summary"])
    elif papers is not None:
        st.info("No papers found. Run the pipeline to ingest and process papers.")

with tab_search:
    query = st.text_input("Search query", placeholder="e.g. deep learning for NLP")
    top_k = st.slider("Number of results", min_value=1, max_value=20, value=5)

    if st.button("Search", type="primary") and query:
        results = fetch(f"/papers/search?q={quote(query)}&top_k={top_k}")
        if results and results.get("results"):
            for r in results["results"]:
                score_pct = f"{r['score'] * 100:.1f}%"
                with st.expander(f"**{r['title']}** (relevance: {score_pct})"):
                    if r.get("topics"):
                        st.caption(" | ".join(r["topics"]))
                    if r.get("authors"):
                        st.markdown(f"**Authors:** {', '.join(r['authors'])}")
                    if r.get("summary"):
                        render_summary(r["summary"])
        elif results:
            st.info(results.get("message", "No results found."))
