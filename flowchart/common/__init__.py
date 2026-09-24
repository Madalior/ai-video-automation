# Common Modules Package
# ═══════════════════════════════════════════════════════════
# CORE EXPORTS — only files that actually live in flowchart/common/
# NOTE: trend_finder → 02_niche_discovery/trend_finder.py
#       enhanced_editor → 04_generation/enhanced_editor.py
#       smart_uploader  → 06_uploading/smart_uploader.py
# ═══════════════════════════════════════════════════════════

# Core classes that live in common/
from .llm_manager import LLMManager

# Optional modules — use try/except so one missing file doesn't break everything
try:
    from .ai_metadata_generator import AIMetadataGenerator
except ImportError:
    pass

try:
    from .emotional_script_generator import EmotionalScriptGenerator
except ImportError:
    pass

try:
    from .identity_cards import CharacterIdentityCard, IdentityCardManager
except ImportError:
    pass

__all__ = ['LLMManager', 'AIMetadataGenerator', 'EmotionalScriptGenerator',
           'CharacterIdentityCard', 'IdentityCardManager']
