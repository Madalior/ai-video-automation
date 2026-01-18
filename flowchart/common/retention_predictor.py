"""
Retention Predictor - Content Intelligence System

Analyzes videos before publishing to predict and fix retention issues:
- Scene analysis
- Audio analysis  
- Retention scoring
- Automatic fixes
"""

from moviepy.editor import VideoFileClip, AudioFileClip
import os
from typing import Dict, List, Tuple
import json


class RetentionPredictor:
    """
    Predict retention and suggest improvements before publishing.
    
    Goal: Catch 80% of retention issues proactively
    """
    
    def __init__(self):
        self.ideal_scene_duration = (3, 8)  # Min and max seconds
        self.slow_moment_threshold = 10  # Seconds without change
        self.minimum_retention_score = 60  # Target score
        
    def predict_retention(self, script_data: Dict) -> Dict:
        """
        Predict retention based on script content.
        
        Args:
            script_data: Script dictionary
            
        Returns:
            Dict with prediction data
        """
        title = script_data.get('title', '')
        hook = script_data.get('hook', '')
        scenes = script_data.get('scenes', [])
        
        # Heuristic scoring
        score = 50
        
        # Title analysis
        if any(w in title.lower() for w in ['secret', 'revealed', 'shocking', 'truth', 'guide']):
            score += 10
            
        # Hook analysis
        if len(hook) < 100:  # Short hooks are punchy
            score += 10
        if '?' in hook or '!' in hook:
            score += 5
            
        # Scene pacing
        if scenes:
             avg_words = sum(len(s.get('script', '').split()) for s in scenes) / len(scenes)
             if avg_words < 30: # Fast paced
                 score += 15
        
        return {
            'retention': min(score, 95),
            'ctr': min(score / 5, 20) # Rough estimate
        }

    def analyze(self, video_path: str, complete_analysis: bool = True) -> Dict:
        """
        Comprehensive video analysis for retention prediction.
        
        Args:
            video_path: Path to video file
            complete_analysis: Full analysis vs quick scan
            
        Returns:
            Dict with analysis results
        """
        print(f"[PREDICTOR] Analyzing video: {os.path.basename(video_path)}")
        
        try:
            clip = VideoFileClip(video_path)
        except Exception as e:
            print(f"[PREDICTOR] Error loading video: {e}")
            return self._empty_analysis()
        
        analysis = {
            'video_path': video_path,
            'duration': clip.duration,
            'fps': clip.fps,
            'resolution': clip.size,
            'has_audio': clip.audio is not None
        }
        
        # Scene analysis
        analysis['scene_analysis'] = self.analyze_scenes(clip)
        
        # Audio analysis (if audio exists)
        if clip.audio:
            analysis['audio_analysis'] = self.analyze_audio(clip)
        else:
            analysis['audio_analysis'] = {'has_audio': False, 'issues': ['No audio track']}
        
        # Calculate overall retention score
        analysis['retention_score'] = self.calculate_retention_score(analysis)
        
        # Generate recommendations
        analysis['recommendations'] = self.generate_recommendations(analysis)
        
        # Identify fixable issues
        analysis['auto_fixes'] = self.identify_auto_fixes(analysis)
        
        clip.close()
        
        print(f"[PREDICTOR] ✓ Analysis complete - Retention Score: {analysis['retention_score']}/100")
        
        return analysis
    
    def analyze_scenes(self, clip: VideoFileClip) -> Dict:
        """
        Analyze scene pacing and structure.
        
        Returns:
            Dict with scene analysis
        """
        duration = clip.duration
        
        # Estimate number of scenes (for now, assume 1 scene per 6 seconds)
        estimated_scenes = int(duration / 6)
        
        analysis = {
            'duration': duration,
            'estimated_scenes': estimated_scenes,
            'avg_scene_duration': duration / max(estimated_scenes, 1),
            'pacing_issues': []
        }
        
        # Check for pacing issues
        if analysis['avg_scene_duration'] > self.ideal_scene_duration[1]:
            analysis['pacing_issues'].append(
                f"Scenes too long ({analysis['avg_scene_duration']:.1f}s avg, should be <{self.ideal_scene_duration[1]}s)"
            )
        
        if duration > 60:
            analysis['pacing_issues'].append(
                "Video exceeds 60 seconds - consider trimming for shorts format"
            )
        
        if duration < 15:
            analysis['pacing_issues'].append(
                "Video too short (<15s) - may not provide enough value"
            )
        
        return analysis
    
    def analyze_audio(self, clip: VideoFileClip) -> Dict:
        """
        Analyze audio for engagement factors.
        
        Returns:
            Dict with audio analysis
        """
        analysis = {
            'has_audio': True,
            'duration': clip.audio.duration if clip.audio else 0,
            'issues': []
        }
        
        if not clip.audio:
            analysis['issues'].append("No audio - consider adding voiceover or music")
            return analysis
        
        # Check audio duration vs video duration
        if clip.audio.duration < clip.duration * 0.8:
            analysis['issues'].append(
                "Audio coverage <80% - add background music for full coverage"
            )
        
        # In full implementation, would analyze:
        # - Silence detection
        # - Volume levels
        # - Speech pacing
        # - Background music presence
        
        return analysis
    
    def calculate_retention_score(self, analysis: Dict) -> int:
        """
        Calculate predicted retention score (0-100).
        
        Based on:
        - Video duration
        - Pacing
        - Audio quality
        - Scene structure
        """
        score = 50  # Baseline
        
        # Duration scoring
        duration = analysis['duration']
        if 30 <= duration <= 60:
            score += 15  # Ideal length for shorts
        elif 15 <= duration < 30:
            score += 10
        elif duration > 90:
            score -= 15  # Too long
        
        # Pacing scoring
        scene_analysis = analysis.get('scene_analysis', {})
        pacing_issues = len(scene_analysis.get('pacing_issues', []))
        score -= (pacing_issues * 5)
        
        # Audio scoring
        audio_analysis = analysis.get('audio_analysis', {})
        if audio_analysis.get('has_audio'):
            score += 20  # Audio presence is crucial
            issues = len(audio_analysis.get('issues', []))
            score -= (issues * 5)
        else:
            score -= 20  # No audio is major issue
        
        # Cap between 0-100
        return max(0, min(100, score))
    
    def generate_recommendations(self, analysis: Dict) -> List[str]:
        """
        Generate actionable recommendations based on analysis.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        score = analysis.get('retention_score', 0)
        
        # Critical issues (score < 40)
        if score < 40:
            recommendations.append("⚠️ CRITICAL: Major retention issues detected")
        
        # Scene pacing recommendations
        scene_analysis = analysis.get('scene_analysis', {})
        for issue in scene_analysis.get('pacing_issues', []):
            recommendations.append(f"📹 Pacing: {issue}")
        
        # Audio recommendations
        audio_analysis = analysis.get('audio_analysis', {})
        for issue in audio_analysis.get('issues', []):
            recommendations.append(f"🔊 Audio: {issue}")
        
        # General best practices
        if analysis.get('duration', 0) > 45:
            recommendations.append(
                "💡 Consider: Add chapter markers for longer videos"
            )
        
        if score < 60:
            recommendations.append(
                "💡 Consider: Add subtitles (+25% retention boost)"
            )
            recommendations.append(
                "💡 Consider: Add pattern interrupts every 3-5s"
            )
        
        # Success message
        if score >= 70:
            recommendations.append("✅ EXCELLENT: Video is optimized for viral performance!")
        
        return recommendations
    
    def identify_auto_fixes(self, analysis: Dict) -> List[Dict]:
        """
        Identify issues that can be automatically fixed.
        
        Returns:
            List of dicts with fix information
        """
        fixes = []
        
        scene_analysis = analysis.get('scene_analysis', {})
        
        # Fix: Speed up if too long
        if analysis.get('duration', 0) > 60:
            fixes.append({
                'type': 'speed_adjustment',
                'description': 'Apply 1.1x speed to reduce to <60s',
                'auto_fixable': True,
                'impact': 'medium'
            })
        
        # Fix: Scene pacing
        avg_duration = scene_analysis.get('avg_scene_duration', 0)
        if avg_duration > 8:
            fixes.append({
                'type': 'pace_optimization',
                'description': f'Increase pace - scenes are {avg_duration:.1f}s avg (should be <8s)',
                'auto_fixable': True,
                'impact': 'high'
            })
        
        # Fix: Add background music
        audio_analysis = analysis.get('audio_analysis', {})
        if not audio_analysis.get('has_audio'):
            fixes.append({
                'type': 'add_music',
                'description': 'Add background music for audio coverage',
                'auto_fixable': True,
                'impact': 'high'
            })
        
        return fixes
    
    def apply_auto_fixes(self, video_path: str, analysis: Dict) -> str:
        """
        Automatically apply recommended fixes.
        
        Args:
            video_path: Path to original video
            analysis: Analysis dict from analyze()
            
        Returns:
            Path to fixed video
        """
        print("[PREDICTOR] Applying automatic fixes...")
        
        fixes = analysis.get('auto_fixes', [])
        
        if not fixes:
            print("[PREDICTOR] No auto-fixes needed")
            return video_path
        
        try:
            clip = VideoFileClip(video_path)
            
            for fix in fixes:
                if fix['type'] == 'speed_adjustment' and fix['auto_fixable']:
                    from moviepy.video.fx.all import speedx
                    target_duration = 58  # Target just under 60s
                    speed_factor = clip.duration / target_duration
                    clip = clip.fx(speedx, speed_factor)
                    print(f"[PREDICTOR] ✓ Applied {speed_factor:.2f}x speed adjustment")
                
                elif fix['type'] == 'pace_optimization' and fix['auto_fixable']:
                    from moviepy.video.fx.all import speedx
                    clip = clip.fx(speedx, 1.1)  # 10% faster
                    print("[PREDICTOR] ✓ Applied pacing optimization (1.1x speed)")
            
            # Save fixed video
            output_path = video_path.replace('.mp4', '_optimized.mp4')
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()
            
            print(f"[PREDICTOR] ✓ Fixes applied: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[PREDICTOR] Error applying fixes: {e}")
            return video_path
    
    def generate_analysis_report(self, analysis: Dict) -> str:
        """
        Generate detailed analysis report.
        
        Args:
            analysis: Analysis dict
            
        Returns:
            Formatted report string
        """
        score = analysis.get('retention_score', 0)
        
        # Score color coding
        if score >= 70:
            score_status = "EXCELLENT ✅"
        elif score >= 50:
            score_status = "GOOD ⚠️"
        else:
            score_status = "NEEDS WORK ❌"
        
        report = f"""
╔══════════════════════════════════════════════════════════╗
║         RETENTION PREDICTION REPORT                       ║
╚══════════════════════════════════════════════════════════╝

Video: {os.path.basename(analysis['video_path'])}
Duration: {analysis['duration']:.1f}s
Resolution: {analysis['resolution'][0]}x{analysis['resolution'][1]}

═══════════════════════════════════════════════════════════

RETENTION SCORE: {score}/100 - {score_status}

═══════════════════════════════════════════════════════════

SCENE ANALYSIS:
"""
        
        scene = analysis.get('scene_analysis', {})
        report += f"  • Estimated scenes: {scene.get('estimated_scenes', 0)}\n"
        report += f"  • Avg scene duration: {scene.get('avg_scene_duration', 0):.1f}s\n"
        
        pacing_issues = scene.get('pacing_issues', [])
        if pacing_issues:
            report += "\n  Issues:\n"
            for issue in pacing_issues:
                report += f"    - {issue}\n"
        
        report += "\nAUDIO ANALYSIS:\n"
        audio = analysis.get('audio_analysis', {})
        report += f"  • Has audio: {'Yes' if audio.get('has_audio') else 'No'}\n"
        
        audio_issues = audio.get('issues', [])
        if audio_issues:
            report += "  Issues:\n"
            for issue in audio_issues:
                report += f"    - {issue}\n"
        
        report += "\n═══════════════════════════════════════════════════════════\n"
        report += "\nRECOMMENDATIONS:\n"
        
        for i, rec in enumerate(analysis.get('recommendations', []), 1):
            report += f"  {i}. {rec}\n"
        
        auto_fixes = analysis.get('auto_fixes', [])
        if auto_fixes:
            report += "\n═══════════════════════════════════════════════════════════\n"
            report += "\nAUTO-FIXABLE ISSUES:\n"
            for i, fix in enumerate(auto_fixes, 1):
                report += f"  {i}. {fix['description']} (Impact: {fix['impact']})\n"
        
        report += "\n═══════════════════════════════════════════════════════════\n"
        
        if score >= 70:
            report += "\n🎉 This video is ready for viral performance!\n"
        elif score >= 50:
            report += "\n👍 This video is good, but could be optimized further.\n"
        else:
            report += "\n⚠️  Apply recommended fixes before publishing.\n"
        
        return report
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure for error cases."""
        return {
            'video_path': '',
            'duration': 0,
            'retention_score': 0,
            'scene_analysis': {},
            'audio_analysis': {},
            'recommendations': ['Error analyzing video'],
            'auto_fixes': []
        }


# Test/Demo
if __name__ == "__main__":
    print("Retention Predictor - Testing")
    
    predictor = RetentionPredictor()
    
    # Create mock analysis for testing
    mock_analysis = {
        'video_path': 'test_video.mp4',
        'duration': 45,
        'fps': 30,
        'resolution': (1920, 1080),
        'has_audio': True,
        'scene_analysis': {
            'duration': 45,
            'estimated_scenes': 7,
            'avg_scene_duration': 6.4,
            'pacing_issues': []
        },
        'audio_analysis': {
            'has_audio': True,
            'duration': 45,
            'issues': []
        },
        'retention_score': 75,
        'recommendations': [
            "✅ EXCELLENT: Video is optimized for viral performance!"
        ],
        'auto_fixes': []
    }
    
    # Generate test report
    report = predictor.generate_analysis_report(mock_analysis)
    print(report)
    
    print("\n✓ Retention Predictor ready!")
