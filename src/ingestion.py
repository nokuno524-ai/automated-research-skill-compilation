"""Paper-to-Skill Pipeline: arXiv Paper Ingestion."""
import json
import logging
import re
import sqlite3
import time
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArxivFetcher:
    """Fetches papers from the arXiv API with rate limiting."""

    BASE_URL = "http://export.arxiv.org/api/query"
    RATE_LIMIT_SEC = 3.0

    def __init__(self):
        self.last_request_time = 0.0

    def fetch(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Fetch papers from arXiv.

        Args:
            query: Search query (e.g., "cat:cs.AI AND all:transformer").
            max_results: Maximum number of papers to fetch.

        Returns:
            List of dictionaries containing paper metadata (id, title, abstract, authors).
        """
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.RATE_LIMIT_SEC:
            time.sleep(self.RATE_LIMIT_SEC - elapsed)

        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        logger.info(f"Fetching from arXiv: {url}")

        try:
            with urllib.request.urlopen(url) as response:
                xml_data = response.read()

            self.last_request_time = time.time()
            return self._parse_arxiv_xml(xml_data)
        except Exception as e:
            logger.error(f"Failed to fetch from arXiv: {e}")
            return []

    def _parse_arxiv_xml(self, xml_data: bytes) -> List[Dict[str, str]]:
        """Parse Atom XML response from arXiv."""
        root = ET.fromstring(xml_data)
        # arXiv API uses Atom namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        papers = []
        for entry in root.findall("atom:entry", ns):
            paper_id = entry.find("atom:id", ns).text
            title = entry.find("atom:title", ns).text.replace("\n", " ").strip()
            abstract = entry.find("atom:summary", ns).text.replace("\n", " ").strip()

            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns).text
                authors.append(name)

            papers.append({
                "id": paper_id,
                "title": title,
                "abstract": abstract,
                "authors": authors
            })

        return papers


class PaperExtractor:
    """Extracts methods and key contributions from paper text using heuristics."""

    def extract_methods(self, text: str) -> List[str]:
        """
        Extract method descriptions using regex and heuristics.

        Args:
            text: Paper abstract or body text.

        Returns:
            List of extracted method sentences.
        """
        methods = []
        # Look for "we propose", "we introduce", "we present", etc.
        patterns = [
            r"we propose (.*?)\.",
            r"we introduce (.*?)\.",
            r"we present (.*?)\.",
            r"we develop (.*?)\.",
            r"we design (.*?)\.",
            r"propose a novel (.*?)\.",
        ]

        # Split text into sentences (rudimentary)
        sentences = [s.strip() + "." if not s.strip().endswith(".") else s.strip() for s in re.split(r'\.\s+', text) if s.strip()]
        sentences = [s.strip() + "." if not s.strip().endswith(".") else s.strip() for s in re.split(r'\.\s+', text) if s.strip()]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            for pattern in patterns:
                if re.search(pattern, sentence_lower):
                    methods.append(sentence)
                    break # Don't add same sentence multiple times

        return methods

    def extract_contributions(self, text: str) -> List[str]:
        """
        Extract key contributions using regex and heuristics.

        Args:
            text: Paper abstract or body text.

        Returns:
            List of extracted contribution sentences.
        """
        contributions = []
        # Look for "achieves", "outperforms", "state-of-the-art", "contribute"
        patterns = [
            r"we achieve (.*?)\.",
            r"outperforms (.*?)\.",
            r"state-of-the-art",
            r"we demonstrate (.*?)\.",
            r"we show that (.*?)\.",
            r"our main contribution",
        ]

        sentences = [s.strip() + "." for s in re.split(r'\.\s+', text) if s.strip()]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            for pattern in patterns:
                if re.search(pattern, sentence_lower):
                    contributions.append(sentence)
                    break

        return contributions


class QualityScorer:
    """Scores papers on novelty, reproducibility, and relevance."""

    def __init__(self):
        self.novelty_keywords = ["novel", "first", "new", "breakthrough", "unprecedented", "state-of-the-art", "propose"]
        self.reproducibility_keywords = ["code", "github", "open-source", "dataset", "released", "available", "hyperparameters", "reproduce"]
        self.relevance_keywords = ["agent", "llm", "large language model", "tool", "skill", "reasoning", "planning"]

    def score(self, paper: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate quality scores for a paper.

        Args:
            paper: Paper dictionary containing 'title' and 'abstract'.

        Returns:
            Dictionary with scores (0.0 to 1.0) for novelty, reproducibility, relevance, and overall.
        """
        text = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()

        def calculate_score(keywords: List[str], max_matches: int = 3) -> float:
            matches = sum(1 for kw in keywords if kw in text)
            return min(1.0, matches / max_matches)

        novelty_score = calculate_score(self.novelty_keywords, 2)
        reproducibility_score = calculate_score(self.reproducibility_keywords, 2)
        relevance_score = calculate_score(self.relevance_keywords, 3)

        # Overall score is a weighted average
        overall_score = (novelty_score * 0.4) + (reproducibility_score * 0.3) + (relevance_score * 0.3)

        return {
            "novelty": novelty_score,
            "reproducibility": reproducibility_score,
            "relevance": relevance_score,
            "overall": overall_score
        }


class StorageDB:
    """SQLite interface for storing parsed and scored paper records."""

    def __init__(self, db_path: str = "papers.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    abstract TEXT,
                    authors TEXT,
                    methods TEXT,
                    contributions TEXT,
                    novelty_score REAL,
                    reproducibility_score REAL,
                    relevance_score REAL,
                    overall_score REAL,
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_paper(self, paper: Dict[str, Any], scores: Dict[str, float], methods: List[str], contributions: List[str]):
        """Save a processed paper to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO papers
                (id, title, abstract, authors, methods, contributions,
                 novelty_score, reproducibility_score, relevance_score, overall_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper["id"],
                paper["title"],
                paper["abstract"],
                json.dumps(paper.get("authors", [])),
                json.dumps(methods),
                json.dumps(contributions),
                scores["novelty"],
                scores["reproducibility"],
                scores["relevance"],
                scores["overall"]
            ))
            conn.commit()

    def get_all_papers(self) -> List[Dict[str, Any]]:
        """Retrieve all papers from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers ORDER BY overall_score DESC")
            rows = cursor.fetchall()

            papers = []
            for row in rows:
                paper = dict(row)
                paper["authors"] = json.loads(paper["authors"]) if paper["authors"] else []
                paper["methods"] = json.loads(paper["methods"]) if paper["methods"] else []
                paper["contributions"] = json.loads(paper["contributions"]) if paper["contributions"] else []
                papers.append(paper)
            return papers


class IngestionPipeline:
    """Orchestrates fetching, extracting, scoring, and storing papers."""

    def __init__(self, db_path: str = "papers.db"):
        self.fetcher = ArxivFetcher()
        self.extractor = PaperExtractor()
        self.scorer = QualityScorer()
        self.db = StorageDB(db_path)

    def run(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Run the ingestion pipeline.

        Args:
            query: arXiv search query.
            max_results: Maximum papers to process.

        Returns:
            List of processed paper dictionaries.
        """
        logger.info(f"Starting ingestion pipeline for query: {query}")
        papers = self.fetcher.fetch(query, max_results)

        processed_papers = []
        for paper in papers:
            logger.info(f"Processing paper: {paper['title']}")

            methods = self.extractor.extract_methods(paper["abstract"])
            contributions = self.extractor.extract_contributions(paper["abstract"])
            scores = self.scorer.score(paper)

            self.db.save_paper(paper, scores, methods, contributions)

            processed_paper = {
                **paper,
                "methods": methods,
                "contributions": contributions,
                "scores": scores
            }
            processed_papers.append(processed_paper)

        logger.info(f"Pipeline completed. Processed {len(processed_papers)} papers.")
        return processed_papers

    def generate_report(self) -> str:
        """Generate a summary report of ingested papers."""
        papers = self.db.get_all_papers()

        if not papers:
            return "No papers in database."

        lines = []
        lines.append("=== Paper Ingestion Summary Report ===")
        lines.append(f"Total Papers: {len(papers)}")

        avg_score = sum(p["overall_score"] for p in papers) / len(papers)
        lines.append(f"Average Overall Score: {avg_score:.2f}")
        lines.append("")
        lines.append("Top 5 Papers by Score:")

        for i, p in enumerate(papers[:5]):
            lines.append(f"{i+1}. {p['title']} ({p['id']})")
            lines.append(f"   Score: {p['overall_score']:.2f}")
            if p["methods"]:
                lines.append(f"   Methods: {len(p['methods'])} extracted")

        return "\n".join(lines)
