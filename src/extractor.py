"""Paper-to-Skill Pipeline: Content extraction from research papers."""
import json
import re
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Section:
    """Represents a section in a research paper."""
    title: str
    level: int
    content: str
    subsections: list = field(default_factory=list)


@dataclass
class Equation:
    """Represents an extracted LaTeX equation from a paper."""
    latex: str
    context: str  # surrounding text
    label: Optional[str] = None


@dataclass
class Algorithm:
    """Represents a pseudocode algorithm parsed from a paper."""
    name: str
    description: str
    pseudocode: str
    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)


@dataclass
class PaperContent:
    """Structured representation of a research paper's content."""
    title: str = ""
    authors: list = field(default_factory=list)
    abstract: str = ""
    sections: list = field(default_factory=list)  # List[Section]
    equations: list = field(default_factory=list)  # List[Equation]
    algorithms: list = field(default_factory=list)  # List[Algorithm]
    tables: list = field(default_factory=list)  # List[dict]
    references: list = field(default_factory=list)
    url: str = ""
    arxiv_id: str = ""


def extract_arxiv_id(url_or_id: str) -> str:
    """Extract arXiv ID from URL or return as-is."""
    patterns = [
        r'arxiv\.org/abs/(\d+\.\d+)',
        r'arxiv\.org/pdf/(\d+\.\d+)',
        r'arxiv\.org/html/(\d+\.\d+)',
        r'^(\d{4}\.\d{4,5})$',
    ]
    for p in patterns:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    return url_or_id


def parse_arxiv_html(html: str, url: str = "") -> PaperContent:
    """Parse arXiv HTML into structured PaperContent."""
    content = PaperContent(url=url)
    
    # Extract title
    title_match = re.search(r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if not title_match:
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if title_match:
        content.title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    
    # Extract abstract
    abs_match = re.search(r'<blockquote[^>]*class="[^"]*abstract[^"]*"[^>]*>(.*?)</blockquote>', html, re.DOTALL)
    if abs_match:
        content.abstract = re.sub(r'<[^>]+>', '', abs_match.group(1)).strip()
    
    # Extract authors
    author_matches = re.findall(r'<a[^>]*class="[^"]*author[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
    content.authors = [re.sub(r'<[^>]+>', '', a).strip() for a in author_matches]
    
    # Extract sections from HTML
    section_pattern = re.compile(r'<h[23][^>]*>(.*?)</h[23]>(.*?)(?=<h[23]|$)', re.DOTALL)
    for match in section_pattern.finditer(html):
        title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        body = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if title:
            content.sections.append(Section(title=title, level=2, content=body[:5000]))
    
    # Extract equations (LaTeX)
    eq_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    for m in eq_pattern.finditer(html):
        content.equations.append(Equation(latex=m.group(1).strip(), context=""))
    
    # Also try \(...\) style
    eq_pattern2 = re.compile(r'\\\((.*?)\\\)', re.DOTALL)
    for m in eq_pattern2.finditer(html):
        content.equations.append(Equation(latex=m.group(1).strip(), context=""))
    
    # Extract arxiv ID from URL
    if url:
        content.arxiv_id = extract_arxiv_id(url)
    
    return content


def parse_markdown_paper(md_text: str, url: str = "") -> PaperContent:
    """Parse a markdown-formatted paper into PaperContent."""
    content = PaperContent(url=url)
    
    lines = md_text.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        header_match = re.match(r'^(#{1,4})\s+(.*)', line)
        if header_match:
            # Save previous section
            if current_section:
                current_section.content = '\n'.join(current_content).strip()
                content.sections.append(current_section)
            
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            
            if level == 1 and not content.title:
                content.title = title
                current_section = None
                current_content = []
            else:
                current_section = Section(title=title, level=level, content='')
                current_content = []
            
            if title.lower() == 'abstract' and current_section:
                # Next lines until next header are abstract
                pass
        else:
            current_content.append(line)
    
    # Save last section
    if current_section:
        current_section.content = '\n'.join(current_content).strip()
        content.sections.append(current_section)
    
    # Set abstract explicitly by looking for the abstract section
    for sec in content.sections:
        if sec.title.lower() == 'abstract':
            content.abstract = sec.content
            break

    # Extract equations from markdown
    eq_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    for m in eq_pattern.finditer(md_text):
        content.equations.append(Equation(latex=m.group(1).strip(), context=""))
    
    if url:
        content.arxiv_id = extract_arxiv_id(url)
    
    return content


def content_to_dict(content: PaperContent) -> dict:
    """Serialize PaperContent to dict."""
    return asdict(content)


def save_content(content: PaperContent, path: str):
    """Save PaperContent to JSON."""
    with open(path, 'w') as f:
        json.dump(content_to_dict(content), f, indent=2)
    logger.info(f"Saved paper content to {path}")


if __name__ == "__main__":
    # Quick test with sample markdown
    sample = """# Attention Is All You Need

## Abstract
We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.

## 1 Introduction
Recurrent neural networks have been the dominant approach.

## 3 Model Architecture
The Transformer follows an encoder-decoder structure.

$$\\text{Attention}(Q, K, V) = \\text{softmax}(\\frac{QK^T}{\\sqrt{d_k}})V$$

The multi-head attention mechanism projects queries, keys, and values h times.
"""
    content = parse_markdown_paper(sample, url="arxiv.org/abs/1706.03762")
    print(json.dumps(content_to_dict(content), indent=2)[:2000])
