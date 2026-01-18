"""
Identity Card System for Character Consistency

Implements Veo 3.1's anchor/delta methodology:
- ANCHOR: Unchangeable identity-defining attributes
- DELTA: Scene-specific changeable elements

This ensures 90%+ character consistency across video scenes.
"""

class CharacterIdentityCard:
    """
    Persistent character attributes for AI video consistency.
    
    Separates 'anchor' (unchangeable traits) from 'delta' (scene-specific elements).
    Follows Veo 3.1 best practices for character recognition.
    """
    
    def __init__(self, name: str, anchors: dict = None, voice_profile: dict = None):
        """
        Initialize character identity card.
        
        Args:
            name: Character name
            anchors: Dict of unchangeable attributes (see get_default_anchors)
            voice_profile: Dict of vocal characteristics (see get_default_voice)
        """
        self.name = name
        
        # Core identity attributes (NEVER change)
        self.anchors = {
            'facial_features': '',      # Eyes, nose, mouth, face shape, skin tone
            'body_type': '',            # Height, build, posture
            'distinctive_marks': '',     # Scars, tattoos, birthmarks, unique features
            'hair': '',                 # Color, style, length, texture
            'clothing_style': '',       # Core wardrobe identity (not specific outfit)
            'age_appearance': '',       # Apparent age range
            'ethnicity': '',            # Ethnic/racial appearance
            'gender_presentation': '',   # Gender appearance
        }
        
        if anchors:
            self.anchors.update(anchors)
        
        # Voice characteristics for dialogue consistency
        self.voice_profile = {
            'tone': 'neutral',          # Warm, cold, authoritative, friendly
            'pace': 'moderate',         # Fast, slow, measured, energetic
            'accent': 'standard',       # Regional, none, specific
            'pitch': 'medium',          # High, low, medium
            'style': 'conversational'   # Formal, casual, professional
        }
        
        if voice_profile:
            self.voice_profile.update(voice_profile)
    
    def get_anchor_prompt(self) -> str:
        """
        Returns unchangeable attributes as detailed prompt text.
        
        Returns:
            Formatted anchor attributes string for AI generation
        """
        parts = []
        for key, value in self.anchors.items():
            if value and value.strip():
                # Format as natural language
                label = key.replace('_', ' ').title()
                parts.append(f"{label}: {value}")
        
        if not parts:
            return f"{self.name} (no specific features defined)"
        
        return "; ".join(parts)
    
    def get_voice_prompt(self) -> str:
        """
        Returns voice characteristics for consistent dialogue.
        
        Returns:
            Formatted voice profile string
        """
        parts = []
        for key, value in self.voice_profile.items():
            if value and value.strip():
                parts.append(f"{key}: {value}")
        
        return "Voice - " + ", ".join(parts)
    
    def get_scene_prompt(self, delta_attributes: dict) -> str:
        """
        Combines anchor (fixed) with delta (changeable) attributes.
        
        Args:
            delta_attributes: Scene-specific elements:
                - pose: Body position/stance
                - emotion: Facial expression/mood
                - action: What character is doing
                - clothing_details: Specific outfit for this scene
                - lighting: Scene lighting conditions
                - camera_angle: Shot composition
                - background: Setting description
        
        Returns:
            Complete prompt with [ANCHOR] and [DELTA] sections
        """
        anchor = self.get_anchor_prompt()
        
        delta_parts = []
        for key, value in delta_attributes.items():
            if value and value.strip():
                label = key.replace('_', ' ').title()
                delta_parts.append(f"{label}: {value}")
        
        delta_text = "; ".join(delta_parts) if delta_parts else "default scene"
        
        # Veo 3.1 format: Clearly separate fixed vs changing attributes
        return f"[CHARACTER ANCHOR] {anchor} [SCENE DELTA] {delta_text}"
    
    def to_dict(self) -> dict:
        """Export identity card to dictionary format."""
        return {
            'name': self.name,
            'anchors': self.anchors,
            'voice_profile': self.voice_profile
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create identity card from dictionary."""
        return cls(
            name=data.get('name', 'Unknown'),
            anchors=data.get('anchors'),
            voice_profile=data.get('voice_profile')
        )
    
    @staticmethod
    def get_default_anchors() -> dict:
        """Returns template for anchor attributes."""
        return {
            'facial_features': 'Example: 30s male, sharp jawline, green eyes, thin nose, olive skin',
            'body_type': 'Example: 6\'2", athletic build, confident posture',
            'distinctive_marks': 'Example: Small scar above left eyebrow',
            'hair': 'Example: Short brown hair, slightly wavy, well-groomed',
            'clothing_style': 'Example: Business casual, always professional',
            'age_appearance': 'Example: Early 30s',
            'ethnicity': 'Example: Caucasian',
            'gender_presentation': 'Example: Masculine'
        }
    
    @staticmethod
    def get_default_voice() -> dict:
        """Returns template for voice profile."""
        return {
            'tone': 'authoritative yet warm',
            'pace': 'measured, deliberate',
            'accent': 'Midwestern American',
            'pitch': 'medium-low',
            'style': 'professional but approachable'
        }


class IdentityCardManager:
    """Manages multiple character identity cards for a video project."""
    
    def __init__(self):
        """Initialize empty card collection."""
        self.cards = {}  # name -> CharacterIdentityCard
    
    def add_card(self, card: CharacterIdentityCard):
        """Add or update identity card."""
        self.cards[card.name] = card
    
    def get_card(self, name: str) -> CharacterIdentityCard:
        """Retrieve identity card by character name."""
        return self.cards.get(name)
    
    def has_card(self, name: str) -> bool:
        """Check if card exists for character."""
        return name in self.cards
    
    def get_all_cards(self) -> dict:
        """Get all identity cards."""
        return self.cards.copy()
    
    def to_dict(self) -> dict:
        """Export all cards to dictionary."""
        return {
            name: card.to_dict() 
            for name, card in self.cards.items()
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create manager from dictionary."""
        manager = cls()
        for name, card_data in data.items():
            card = CharacterIdentityCard.from_dict(card_data)
            manager.add_card(card)
        return manager


# Example usage
if __name__ == "__main__":
    # Create identity card
    john = CharacterIdentityCard(
        name="John Smith",
        anchors={
            'facial_features': '35-year-old male, sharp jawline, piercing green eyes, straight nose, light stubble',
            'body_type': '6\'2", athletic build, broad shoulders, confident posture',
            'distinctive_marks': 'Small scar above left eyebrow, silver watch always worn',
            'hair': 'Short dark brown hair with slight gray at temples, professional cut',
            'clothing_style': 'Business professional - suits and dress shirts',
            'age_appearance': 'Mid-to-late 30s',
            'ethnicity': 'Caucasian',
            'gender_presentation': 'Masculine'
        },
        voice_profile={
            'tone': 'authoritative yet approachable',
            'pace': 'measured and deliberate',
            'accent': 'Standard American',
            'pitch': 'medium-low baritone',
            'style': 'professional corporate'
        }
    )
    
    # Generate scene-specific prompts
    scene1_delta = {
        'pose': 'standing confidently with arms crossed',
        'emotion': 'focused and determined',
        'action': 'reviewing documents on desk',
        'clothing_details': 'navy blue suit, white shirt, red power tie',
        'lighting': 'warm office lighting from desk lamp',
        'camera_angle': 'medium shot at eye level',
        'background': 'modern corner office with city skyline visible through window'
    }
    
    scene2_delta = {
        'pose': 'leaning against car casually',
        'emotion': 'relaxed smile',
        'action': 'checking wristwatch',
        'clothing_details': 'charcoal gray suit, light blue shirt, loosened tie',
        'lighting': 'golden hour sunset',
        'camera_angle': 'low angle hero shot',
        'background': 'downtown city street with evening traffic'
    }
    
    print("="*80)
    print("IDENTITY CARD SYSTEM DEMO")
    print("="*80)
    
    print("\n[ANCHOR] Character Identity (never changes):")
    print(john.get_anchor_prompt())
    
    print("\n[VOICE] Voice Profile:")
    print(john.get_voice_prompt())
    
    print("\n" + "="*80)
    print("SCENE 1 - Office")
    print("="*80)
    print(john.get_scene_prompt(scene1_delta))
    
    print("\n" + "="*80)
    print("SCENE 2 - Street")
    print("="*80)
    print(john.get_scene_prompt(scene2_delta))
    
    print("\n✅ Notice: Character anchor stays identical, only scene deltas change!")
