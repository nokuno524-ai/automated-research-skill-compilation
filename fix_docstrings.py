import sys

# pipeline
content = open("src/pipeline.py").read()
content = content.replace('    """Run the full Paper-to-Skill pipeline."""\n    """\n    Run the full Paper-to-Skill pipeline.', '    """\n    Run the full Paper-to-Skill pipeline.')
with open("src/pipeline.py", "w") as f:
    f.write(content)

# validator
content = open("src/validator.py").read()
content = content.replace('    """Validate a generated skill directory."""\n    """Validate a generated skill directory."""', '    """Validate a generated skill directory."""')
content = content.replace('    """Format validation result as readable report."""\n    """Format validation result as readable report."""', '    """Format validation result as readable report."""')
with open("src/validator.py", "w") as f:
    f.write(content)

# extractor
content = open("src/extractor.py").read()
content = content.replace('    """Serialize PaperContent to dict."""\n    """Serialize PaperContent to dict."""', '    """Serialize PaperContent to dict."""')
content = content.replace('    """Save PaperContent to JSON."""\n    """Save PaperContent to JSON."""', '    """Save PaperContent to JSON."""')
with open("src/extractor.py", "w") as f:
    f.write(content)

# synthesizer
content = open("src/synthesizer.py").read()
content = content.replace('    """Serialize MethodSpec to dict."""\n    """Serialize MethodSpec to dict."""', '    """Serialize MethodSpec to dict."""')
content = content.replace('    """Save MethodSpec to JSON."""\n    """Save MethodSpec to JSON."""', '    """Save MethodSpec to JSON."""')
with open("src/synthesizer.py", "w") as f:
    f.write(content)
