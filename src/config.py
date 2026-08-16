"""Pipeline Configuration."""
from dataclasses import dataclass, field
import os
import json


@dataclass
class PipelineConfig:
    """Configuration for the P2S pipeline."""
    output_dir: str = "output"
    use_llm: bool = False
    timeout_seconds: int = 10
    retry_attempts: int = 3
    retry_backoff: float = 2.0
    checkpoint_file: str = "pipeline_checkpoint.json"

    def to_dict(self):
        """Convert config to dictionary."""
        return {
            "output_dir": self.output_dir,
            "use_llm": self.use_llm,
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "retry_backoff": self.retry_backoff,
            "checkpoint_file": self.checkpoint_file
        }

    def save(self, path: str):
        """Save configuration to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "PipelineConfig":
        """Load configuration from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)
