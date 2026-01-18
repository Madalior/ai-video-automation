"""
Genkit AI Service Python Client

Simple client library for interacting with the Genkit Go microservice.
"""

import requests
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class GenkitClient:
    """Client for Genkit AI Service"""
    
    def __init__(self, base_url: str = "http://localhost:3400", timeout: int = 30):
        """
        Initialize Genkit client
        
        Args:
            base_url: Base URL of the Genkit service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._check_health()
    
    def _check_health(self):
        """Check if service is available"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Genkit AI Service is healthy")
            else:
                logger.warning("⚠ Genkit service returned non-200 status")
        except requests.exceptions.RequestException:
            logger.warning("⚠ Genkit AI Service is not available - features will be disabled")
    
    def _post(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make POST request to service"""
        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}",
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                return result.get('data')
            else:
                logger.error(f"Genkit error: {result.get('error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Genkit request failed: {e}")
            return None
    
    def optimize_seo(
        self,
        script: str,
        niche: str,
        target_audience: Optional[str] = None,
        duration: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Optimize SEO metadata for video
        
        Args:
            script: Video script content
            niche: Video niche/category
            target_audience: Target audience (optional)
            duration: Video duration in seconds (optional)
            
        Returns:
            Dict with title, description, tags, hashtags, thumbnail_text, keywords
        """
        data = {
            "script": script,
            "niche": niche
        }
        if target_audience:
            data["target_audience"] = target_audience
        if duration:
            data["duration"] = duration
        
        result = self._post("optimize-seo", data)
        if result:
            logger.info(f"✓ SEO optimized: {result.get('title', 'N/A')}")
        return result
    
    def enhance_prompt(
        self,
        prompt: str,
        style: Optional[str] = None,
        character_context: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Enhance AI image generation prompt
        
        Args:
            prompt: Basic prompt to enhance
            style: Desired style (optional)
            character_context: Character consistency info (optional)
            
        Returns:
            Dict with enhanced_prompt, improvements, style_guide
        """
        data = {"prompt": prompt}
        if style:
            data["style"] = style
        if character_context:
            data["character_context"] = character_context
        
        result = self._post("enhance-prompt", data)
        if result:
            logger.info(f"✓ Prompt enhanced with {len(result.get('improvements', []))} improvements")
        return result
    
    def validate_content(
        self,
        script: str,
        scenes: List[Dict],
        duration: int
    ) -> Optional[Dict]:
        """
        Validate video content for issues
        
        Args:
            script: Complete script
            scenes: List of scenes with duration, narration, visual_description
            duration: Total duration in seconds
            
        Returns:
            Dict with is_valid, issues (list), summary
        """
        data = {
            "script": script,
            "scenes": scenes,
            "duration": duration
        }
        
        result = self._post("validate-content", data)
        if result:
            issues_count = len(result.get('issues', []))
            if issues_count > 0:
                logger.warning(f"⚠ Found {issues_count} validation issues")
            else:
                logger.info("✓ Content validation passed")
        return result
    
    def recover_error(
        self,
        error: str,
        context: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get error recovery strategies
        
        Args:
            error: Error message
            context: Error context (dict)
            prompt: Original prompt that failed (optional)
            
        Returns:
            Dict with analysis, strategies, fixed_prompt, recommendations
        """
        data = {
            "error": error,
            "context": context
        }
        if prompt:
            data["prompt"] = prompt
        
        result = self._post("recover-error", data)
        if result:
            strategies_count = len(result.get('strategies', []))
            logger.info(f"✓ Generated {strategies_count} recovery strategies")
        return result
    
    def discover_niches(
        self,
        category: str,
        competition_level: Optional[str] = None,
        monetization_potential: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Discover trending niches
        
        Args:
            category: Content category
            competition_level: low/medium/high (optional)
            monetization_potential: low/medium/high (optional)
            
        Returns:
            Dict with trending_niches (list), analysis
        """
        data = {"category": category}
        if competition_level:
            data["competition_level"] = competition_level
        if monetization_potential:
            data["monetization_potential"] = monetization_potential
        
        result = self._post("discover-niches", data)
        if result:
            niches_count = len(result.get('trending_niches', []))
            logger.info(f"✓ Discovered {niches_count} trending niches")
        return result
    
    def optimize_antigravity_prompt(
        self,
        goal: str,
        codebase_context: Optional[Dict] = None,
        additional_info: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Optimize prompt for Antigravity AI assistant
        
        Args:
            goal: User's high-level goal/objective
            codebase_context: Context about the codebase (files, errors, etc.)
            additional_info: Any additional information (optional)
            
        Returns:
            Dict with optimized_prompt, context_summary, relevant_files, estimated_complexity
        """
        data = {"goal": goal}
        if codebase_context:
            data["codebase_context"] = codebase_context
        if additional_info:
            data["additional_info"] = additional_info
        
        result = self._post("optimize-antigravity-prompt", data)
        if result:
            complexity = result.get('estimated_complexity', 'unknown')
            logger.info(f"✓ Prompt optimized (complexity: {complexity})")
        return result



# Convenience instance
genkit = GenkitClient()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Test SEO optimization
    seo = genkit.optimize_seo(
        script="A woman explores luxury hotels around the world...",
        niche="luxury travel",
        target_audience="affluent millennials"
    )
    if seo:
        print(f"\nTitle: {seo['title']}")
        print(f"Tags: {', '.join(seo['tags'][:5])}...")
    
    # Test prompt enhancement
    enhanced = genkit.enhance_prompt(
        prompt="woman in hotel lobby",
        style="cinematic"
    )
    if enhanced:
        print(f"\nEnhanced prompt: {enhanced['enhanced_prompt'][:100]}...")
