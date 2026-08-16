import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from extractor import parse_markdown_paper, parse_arxiv_html, extract_arxiv_id, ExtractorStage


def test_parse_markdown_paper_abstract_extraction():
    md = """# My Paper

## Abstract
This is the abstract content.

## Introduction
Intro content.
"""
    content = parse_markdown_paper(md)
    assert content.title == "My Paper"
    assert content.abstract == "This is the abstract content."
    assert len(content.sections) == 2


def test_parse_arxiv_html_error_handling():
    html = "just a string without any html tags"
    content = parse_arxiv_html(html)
    assert content.title == ""
    assert content.abstract == ""


def test_extract_arxiv_id():
    assert extract_arxiv_id("https://arxiv.org/abs/1234.56789") == "1234.56789"
    assert extract_arxiv_id("arxiv.org/pdf/1234.56789") == "1234.56789"
    assert extract_arxiv_id("not an id") == "not an id"

def test_parse_malformed_pdf_mock():
    # Since there's no native PDF parser yet, if a hypothetical parser extracts
    # garbage/empty text, ensure our pipeline handles it.
    garbage_md = "(x+y)=1"
    content = parse_markdown_paper(garbage_md)
    assert content.title == ""
    assert content.abstract == ""
    assert len(content.sections) == 0


def test_extractor_stage_interface():
    stage = ExtractorStage()
    md = "# Title\n\n## Abstract\nAbstract text."
    content = stage.run(md, is_html=False)
    assert content.title == "Title"
    assert content.abstract == "Abstract text."

def test_extractor_stage_invalid_input():
    stage = ExtractorStage()
    with pytest.raises(ValueError):
        stage.run(None)
    with pytest.raises(ValueError):
        stage.run(123)
    with pytest.raises(ValueError):
        stage.run("")
