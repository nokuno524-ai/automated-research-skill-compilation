import pytest
from src.extractor import PaperContent, Section

@pytest.fixture
def mock_paper_content():
    return PaperContent(
        title="Mock Title",
        abstract="Mock abstract.",
        sections=[Section(title="Method", level=2, content="We propose mock method.")],
        arxiv_id="1234.5678"
    )

@pytest.fixture
def mock_method_spec():
    return {
        "name": "MockMethod",
        "category": "architecture",
        "summary": "Mock summary",
        "description": "Mock description",
        "paper_title": "Mock Title",
        "key_equations": ["a = b + c"]
    }
