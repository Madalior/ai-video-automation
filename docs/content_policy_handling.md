# Content Policy Handling Guide

## Understanding Gemini/Dreamina Safeguards

Google's AI systems have content policies to ensure safe and appropriate content generation. Here's how to work **within** these guidelines effectively.

## Legitimate Techniques

### 1. Prompt Engineering Best Practices

**Instead of vague/problematic prompts, use specific, descriptive language**:

❌ **Avoid**:
- Vague descriptions
- Potentially sensitive topics without context
- Celebrity names or copyrighted characters
- Violent or adult content

✅ **Use**:
- Detailed, professional descriptions
- Generic character archetypes
- Clear artistic direction
- Family-friendly alternatives

**Example Transformations**:
```
❌ "A scary monster attacking"
✅ "A fantasy creature in a misty forest, cinematic style"

❌ "Famous actor as superhero"
✅ "A heroic character in blue costume, dynamic pose"

❌ "Dark horror scene"
✅ "A mysterious shadowy atmosphere, gothic style"
```

---

### 2. Automatic Prompt Refinement

**Implement fallback prompts when policy blocks occur**:

```python
class SafePromptGenerator:
    """Automatically refine prompts to pass content policies."""
    
    def __init__(self):
        self.refinement_rules = {
            # Remove potentially triggering words
            'violent': ['action-oriented', 'dynamic'],
            'scary': ['mysterious', 'atmospheric'],
            'dark': ['shadowy', 'moody lighting'],
            'weapon': ['object', 'prop'],
        }
    
    def refine_prompt(self, original_prompt):
        """
        Refine prompt to be more policy-compliant.
        
        Args:
            original_prompt: Original prompt text
            
        Returns:
            Refined prompt with safer wording
        """
        refined = original_prompt
        
        # Apply refinement rules
        for trigger, alternatives in self.refinement_rules.items():
            if trigger.lower() in refined.lower():
                # Replace with safer alternative
                import random
                replacement = random.choice(alternatives)
                refined = refined.replace(trigger, replacement)
        
        # Add positive framing
        if "not" in refined or "without" in refined:
            # Focus on what TO include, not what to exclude
            refined = self._reframe_positive(refined)
        
        return refined
    
    def _reframe_positive(self, prompt):
        """Reframe negative descriptions positively."""
        # Example: "not scary" -> "friendly and welcoming"
        positive_mappings = {
            "not scary": "friendly",
            "not violent": "peaceful",
            "without weapons": "unarmed character",
        }
        
        for negative, positive in positive_mappings.items():
            if negative in prompt.lower():
                prompt = prompt.lower().replace(negative, positive)
        
        return prompt
```

---

### 3. Retry Logic with Escalating Refinement

```python
def generate_with_policy_handling(self, prompt, output_path, max_attempts=3):
    """
    Generate image with automatic prompt refinement on policy blocks.
    
    Args:
        prompt: Original prompt
        output_path: Where to save
        max_attempts: Maximum refinement attempts
        
    Returns:
        Success status and path
    """
    refiner = SafePromptGenerator()
    
    for attempt in range(max_attempts):
        try:
            if attempt == 0:
                current_prompt = prompt
            else:
                # Refine prompt with increasing strength
                current_prompt = refiner.refine_prompt(prompt)
                print(f"[REFINE] Attempt {attempt + 1}: {current_prompt[:50]}...")
            
            # Attempt generation
            result = self.generate_image(current_prompt, output_path)
            
            if result:
                print(f"[SUCCESS] Generated with prompt: {current_prompt[:50]}...")
                return True, output_path
                
        except PolicyViolationError as e:
            print(f"[POLICY] Blocked: {str(e)}")
            
            if attempt < max_attempts - 1:
                print(f"[RETRY] Refining prompt and retrying...")
                continue
            else:
                print(f"[FAILED] Could not generate after {max_attempts} attempts")
                return False, None
        
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False, None
    
    return False, None
```

---

### 4. Error Detection and Handling

**Detect policy blocks in your automation**:

```python
def detect_policy_block(self, driver):
    """
    Check if content was blocked by policy.
    
    Returns:
        True if blocked, False otherwise
    """
    # Common policy block indicators
    block_indicators = [
        "content policy",
        "can't generate",
        "unable to create",
        "violates our policies",
        "try a different prompt",
    ]
    
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        for indicator in block_indicators:
            if indicator in page_text:
                print(f"[POLICY] Detected block: {indicator}")
                return True
        
        return False
        
    except Exception:
        return False
```

---

### 5. Generic Character Descriptions

**Use archetypal descriptions instead of specific references**:

```python
CHARACTER_ARCHETYPES = {
    "hero": "A brave protagonist in heroic attire, noble expression",
    "wizard": "An elderly sage with long robes and mystical staff",
    "warrior": "A strong fighter in protective armor, determined pose",
    "explorer": "An adventurer with travel gear, curious expression",
}

def get_safe_character_prompt(character_type, scene_context):
    """
    Generate policy-compliant character prompts.
    
    Args:
        character_type: Type of character (hero, wizard, etc.)
        scene_context: Scene description
        
    Returns:
        Safe, descriptive prompt
    """
    base_description = CHARACTER_ARCHETYPES.get(
        character_type, 
        "A character in appropriate attire"
    )
    
    return f"{base_description}, {scene_context}, professional quality, detailed"
```

---

### 6. Logging and Analytics

**Track what prompts work and which don't**:

```python
import json
from datetime import datetime

class PromptAnalytics:
    """Track prompt success rates for optimization."""
    
    def __init__(self, log_file="prompt_analytics.json"):
        self.log_file = log_file
        self.load_data()
    
    def log_attempt(self, prompt, success, reason=None):
        """Log a generation attempt."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt[:100],  # Truncate for privacy
            "success": success,
            "reason": reason
        }
        
        self.data["attempts"].append(entry)
        self.save_data()
    
    def get_success_rate(self):
        """Get overall success rate."""
        total = len(self.data["attempts"])
        if total == 0:
            return 0.0
        
        successful = sum(1 for a in self.data["attempts"] if a["success"])
        return successful / total
    
    def get_common_failures(self, limit=10):
        """Get most common failure reasons."""
        failures = [a for a in self.data["attempts"] if not a["success"]]
        # Aggregate by reason
        # ... implementation ...
```

---

## Best Practices

### ✅ DO:
1. **Use descriptive, professional language**
2. **Test prompts manually first**
3. **Implement automatic refinement**
4. **Log failures for learning**
5. **Focus on artistic style and composition**
6. **Use generic archetypes** instead of specific characters
7. **Add positive framing** (what you want, not what you don't want)

### ❌ DON'T:
1. Try to bypass safety systems maliciously
2. Generate copyrighted or trademarked content
3. Create content violating policies
4. Use celebrity names or likenesses
5. Generate explicit or violent content

---

## Integration Example

**Add to your image_generator.py**:

```python
from flowchart.common.safe_prompt_generator import SafePromptGenerator

class DreaminaGenerator:
    def __init__(self, headless=False, profile_path=None):
        self.driver = start_browser(profile_path, headless)
        self.prompt_refiner = SafePromptGenerator()
        self.analytics = PromptAnalytics()
    
    def generate_image_safe(self, prompt, output_path, max_retries=3):
        """Generate with automatic policy handling."""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    prompt = self.prompt_refiner.refine_prompt(prompt)
                
                result = self.generate_image(prompt, output_path)
                
                if self.detect_policy_block(self.driver):
                    raise PolicyViolationError("Content blocked by policy")
                
                if result:
                    self.analytics.log_attempt(prompt, True)
                    return result
                    
            except PolicyViolationError:
                self.analytics.log_attempt(prompt, False, "policy_block")
                if attempt < max_retries - 1:
                    print(f"[REFINE] Attempt {attempt + 1} failed, refining...")
                    continue
        
        return None
```

---

## Summary

The key is **working WITH the system, not against it**:

1. ✅ **Better prompts** = Better results
2. ✅ **Automatic refinement** = Fewer failures
3. ✅ **Error handling** = Robust automation
4. ✅ **Analytics** = Continuous improvement

This makes your automation **more reliable** while staying within Google's guidelines.
