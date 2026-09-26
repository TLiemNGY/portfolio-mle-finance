"""Shared, lazily-created clients used across the project.

Clients are created on first use, not at import time, so importing
modules that reference them (e.g. in tests) never requires live
credentials unless a client is actually used.
"""

import os

from dotenv import load_dotenv
from google.cloud import bigquery
from langchain_google_genai import ChatGoogleGenerativeAI

from core.config import PROJECT_ID

load_dotenv()

_bq_client: bigquery.Client | None = None
_llm: ChatGoogleGenerativeAI | None = None


def get_client() -> bigquery.Client:
    """Returns a shared BigQuery client, created on first use."""
    global _bq_client
    if _bq_client is None:
        _bq_client = bigquery.Client(project=PROJECT_ID)
    return _bq_client


def get_llm() -> ChatGoogleGenerativeAI:
    """Returns a shared Gemini client, created on first use."""
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            google_api_key=os.environ["GOOGLE_API_KEY"],
        )
    return _llm
