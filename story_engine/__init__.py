"""
Automated Story Engine: Concept-to-Multi-Modal Narrative Workflow

A comprehensive system for generating multi-modal storybooks from high-level concepts
using advanced LLM orchestration and prompt optimization.
"""

__version__ = "1.0.0"
__author__ = "Story Engine Team"

# Always available core components
from .core.orchestrator import StoryOrchestrator
from .core.prompt_builder import PromptBuilder

# Optional components that may have heavy dependencies
try:
    from .generators.image_generator import ImageGenerator
except ImportError:
    ImageGenerator = None

try:
    from .generators.audio_generator import AudioGenerator
except ImportError:
    AudioGenerator = None

try:
    from .assemblers.story_compiler import StoryCompiler
except ImportError:
    StoryCompiler = None

# Only export what's available
__all__ = ["StoryOrchestrator", "PromptBuilder"]

if ImageGenerator:
    __all__.append("ImageGenerator")
if AudioGenerator:
    __all__.append("AudioGenerator") 
if StoryCompiler:
    __all__.append("StoryCompiler")
