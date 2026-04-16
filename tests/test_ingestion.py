"""Tests for the arXiv ingestion pipeline."""
import json
import os
import sqlite3
import tempfile
import urllib.request
from unittest import mock

import pytest

from src.ingestion import (
    ArxivFetcher,
    PaperExtractor,
    QualityScorer,
    StorageDB,
    IngestionPipeline
)


@pytest.fixture
def sample_arxiv_xml():
    return b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2301.00001v1</id>
        <title>A Novel Approach to AI Agents</title>
        <summary>
          We propose a novel architecture for autonomous AI agents.
          Our approach achieves state-of-the-art results on several benchmarks.
          The code is available on github.
        </summary>
        <author><name>Jane Doe</name></author>
        <author><name>John Smith</name></author>
      </entry>
    </feed>
    """


@pytest.fixture
def mock_urlopen(sample_arxiv_xml):
    mock_response = mock.MagicMock()
    mock_response.read.return_value = sample_arxiv_xml
    mock_response.__enter__.return_value = mock_response
    return mock_response


def test_arxiv_fetcher(mock_urlopen):
    with mock.patch('urllib.request.urlopen', return_value=mock_urlopen):
        fetcher = ArxivFetcher()
        # Should not sleep on first request
        with mock.patch('time.sleep') as mock_sleep:
            papers = fetcher.fetch("cat:cs.AI")
            assert len(papers) == 1
            assert papers[0]["id"] == "http://arxiv.org/abs/2301.00001v1"
            assert papers[0]["title"] == "A Novel Approach to AI Agents"
            assert "We propose a novel architecture" in papers[0]["abstract"]
            assert papers[0]["authors"] == ["Jane Doe", "John Smith"]
            mock_sleep.assert_not_called()

            # Should sleep on second request within rate limit
            fetcher.fetch("cat:cs.AI")
            mock_sleep.assert_called_once()


def test_paper_extractor():
    extractor = PaperExtractor()
    text = "We propose a novel architecture for autonomous AI agents. We introduce a new training method. Our approach achieves state-of-the-art results on several benchmarks. It outperforms existing baselines."

    methods = extractor.extract_methods(text)
    assert len(methods) == 2
    assert "We propose a novel architecture for autonomous AI agents." in methods
    assert "We introduce a new training method." in methods

    contributions = extractor.extract_contributions(text)
    assert len(contributions) == 2
    assert "Our approach achieves state-of-the-art results on several benchmarks." in contributions
    assert "It outperforms existing baselines.." in contributions


def test_quality_scorer():
    scorer = QualityScorer()

    # High score paper
    high_paper = {
        "title": "A novel agent for LLM reasoning",
        "abstract": "We propose a breakthrough method. Code is released on github."
    }
    high_scores = scorer.score(high_paper)
    assert high_scores["novelty"] == 1.0  # novel, breakthrough, propose
    assert high_scores["reproducibility"] == 1.0  # code, released, github
    assert high_scores["relevance"] > 0.0  # agent, llm, reasoning
    assert high_scores["overall"] > 0.8

    # Low score paper
    low_paper = {
        "title": "A standard approach",
        "abstract": "We use standard techniques. No datasets."
    }
    low_scores = scorer.score(low_paper)
    assert low_scores["novelty"] == 0.0
    assert low_scores["relevance"] == 0.0


def test_storage_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = StorageDB(db_path)

        paper = {
            "id": "1234",
            "title": "Test Paper",
            "abstract": "Test abstract",
            "authors": ["Author 1"]
        }
        scores = {
            "novelty": 0.5,
            "reproducibility": 0.5,
            "relevance": 0.5,
            "overall": 0.5
        }
        methods = ["Method 1"]
        contributions = ["Contribution 1"]

        db.save_paper(paper, scores, methods, contributions)

        papers = db.get_all_papers()
        assert len(papers) == 1
        assert papers[0]["id"] == "1234"
        assert papers[0]["title"] == "Test Paper"
        assert papers[0]["authors"] == ["Author 1"]
        assert papers[0]["methods"] == ["Method 1"]
        assert papers[0]["contributions"] == ["Contribution 1"]
        assert papers[0]["overall_score"] == 0.5

    finally:
        os.unlink(db_path)


def test_ingestion_pipeline(mock_urlopen):
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        with mock.patch('urllib.request.urlopen', return_value=mock_urlopen):
            pipeline = IngestionPipeline(db_path=db_path)

            # Disable sleep for fast testing
            with mock.patch('time.sleep'):
                papers = pipeline.run("test query", max_results=1)

            assert len(papers) == 1
            assert papers[0]["id"] == "http://arxiv.org/abs/2301.00001v1"
            assert "methods" in papers[0]
            assert "contributions" in papers[0]
            assert "scores" in papers[0]

            report = pipeline.generate_report()
            assert "Total Papers: 1" in report
            assert "A Novel Approach to AI Agents" in report
            assert "Average Overall Score" in report

    finally:
        os.unlink(db_path)
