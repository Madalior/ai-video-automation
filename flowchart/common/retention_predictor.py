"""
🔥 GOD MASTER MODE — Retention Predictor
════════════════════════════════════════════

Script-aware content intelligence system:
- Script.json integration (real scene data vs heuristic guessing)
- Emotion-weighted scoring
- Dialogue density analysis
- Visual variety scoring
- Smart auto-fixes using scene awareness
- Comprehensive analysis reports

Goal: Catch 95% of retention issues proactively
"""

from moviepy.editor import VideoFileClip, AudioFileClip
import os
import json
from typing import Dict, List, Tuple, Optional


# Emotion intensity map (shared with retention_optimizer)
EMOTION_INTENSITY = {
    'anger': 0.9, 'rage': 0.95, 'shock': 0.9, 'fear': 0.85,
    'panic': 0.9, 'desperation': 0.85, 'horror': 0.9,
    'excitement': 0.8, 'thrill': 0.85, 'triumph': 0.8,
    'tension': 0.7, 'suspense': 0.7, 'curiosity': 0.65,
    'frustration': 0.7, 'confusion': 0.6, 'determination': 0.65,
    'hope': 0.6, 'jealousy': 0.7, 'guilt': 0.65,
    'mystery': 0.6, 'surprise': 0.75, 'revelation': 0.8,
    'sadness': 0.4, 'melancholy': 0.35, 'nostalgia': 0.3,
    'calm': 0.2, 'peace': 0.15, 'relief': 0.4,
    'love': 0.5, 'tenderness': 0.3, 'acceptance': 0.35,
    'reflection': 0.25, 'contemplation': 0.2,
}


class RetentionPredictor:
    """
    🔥 GOD MASTER MODE — Retention Predictor

    Script-aware content analysis that uses real scene data
    instead of heuristic estimates.

    Goal: Catch 95% of retention issues proactively
    """

    def __init__(self):
        self.ideal_scene_duration = (3, 8)
        self.slow_moment_threshold = 10
        self.minimum_retention_score = 60

    # ════════════════════════════════════════════════════════
    # 1. SCRIPT-AWARE PREDICTION
    # ════════════════════════════════════════════════════════
    def predict_from_script(self, script_json_path: str) -> Dict:
        """
        🔥 Predict retention using full script.json data.

        Uses real scene data: emotions, dialogue, visual variety,
        shot types, camera movements, audio cues.

        Returns:
            Dict with comprehensive prediction data
        """
        with open(script_json_path, 'r', encoding='utf-8') as f:
            script = json.load(f)

        scenes = script.get('scenes', [])
        title = script.get('title', '')

        print(f"\n{'═'*60}")
        print(f"🔮 GOD MASTER MODE — RETENTION PREDICTION")
        print(f"{'═'*60}")
        print(f"   Title: {title}")
        print(f"   Scenes: {len(scenes)}")

        # Run all analyses
        emotion_score = self._score_emotion_arc(scenes)
        dialogue_score = self._score_dialogue_density(scenes)
        visual_score = self._score_visual_variety(scenes)
        pacing_score = self._score_pacing(scenes)
        audio_score = self._score_audio_design(scenes)
        hook_score = self._score_hook_potential(scenes, script)

        # Weighted composite score
        weights = {
            'emotion': 0.25,
            'dialogue': 0.15,
            'visual': 0.20,
            'pacing': 0.15,
            'audio': 0.10,
            'hook': 0.15,
        }

        composite = (
            emotion_score * weights['emotion'] +
            dialogue_score * weights['dialogue'] +
            visual_score * weights['visual'] +
            pacing_score * weights['pacing'] +
            audio_score * weights['audio'] +
            hook_score * weights['hook']
        )

        # Generate per-scene breakdown
        scene_breakdown = self._per_scene_breakdown(scenes)

        # Generate smart recommendations
        recommendations = self._smart_recommendations(
            scenes, emotion_score, dialogue_score,
            visual_score, pacing_score, audio_score, hook_score
        )

        # Identify auto-fixes
        auto_fixes = self._smart_auto_fixes(scenes, scene_breakdown)

        prediction = {
            'title': title,
            'total_scenes': len(scenes),
            'scores': {
                'emotion_arc': round(emotion_score, 1),
                'dialogue_density': round(dialogue_score, 1),
                'visual_variety': round(visual_score, 1),
                'pacing': round(pacing_score, 1),
                'audio_design': round(audio_score, 1),
                'hook_potential': round(hook_score, 1),
                'composite': round(composite, 1),
            },
            'predicted_retention': round(min(95, composite), 1),
            'predicted_ctr': round(min(20, composite / 5), 1),
            'scene_breakdown': scene_breakdown,
            'recommendations': recommendations,
            'auto_fixes': auto_fixes,
        }

        # Print summary
        print(f"\n   📊 Predicted Retention: {prediction['predicted_retention']}%")
        print(f"   📊 Predicted CTR: {prediction['predicted_ctr']}%")
        print(f"\n   Score Breakdown:")
        for name, score in prediction['scores'].items():
            bar = '█' * int(score / 5)
            print(f"      {name:20s} [{bar:20s}] {score}/100")

        return prediction

    # ════════════════════════════════════════════════════════
    # 2. SCORING ENGINES
    # ════════════════════════════════════════════════════════
    def _score_emotion_arc(self, scenes: List[Dict]) -> float:
        """Score the emotional journey — variety and intensity."""
        if not scenes:
            return 30

        score = 50
        emotions = [s.get('emotion', '').lower() for s in scenes]
        intensities = [EMOTION_INTENSITY.get(e, 0.5) for e in emotions]

        # Emotion variety bonus (unique emotions / total)
        unique_ratio = len(set(emotions)) / len(emotions)
        score += unique_ratio * 20  # Up to +20 for all unique emotions

        # Intensity range bonus (high contrast = engaging)
        if intensities:
            intensity_range = max(intensities) - min(intensities)
            score += intensity_range * 15  # Up to +15 for full range

        # Emotional contrast between adjacent scenes
        contrasts = [abs(intensities[i] - intensities[i-1]) for i in range(1, len(intensities))]
        if contrasts:
            avg_contrast = sum(contrasts) / len(contrasts)
            score += avg_contrast * 10  # Up to +10 for strong contrasts

        # Penalty for flat arcs (all same emotion)
        if len(set(emotions)) == 1:
            score -= 25

        # Bonus for ending on high note
        if intensities and intensities[-1] >= 0.7:
            score += 5

        return min(100, max(0, score))

    def _score_dialogue_density(self, scenes: List[Dict]) -> float:
        """Score dialogue quality — subtext, variety, punchiness."""
        if not scenes:
            return 30

        score = 40
        total_dialogue = 0
        has_subtext = 0

        for scene in scenes:
            dialogue = scene.get('dialogue', '')
            subtext = scene.get('subtext', '')

            if dialogue and dialogue.lower() not in ('none', ''):
                total_dialogue += 1
                word_count = len(dialogue.split())
                # Punchy dialogue bonus (short = impactful)
                if word_count <= 10:
                    score += 5
                elif word_count <= 20:
                    score += 3

            if subtext and subtext.lower() not in ('none', ''):
                has_subtext += 1

        # Dialogue coverage
        dialogue_ratio = total_dialogue / len(scenes) if scenes else 0
        score += dialogue_ratio * 20  # Up to +20 for full coverage

        # Subtext depth bonus
        subtext_ratio = has_subtext / len(scenes) if scenes else 0
        score += subtext_ratio * 15  # Up to +15 for subtext

        return min(100, max(0, score))

    def _score_visual_variety(self, scenes: List[Dict]) -> float:
        """Score visual diversity — shot types, camera movements, lighting."""
        if not scenes:
            return 30

        score = 40
        shot_types = set()
        camera_movements = set()
        color_palettes = set()

        for scene in scenes:
            visual = scene.get('visual', {})
            shot_types.add(visual.get('shot_type', 'medium'))
            camera_movements.add(visual.get('camera_movement', 'static'))
            color_palettes.add(visual.get('color_palette', ''))

        # Shot type variety
        if len(shot_types) >= 3:
            score += 25
        elif len(shot_types) >= 2:
            score += 15
        else:
            score -= 10  # Same shot type = boring

        # Camera movement variety
        if len(camera_movements) >= 3:
            score += 20
        elif len(camera_movements) >= 2:
            score += 10

        # Color palette variety
        if len(color_palettes) >= 2:
            score += 10

        # Penalty for all static shots
        if camera_movements == {'static'}:
            score -= 15

        return min(100, max(0, score))

    def _score_pacing(self, scenes: List[Dict]) -> float:
        """Score pacing based on scene structure and shot durations."""
        if not scenes:
            return 30

        score = 50
        num_scenes = len(scenes)

        # Scene count sweet spot (4-8 scenes for a short)
        if 4 <= num_scenes <= 8:
            score += 20
        elif 2 <= num_scenes <= 3:
            score += 10
        elif num_scenes > 10:
            score -= 10  # Too many scenes = rushed

        # Check for act structure
        acts = set(s.get('act', '') for s in scenes)
        if len(acts) >= 2:
            score += 10  # Multi-act structure = better storytelling

        # Emotion pacing (alternating high/low is ideal)
        intensities = [EMOTION_INTENSITY.get(s.get('emotion', ''), 0.5) for s in scenes]
        alternations = sum(1 for i in range(1, len(intensities))
                          if (intensities[i] >= 0.6) != (intensities[i-1] >= 0.6))
        if len(intensities) > 1:
            alt_ratio = alternations / (len(intensities) - 1)
            score += alt_ratio * 15

        return min(100, max(0, score))

    def _score_audio_design(self, scenes: List[Dict]) -> float:
        """Score audio design — music, SFX, strategic silence."""
        if not scenes:
            return 30

        score = 30
        has_music = 0
        has_sfx = 0
        has_silence = 0

        for scene in scenes:
            audio = scene.get('audio', {})
            music = audio.get('music', 'none')
            sfx = audio.get('sfx', 'none')
            silence = audio.get('silence', 'none')

            if music and music.lower() not in ('none', ''):
                has_music += 1
            if sfx and sfx.lower() not in ('none', ''):
                has_sfx += 1
            if silence and silence.lower() not in ('none', ''):
                has_silence += 1

        # Music coverage
        music_ratio = has_music / len(scenes)
        score += music_ratio * 25  # Up to +25

        # SFX presence
        if has_sfx > 0:
            score += min(20, has_sfx * 8)  # Up to +20

        # Strategic silence (intentional silence is a technique)
        if has_silence > 0:
            score += 10

        # Variety of audio elements
        unique_music = set(s.get('audio', {}).get('music', '') for s in scenes) - {'none', ''}
        if len(unique_music) >= 2:
            score += 10

        return min(100, max(0, score))

    def _score_hook_potential(self, scenes: List[Dict], script: Dict) -> float:
        """Score hook potential — opening, subtext, cliffhanger material."""
        if not scenes:
            return 30

        score = 40

        # Opening scene strength
        first = scenes[0]
        first_emotion = first.get('emotion', '')
        first_intensity = EMOTION_INTENSITY.get(first_emotion.lower(), 0.5)

        if first_intensity >= 0.7:
            score += 20  # Strong emotional opening
        elif first_intensity >= 0.5:
            score += 10

        # Has dialogue in opening (voice hook)
        if first.get('dialogue', '') and first.get('dialogue', '').lower() != 'none':
            score += 10

        # Ending strength (cliffhanger potential)
        last = scenes[-1]
        last_emotion = last.get('emotion', '')
        if last_emotion.lower() in ('shock', 'revelation', 'mystery', 'suspense', 'triumph'):
            score += 15

        # Subtext throughout (deeper content = higher hook potential)
        subtext_count = sum(1 for s in scenes if s.get('subtext', '').lower() not in ('none', ''))
        if subtext_count >= len(scenes) * 0.5:
            score += 10

        return min(100, max(0, score))

    # ════════════════════════════════════════════════════════
    # 3. PER-SCENE BREAKDOWN
    # ════════════════════════════════════════════════════════
    def _per_scene_breakdown(self, scenes: List[Dict]) -> List[Dict]:
        """Generate per-scene retention risk assessment."""
        breakdown = []

        for scene in scenes:
            num = scene.get('scene_number', 0)
            emotion = scene.get('emotion', '').lower()
            intensity = EMOTION_INTENSITY.get(emotion, 0.5)
            visual = scene.get('visual', {})
            dialogue = scene.get('dialogue', '')
            audio = scene.get('audio', {})

            risk = 0
            issues = []

            # Low emotion risk
            if intensity < 0.3:
                risk += 25
                issues.append('Low emotional intensity')

            # No dialogue risk
            if not dialogue or dialogue.lower() == 'none':
                risk += 20
                issues.append('No dialogue')

            # Static camera risk
            if visual.get('camera_movement', '').lower() == 'static':
                risk += 10
                issues.append('Static camera')

            # No SFX risk
            if not audio.get('sfx') or audio.get('sfx', '').lower() == 'none':
                risk += 5
                issues.append('No sound effects')

            # No music risk
            if not audio.get('music') or audio.get('music', '').lower() == 'none':
                risk += 10
                issues.append('No music')

            breakdown.append({
                'scene_number': num,
                'emotion': emotion,
                'intensity': intensity,
                'risk_score': min(100, risk),
                'risk_level': 'HIGH' if risk >= 40 else ('MEDIUM' if risk >= 20 else 'LOW'),
                'issues': issues,
            })

        return breakdown

    # ════════════════════════════════════════════════════════
    # 4. SMART RECOMMENDATIONS
    # ════════════════════════════════════════════════════════
    def _smart_recommendations(self, scenes, emotion_score, dialogue_score,
                                visual_score, pacing_score, audio_score, hook_score) -> List[str]:
        """Generate specific recommendations based on weakest areas."""
        recs = []

        # Emotion arc
        if emotion_score < 50:
            recs.append("🎭 Emotion: Add more emotional contrast between scenes — alternate high/low intensity")
        if emotion_score < 35:
            recs.append("🎭 CRITICAL: Emotional arc is flat — add shock, revelation, or confrontation scenes")

        # Dialogue
        if dialogue_score < 50:
            recs.append("💬 Dialogue: Add punchy dialogue to more scenes — short, impactful lines")
        if dialogue_score < 35:
            recs.append("💬 CRITICAL: Very little dialogue — viewers disengage without voice/text")

        # Visual variety
        if visual_score < 50:
            recs.append("📹 Visual: Mix shot types (close-up → wide → over-shoulder) for visual rhythm")
        if visual_score < 35:
            recs.append("📹 CRITICAL: All scenes look the same — add camera movement and shot variety")

        # Pacing
        if pacing_score < 50:
            recs.append("⏱️ Pacing: Restructure scenes for better rhythm — alternate fast/slow")
        if pacing_score < 35:
            recs.append("⏱️ CRITICAL: Pacing issues detected — consider trimming or reordering scenes")

        # Audio
        if audio_score < 50:
            recs.append("🎵 Audio: Add background music and sound effects for atmosphere")
        if audio_score < 35:
            recs.append("🎵 CRITICAL: Minimal audio design — music and SFX are essential for retention")

        # Hooks
        if hook_score < 50:
            recs.append("🎣 Hooks: Strengthen opening scene — start with mystery, question, or shock")
        if hook_score < 35:
            recs.append("🎣 CRITICAL: Weak hook potential — opening 3 seconds are crucial")

        # Overall
        composite = (emotion_score + dialogue_score + visual_score +
                     pacing_score + audio_score + hook_score) / 6
        if composite >= 70:
            recs.append("✅ EXCELLENT: Script is optimized for viral retention!")
        elif composite >= 50:
            recs.append("👍 GOOD: Script has potential, apply recommendations for boost")

        return recs

    # ════════════════════════════════════════════════════════
    # 5. SMART AUTO-FIXES
    # ════════════════════════════════════════════════════════
    def _smart_auto_fixes(self, scenes: List[Dict],
                           scene_breakdown: List[Dict]) -> List[Dict]:
        """Identify auto-fixable issues using scene awareness."""
        fixes = []

        for bd in scene_breakdown:
            if bd['risk_level'] == 'HIGH':
                scene_num = bd['scene_number']

                if 'Low emotional intensity' in bd['issues']:
                    fixes.append({
                        'type': 'speed_up_scene',
                        'scene': scene_num,
                        'description': f'Scene {scene_num}: Speed up 1.1x (low emotion = shorter is better)',
                        'auto_fixable': True,
                        'impact': 'medium',
                    })

                if 'Static camera' in bd['issues']:
                    fixes.append({
                        'type': 'add_ken_burns',
                        'scene': scene_num,
                        'description': f'Scene {scene_num}: Add Ken Burns effect (slow push to add movement)',
                        'auto_fixable': True,
                        'impact': 'medium',
                    })

                if 'No music' in bd['issues']:
                    fixes.append({
                        'type': 'add_ambient_audio',
                        'scene': scene_num,
                        'description': f'Scene {scene_num}: Add ambient audio to fill silence',
                        'auto_fixable': True,
                        'impact': 'high',
                    })

        return fixes

    # ════════════════════════════════════════════════════════
    # 6. LEGACY: VIDEO FILE ANALYSIS (backward compatible)
    # ════════════════════════════════════════════════════════
    def predict_retention(self, script_data: Dict) -> Dict:
        """Predict retention based on script content (legacy)."""
        title = script_data.get('title', '')
        hook = script_data.get('hook', '')
        scenes = script_data.get('scenes', [])

        score = 50
        if any(w in title.lower() for w in ['secret', 'revealed', 'shocking', 'truth', 'guide']):
            score += 10
        if len(hook) < 100:
            score += 10
        if '?' in hook or '!' in hook:
            score += 5
        if scenes:
            avg_words = sum(len(s.get('script', '').split()) for s in scenes) / len(scenes)
            if avg_words < 30:
                score += 15

        return {'retention': min(score, 95), 'ctr': min(score / 5, 20)}

    def analyze(self, video_path: str, complete_analysis: bool = True) -> Dict:
        """Comprehensive video analysis for retention prediction."""
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
            'has_audio': clip.audio is not None,
        }

        analysis['scene_analysis'] = self.analyze_scenes(clip)

        if clip.audio:
            analysis['audio_analysis'] = self.analyze_audio(clip)
        else:
            analysis['audio_analysis'] = {'has_audio': False, 'issues': ['No audio track']}

        analysis['retention_score'] = self.calculate_retention_score(analysis)
        analysis['recommendations'] = self.generate_recommendations(analysis)
        analysis['auto_fixes'] = self.identify_auto_fixes(analysis)

        clip.close()
        print(f"[PREDICTOR] ✓ Analysis complete - Retention Score: {analysis['retention_score']}/100")
        return analysis

    def analyze_scenes(self, clip: VideoFileClip) -> Dict:
        """Analyze scene pacing and structure."""
        duration = clip.duration
        estimated_scenes = int(duration / 6)

        analysis = {
            'duration': duration,
            'estimated_scenes': estimated_scenes,
            'avg_scene_duration': duration / max(estimated_scenes, 1),
            'pacing_issues': [],
        }

        if analysis['avg_scene_duration'] > self.ideal_scene_duration[1]:
            analysis['pacing_issues'].append(
                f"Scenes too long ({analysis['avg_scene_duration']:.1f}s avg, should be <{self.ideal_scene_duration[1]}s)"
            )
        if duration > 60:
            analysis['pacing_issues'].append("Video exceeds 60 seconds - consider trimming for shorts format")
        if duration < 15:
            analysis['pacing_issues'].append("Video too short (<15s) - may not provide enough value")

        return analysis

    def analyze_audio(self, clip: VideoFileClip) -> Dict:
        """Analyze audio for engagement factors."""
        analysis = {'has_audio': True, 'duration': clip.audio.duration if clip.audio else 0, 'issues': []}

        if not clip.audio:
            analysis['issues'].append("No audio - consider adding voiceover or music")
            return analysis

        if clip.audio.duration < clip.duration * 0.8:
            analysis['issues'].append("Audio coverage <80% - add background music for full coverage")

        return analysis

    def calculate_retention_score(self, analysis: Dict) -> int:
        """Calculate predicted retention score (0-100)."""
        score = 50
        duration = analysis['duration']

        if 30 <= duration <= 60: score += 15
        elif 15 <= duration < 30: score += 10
        elif duration > 90: score -= 15

        pacing_issues = len(analysis.get('scene_analysis', {}).get('pacing_issues', []))
        score -= (pacing_issues * 5)

        audio_analysis = analysis.get('audio_analysis', {})
        if audio_analysis.get('has_audio'):
            score += 20
            score -= len(audio_analysis.get('issues', [])) * 5
        else:
            score -= 20

        return max(0, min(100, score))

    def generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        score = analysis.get('retention_score', 0)

        if score < 40:
            recommendations.append("⚠️ CRITICAL: Major retention issues detected")

        for issue in analysis.get('scene_analysis', {}).get('pacing_issues', []):
            recommendations.append(f"📹 Pacing: {issue}")

        for issue in analysis.get('audio_analysis', {}).get('issues', []):
            recommendations.append(f"🔊 Audio: {issue}")

        if analysis.get('duration', 0) > 45:
            recommendations.append("💡 Consider: Add chapter markers for longer videos")

        if score < 60:
            recommendations.append("💡 Consider: Add subtitles (+25% retention boost)")
            recommendations.append("💡 Consider: Add pattern interrupts every 3-5s")

        if score >= 70:
            recommendations.append("✅ EXCELLENT: Video is optimized for viral performance!")

        return recommendations

    def identify_auto_fixes(self, analysis: Dict) -> List[Dict]:
        """Identify issues that can be automatically fixed."""
        fixes = []
        scene_analysis = analysis.get('scene_analysis', {})

        if analysis.get('duration', 0) > 60:
            fixes.append({'type': 'speed_adjustment', 'description': 'Apply 1.1x speed to reduce to <60s',
                          'auto_fixable': True, 'impact': 'medium'})

        avg_duration = scene_analysis.get('avg_scene_duration', 0)
        if avg_duration > 8:
            fixes.append({'type': 'pace_optimization',
                          'description': f'Increase pace - scenes are {avg_duration:.1f}s avg (should be <8s)',
                          'auto_fixable': True, 'impact': 'high'})

        if not analysis.get('audio_analysis', {}).get('has_audio'):
            fixes.append({'type': 'add_music', 'description': 'Add background music for audio coverage',
                          'auto_fixable': True, 'impact': 'high'})

        return fixes

    def apply_auto_fixes(self, video_path: str, analysis: Dict) -> str:
        """Automatically apply recommended fixes."""
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
                    target_duration = 58
                    speed_factor = clip.duration / target_duration
                    clip = clip.fx(speedx, speed_factor)
                    print(f"[PREDICTOR] ✓ Applied {speed_factor:.2f}x speed adjustment")

                elif fix['type'] == 'pace_optimization' and fix['auto_fixable']:
                    from moviepy.video.fx.all import speedx
                    clip = clip.fx(speedx, 1.1)
                    print("[PREDICTOR] ✓ Applied pacing optimization (1.1x speed)")

            output_path = video_path.replace('.mp4', '_optimized.mp4')
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()

            print(f"[PREDICTOR] ✓ Fixes applied: {output_path}")
            return output_path

        except Exception as e:
            print(f"[PREDICTOR] Error applying fixes: {e}")
            return video_path

    def generate_analysis_report(self, analysis: Dict) -> str:
        """Generate detailed analysis report."""
        score = analysis.get('retention_score', 0)
        score_status = "EXCELLENT ✅" if score >= 70 else ("GOOD ⚠️" if score >= 50 else "NEEDS WORK ❌")

        report = f"""
╔══════════════════════════════════════════════════════════╗
║    🔥 GOD MASTER MODE — RETENTION PREDICTION REPORT      ║
╚══════════════════════════════════════════════════════════╝

Video: {os.path.basename(analysis.get('video_path', 'unknown'))}
Duration: {analysis.get('duration', 0):.1f}s
Resolution: {analysis.get('resolution', [0,0])[0]}x{analysis.get('resolution', [0,0])[1]}

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
            'video_path': '', 'duration': 0, 'retention_score': 0,
            'scene_analysis': {}, 'audio_analysis': {},
            'recommendations': ['Error analyzing video'], 'auto_fixes': [],
        }


# ═══════════════════════════════════════════════════════════
# Quick test/demo
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🔥 GOD MASTER MODE — Retention Predictor Test")

    predictor = RetentionPredictor()

    # Test with script.json if available
    test_path = 'output/test_export/script.json'
    if os.path.exists(test_path):
        prediction = predictor.predict_from_script(test_path)
        print(f"\n✅ Test passed — {prediction['predicted_retention']}% predicted retention")
    else:
        # Fallback: legacy test
        mock_analysis = {
            'video_path': 'test_video.mp4', 'duration': 45,
            'fps': 30, 'resolution': (1920, 1080), 'has_audio': True,
            'scene_analysis': {'duration': 45, 'estimated_scenes': 7,
                              'avg_scene_duration': 6.4, 'pacing_issues': []},
            'audio_analysis': {'has_audio': True, 'duration': 45, 'issues': []},
            'retention_score': 75,
            'recommendations': ["✅ EXCELLENT: Video is optimized for viral performance!"],
            'auto_fixes': [],
        }
        report = predictor.generate_analysis_report(mock_analysis)
        print(report)
        print("\n✓ Retention Predictor ready!")
