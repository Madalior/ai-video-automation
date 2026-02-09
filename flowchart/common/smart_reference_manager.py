"""
Smart Reference Manager for Veo 3.1 Multi-Reference Support

Allows users to specify typed references (character, background, continuity)
and intelligently orders them for optimal Veo 3.1 generation.
"""

import os
from typing import Union, List, Dict, Optional


class SmartReferenceManager:
    """
    Manages intelligent reference ordering for video generation.
    
    Veo 3.1 doesn't differentiate between reference types, but research suggests
    the first reference has the most weight. This manager orders references by priority.
    """
    
    PRIORITY_ORDER = ['continuity', 'character', 'background']
    
    def __init__(self, mode='smart_order'):
        """
        Initialize reference manager.
        
        Args:
            mode: Processing mode
                - 'smart_order': Order by priority (continuity > character > background)
                - 'composite': Blend into single image (future feature)
                - 'selective': Choose based on scene context (future feature)
        """
        self.mode = mode
    
    def process_references(
        self, 
        references: Union[str, List[str], Dict[str, str]], 
        scene_context: Optional[Dict] = None
    ) -> List[str]:
        """
        Process references into Veo-compatible list.
        
        Args:
            references: Can be:
                - str: Single reference path (legacy)
                - List[str]: Multiple paths (legacy)
                - Dict: Typed references {'character': path, 'background': path, 'continuity': path}
            scene_context: Optional scene metadata for smart/selective modes
        
        Returns:
            List of up to 3 validated image paths, ordered by priority
        
        Examples:
            >>> manager = SmartReferenceManager()
            
            # Legacy: single path
            >>> manager.process_references("char.png")
            ['char.png']
            
            # Legacy: list
            >>> manager.process_references(["img1.png", "img2.png"])
            ['img1.png', 'img2.png']
            
            # NEW: typed dict
            >>> manager.process_references({
            ...     'character': 'detective.png',
            ...     'background': 'room.png',
            ...     'continuity': 'prev_frame.png'
            ... })
            ['prev_frame.png', 'detective.png', 'room.png']  # Ordered by priority
        """
        # Handle None
        if not references:
            return []
        
        # Handle dict (NEW typed references)
        if isinstance(references, dict):
            if self.mode == 'smart_order':
                return self._smart_order(references)
            elif self.mode == 'composite':
                # Future: composite mode
                raise NotImplementedError("Composite mode not yet implemented")
            elif self.mode == 'selective':
                # Future: selective mode
                raise NotImplementedError("Selective mode not yet implemented")
            else:
                return self._smart_order(references)  # Default to smart order
        
        # Handle list (legacy)
        elif isinstance(references, list):
            return self._validate_paths(references)[:3]  # Max 3
        
        # Handle string (legacy single path)
        else:
            return self._validate_paths([references])
    
    def _smart_order(self, refs: Dict[str, str]) -> List[str]:
        """
        Order references by priority: continuity > character > background.
        
        Strategy:
        - Continuity (previous frame) has character + background + style → highest priority
        - Character (appearance) is crucial for consistency → medium priority
        - Background (environmental style) supplements → lowest priority
        
        Args:
            refs: Dict with keys 'character', 'background', 'continuity'
        
        Returns:
            Ordered list of paths (max 3)
        """
        ordered = []
        
        # Add in priority order
        for ref_type in self.PRIORITY_ORDER:
            if ref_type in refs and refs[ref_type]:
                path = refs[ref_type]
                # Validate path exists
                if os.path.exists(path):
                    ordered.append(path)
                else:
                    print(f"[WARNING] {ref_type.capitalize()} reference not found: {path}")
        
        # Limit to 3 (Veo maximum)
        result = ordered[:3]
        
        # Log the ordering
        if result:
            print(f"[SMART REF] Ordered {len(result)} reference(s) by priority:")
            for i, path in enumerate(result, 1):
                ref_type = self._identify_type(path, refs)
                print(f"  {i}. {ref_type}: {os.path.basename(path)}")
        
        return result
    
    def _identify_type(self, path: str, refs: Dict[str, str]) -> str:
        """Identify which type a path corresponds to."""
        for ref_type, ref_path in refs.items():
            if ref_path == path:
                return ref_type.capitalize()
        return "Unknown"
    
    def _validate_paths(self, paths: List[str]) -> List[str]:
        """
        Validate that paths exist.
        
        Args:
            paths: List of file paths
        
        Returns:
            List of validated paths that exist
        """
        validated = []
        for path in paths:
            if path and os.path.exists(path):
                validated.append(path)
            elif path:
                print(f"[WARNING] Reference image not found: {path}")
        
        return validated
    
    def create_reference_dict(
        self,
        character: Optional[str] = None,
        background: Optional[str] = None,
        continuity: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Helper to create typed reference dictionary.
        
        Args:
            character: Path to character reference image
            background: Path to background/style reference
            continuity: Path to previous frame for continuity
        
        Returns:
            Dict with non-None values
        
        Example:
            >>> refs = manager.create_reference_dict(
            ...     character='detective.png',
            ...     continuity='prev_frame.png'
            ... )
            >>> # Returns: {'character': 'detective.png', 'continuity': 'prev_frame.png'}
        """
        refs = {}
        if character:
            refs['character'] = character
        if background:
            refs['background'] = background
        if continuity:
            refs['continuity'] = continuity
        return refs


# Convenience function for quick usage
def order_references(
    character: Optional[str] = None,
    background: Optional[str] = None,
    continuity: Optional[str] = None
) -> List[str]:
    """
    Quick helper to order references by priority.
    
    Args:
        character: Character appearance reference
        background: Background/style reference
        continuity: Previous frame reference
    
    Returns:
        Ordered list of paths (max 3)
    
    Example:
        >>> refs = order_references(
        ...     character='detective.png',
        ...     background='room.png',
        ...     continuity='prev_frame.png'
        ... )
        >>> # Returns: ['prev_frame.png', 'detective.png', 'room.png']
    """
    manager = SmartReferenceManager()
    ref_dict = manager.create_reference_dict(character, background, continuity)
    return manager.process_references(ref_dict)


if __name__ == "__main__":
    print("="*60)
    print("Smart Reference Manager - Test Suite")
    print("="*60)
    
    manager = SmartReferenceManager()
    
    # Test 1: Legacy single path
    print("\n[Test 1] Legacy single path:")
    result = manager.process_references("test.png")
    print(f"Input: 'test.png'")
    print(f"Output: {result}")
    
    # Test 2: Legacy list
    print("\n[Test 2] Legacy list:")
    result = manager.process_references(["img1.png", "img2.png"])
    print(f"Input: ['img1.png', 'img2.png']")
    print(f"Output: {result}")
    
    # Test 3: Typed dict (all types)
    print("\n[Test 3] Typed dict (all 3 types):")
    refs = {
        'character': 'detective.png',
        'background': 'room.png',
        'continuity': 'prev_frame.png'
    }
    print(f"Input: {refs}")
    result = manager.process_references(refs)
    print(f"Output: {result}")
    print(f"Order: continuity → character → background")
    
    # Test 4: Partial dict
    print("\n[Test 4] Partial dict (character + continuity only):")
    refs = {
        'character': 'detective.png',
        'continuity': 'prev_frame.png'
    }
    print(f"Input: {refs}")
    result = manager.process_references(refs)
    print(f"Output: {result}")
    
    # Test 5: Helper function
    print("\n[Test 5] Helper function:")
    result = order_references(
        character='detective.png',
        continuity='prev_frame.png'
    )
    print(f"order_references(character='detective.png', continuity='prev_frame.png')")
    print(f"Output: {result}")
    
    print("\n" + "="*60)
    print("Smart Reference Manager Ready! ✅")
    print("="*60)
