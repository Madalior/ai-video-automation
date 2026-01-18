# Common Modules Package
# Simplified __init__.py - only import what exists as classes

# Core classes that exist
from .llm_manager import LLMManager
from .trend_finder import TrendFinder

# Use try-except for optional modules
try:
    from .enhanced_editor import EnhancedVideoEditor
except ImportError:
    pass

try:
    from .ai_metadata_generator import AIMetadataGenerator
except ImportError:
    pass

try:
    from .smart_uploader import SmartUploader
except ImportError:
    pass

__all__ = ['LLMManager', 'TrendFinder']
