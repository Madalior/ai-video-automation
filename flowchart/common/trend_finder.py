import random
import time
import json
from dotenv import load_dotenv

load_dotenv()

class TrendFinder:
    def __init__(self):
        self.popular_niches = [
            "Ancient Mysteries",
            "Future Technology",
            "Space Exploration",
            "True Crime Stories",
            "Motivation & Success",
            "Nature & Wildlife",
            "Psychology Facts",
            "Luxury Lifestyle"
        ]

    def find_trends(self):
        """
        Uses LLM Manager to identify trending niches.
        """
        print("[INFO] AI Trend Analysis: identifying top viral niches...")
        from flowchart.common.llm_manager import LLMManager
        llm = LLMManager()
        
        prompt = """
        Identify 4 high-potential, viral video niches for YouTube/TikTok right now.
        Exclude generic 'AI' topics. Focus on things like History, Mystery, Tech, etc.
        Return ONLY a JSON list of objects:
        [ {"niche": "Name", "score": 95, "reason": "Why it is trending"} ]
        """
        
        result = llm.generate(prompt, json_mode=True)
        return result if result else [
            {"niche": "Hidden History", "score": 90, "reason": "Fallback Trend"},
            {"niche": "Future Tech", "score": 85, "reason": "Fallback Trend"}
        ]

    def select_niche(self):
        """
        Presents trends and asks user to select one.
        Currently defaults to automated selection for the pipeline.
        """
        trends = self.find_trends()
        print("\n[INFO] Top Trending Niches Found:")
        for idx, trend in enumerate(trends):
            print(f"{idx + 1}. {trend['niche']} (Score: {trend['score']})")
        
        # For full automation, we pick the highest score
        selected = max(trends, key=lambda x: x['score'])
        print(f"\n[SUCCESS] Automatically selected best niche: {selected['niche']}")
        return selected['niche']

    def find_video_ideas(self, niche):
        """
        Generates video ideas for a specific niche.
        """
        print(f"[INFO] Brainstorming video ideas for: {niche}...")
        # Simulate idea generation
        ideas = [
            f"The Untold Truth of {niche}",
            f"10 Mind-Blowing Facts About {niche}",
            f"Why {niche} will Change the World in 2025"
        ]
        
        print("\n[INFO] Suggested Video Ideas:")
        for idx, idea in enumerate(ideas):
            print(f"{idx + 1}. {idea}")
            
        return ideas[0] # Return the first one for automation

if __name__ == "__main__":
    tf = TrendFinder()
    niche = tf.select_niche()
    video_idea = tf.find_video_ideas(niche)
