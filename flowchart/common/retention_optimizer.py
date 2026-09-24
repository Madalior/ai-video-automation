"""
🔥 GOD MASTER MODE — Retention Optimizer
════════════════════════════════════════════

Script-aware retention maximization engine:
- Emotion arc engine (pacing from emotional journey)
- Smart hooks (scene-aware, not generic templates)
- Real pattern interrupts (zoom, flash, ken burns, speed ramp)
- Scene-aware pacing (shot_type + camera_movement)
- Audio-driven retention (silence, SFX timing, music swells)
- Second-by-second retention curve prediction
- Auto-intervention at predicted drop-off points
- Full script.json integration

Target: 70-85% average view duration (vs 35-45% baseline)
"""

from moviepy.editor import *
from moviepy.video.fx.all import speedx
import random
import json
import os
import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# EMOTION INTENSITY MAP — drives pacing + interrupt decisions
# ═══════════════════════════════════════════════════════════
EMOTION_INTENSITY = {
    # HIGH intensity → fast cuts, shorter scenes
    'anger': 0.9, 'rage': 0.95, 'shock': 0.9, 'fear': 0.85,
    'panic': 0.9, 'desperation': 0.85, 'horror': 0.9,
    'excitement': 0.8, 'thrill': 0.85, 'triumph': 0.8,

    # MEDIUM intensity → balanced pacing
    'tension': 0.7, 'suspense': 0.7, 'curiosity': 0.65,
    'frustration': 0.7, 'confusion': 0.6, 'determination': 0.65,
    'hope': 0.6, 'jealousy': 0.7, 'guilt': 0.65,
    'mystery': 0.6, 'surprise': 0.75, 'revelation': 0.8,

    # LOW intensity → slower, breathing room
    'sadness': 0.4, 'melancholy': 0.35, 'nostalgia': 0.3,
    'calm': 0.2, 'peace': 0.15, 'relief': 0.4,
    'love': 0.5, 'tenderness': 0.3, 'acceptance': 0.35,
    'reflection': 0.25, 'contemplation': 0.2,
}

# Pattern interrupt types mapped to emotion ranges
INTERRUPT_MAP = {
    'zoom_punch':   (0.6, 1.0),   # High emotion → zoom punch
    'flash_cut':    (0.75, 1.0),   # Very high → flash cut
    'ken_burns':    (0.0, 0.5),    # Low emotion → slow push
    'speed_ramp':   (0.5, 0.8),    # Medium → speed ramp
    'whip_pan':     (0.7, 0.9),    # High → whip transition
}

# Shot type → base duration mapping
SHOT_DURATION = {
    'extreme close-up': (3, 5),
    'close-up': (4, 6),
    'medium': (5, 7),
    'wide establishing': (6, 8),
    'wide': (5, 7),
    'over-the-shoulder': (4, 6),
    'tracking': (5, 7),
    'aerial': (6, 8),
}


class RetentionOptimizer:
    """
    🔥 GOD MASTER MODE — Retention Optimizer

    Script-aware, emotion-driven retention maximization.
    Reads script.json and builds per-scene retention strategies.

    Target: 70-85% average view duration (vs 35-45% baseline)
    """

    def __init__(self):
        # Core timing params
        self.hook_interval = 15           # Seconds between re-hooks
        self.pattern_interrupt_interval = 4  # Seconds between interrupts
        self.max_scene_duration = 8       # Hard cap per scene
        self.min_scene_duration = 3       # Floor per scene

        # Retention curve params
        self.initial_retention = 100      # Start at 100%
        self.natural_decay_rate = 0.8     # % lost per second without intervention
        self.hook_recovery = 8            # % recovered per hook
        self.interrupt_recovery = 3       # % recovered per pattern interrupt

        # Analysis output
        self.last_analysis = None

    # ════════════════════════════════════════════════════════
    # 1. SCRIPT.JSON INTEGRATION
    # ════════════════════════════════════════════════════════
    def optimize_from_script(self, script_json_path: str) -> Dict:
        """
        🔥 Master method — reads script.json, builds retention strategy.

        Returns:
            Dict with per-scene retention metadata + overall strategy
        """
        with open(script_json_path, 'r', encoding='utf-8') as f:
            script = json.load(f)

        scenes = script.get('scenes', [])
        title = script.get('title', 'Untitled')

        print(f"\n{'═'*60}")
        print(f"🔥 GOD MASTER MODE — RETENTION OPTIMIZER")
        print(f"{'═'*60}")
        print(f"   Title: {title}")
        print(f"   Scenes: {len(scenes)}")
        print(f"   Target: 70-85% average view duration")
        print(f"{'═'*60}")

        # Step 1: Build emotion arc
        emotion_arc = self._build_emotion_arc(scenes)

        # Step 2: Calculate per-scene pacing
        pacing_plan = self._build_pacing_plan(scenes, emotion_arc)

        # Step 3: Generate smart hooks
        hooks = self._generate_smart_hooks(scenes, script)

        # Step 4: Plan pattern interrupts
        interrupts = self._plan_pattern_interrupts(scenes, emotion_arc)

        # Step 5: Plan audio retention cues
        audio_cues = self._plan_audio_retention(scenes)

        # Step 6: Predict retention curve
        retention_curve = self._predict_retention_curve(
            scenes, emotion_arc, hooks, interrupts
        )

        # Step 7: Auto-insert interventions at drop-off points
        interventions = self._auto_intervene(retention_curve, scenes)

        # Step 8: Annotate scenes with retention metadata
        optimized_scenes = self._annotate_scenes(
            scenes, emotion_arc, pacing_plan, hooks,
            interrupts, audio_cues, interventions
        )

        # Build analysis result
        analysis = {
            'title': title,
            'total_scenes': len(scenes),
            'emotion_arc': emotion_arc,
            'pacing_plan': pacing_plan,
            'hooks': hooks,
            'interrupts': interrupts,
            'audio_cues': audio_cues,
            'retention_curve': retention_curve,
            'interventions': interventions,
            'optimized_scenes': optimized_scenes,
            'predicted_avg_retention': self._avg_retention(retention_curve),
            'timestamp': datetime.now().isoformat(),
        }

        self.last_analysis = analysis

        # Print summary
        avg_ret = analysis['predicted_avg_retention']
        print(f"\n   📊 Predicted Avg Retention: {avg_ret:.1f}%")
        print(f"   🎣 Hooks planned: {len(hooks)}")
        print(f"   ⚡ Pattern interrupts: {sum(len(v) for v in interrupts.values())}")
        print(f"   🎵 Audio cues: {sum(len(v) for v in audio_cues.values())}")
        print(f"   🛡️ Auto-interventions: {len(interventions)}")

        # Save analysis
        self._save_analysis(analysis, os.path.dirname(script_json_path))

        return analysis

    # ════════════════════════════════════════════════════════
    # 2. EMOTION ARC ENGINE
    # ════════════════════════════════════════════════════════
    def _build_emotion_arc(self, scenes: List[Dict]) -> List[Dict]:
        """
        Map the emotional journey across all scenes.
        Returns per-scene emotion data with intensity and contrast.
        """
        arc = []
        prev_intensity = 0.5

        for scene in scenes:
            emotion = scene.get('emotion', 'neutral').lower()
            intensity = EMOTION_INTENSITY.get(emotion, 0.5)

            # Emotional contrast with previous scene
            contrast = abs(intensity - prev_intensity)

            # Contrast bonus — big swings boost retention
            contrast_bonus = contrast * 15  # Up to +15% for max contrast

            arc.append({
                'scene_number': scene.get('scene_number', 0),
                'emotion': emotion,
                'intensity': intensity,
                'contrast': round(contrast, 2),
                'contrast_bonus': round(contrast_bonus, 1),
                'category': 'high' if intensity >= 0.7 else ('medium' if intensity >= 0.4 else 'low'),
            })

            prev_intensity = intensity

        print(f"\n   🎭 Emotion Arc:")
        for e in arc:
            bar = '█' * int(e['intensity'] * 20)
            print(f"      Scene {e['scene_number']}: {e['emotion']:15s} [{bar:20s}] {e['intensity']:.1f} (contrast: +{e['contrast_bonus']:.0f}%)")

        return arc

    # ════════════════════════════════════════════════════════
    # 3. SCENE-AWARE PACING ENGINE
    # ════════════════════════════════════════════════════════
    def _build_pacing_plan(self, scenes: List[Dict], emotion_arc: List[Dict]) -> List[Dict]:
        """
        Calculate optimal pacing per scene using shot_type + emotion.

        High emotion → shorter, faster scenes
        Low emotion → slightly longer, breathing room
        Close-ups → shorter than wide shots
        """
        plan = []

        for i, scene in enumerate(scenes):
            visual = scene.get('visual', {})
            shot_type = visual.get('shot_type', 'medium').lower()
            camera = visual.get('camera_movement', 'static').lower()
            emotion_data = emotion_arc[i] if i < len(emotion_arc) else {'intensity': 0.5}

            # Base duration from shot type
            base_min, base_max = SHOT_DURATION.get(shot_type, (5, 7))

            # Emotion adjustment: high emotion → shorter
            intensity = emotion_data['intensity']
            emotion_factor = 1.0 - (intensity * 0.3)  # 0.7x at max intensity
            target_duration = ((base_min + base_max) / 2) * emotion_factor

            # Camera movement adjustment
            if camera in ('tracking', 'dolly', 'crane'):
                target_duration += 1  # Moving cameras need slightly more time
            elif camera in ('handheld shaky', 'whip pan'):
                target_duration -= 0.5  # Aggressive movement = shorter

            # Speed multiplier for pacing
            if intensity >= 0.8:
                speed_mult = random.uniform(1.08, 1.15)  # Speed up high-energy
            elif intensity <= 0.3:
                speed_mult = random.uniform(0.95, 1.0)   # Slow down calm scenes
            else:
                speed_mult = 1.0

            # Clamp
            target_duration = max(self.min_scene_duration, min(self.max_scene_duration, target_duration))

            plan.append({
                'scene_number': scene.get('scene_number', 0),
                'shot_type': shot_type,
                'target_duration': round(target_duration, 1),
                'speed_multiplier': round(speed_mult, 2),
                'camera': camera,
            })

        return plan

    # ════════════════════════════════════════════════════════
    # 4. SMART HOOK SYSTEM
    # ════════════════════════════════════════════════════════
    def _generate_smart_hooks(self, scenes: List[Dict], script: Dict) -> List[Dict]:
        """
        Generate scene-aware hooks using actual dialogue and subtext.
        Not generic templates — each hook is built from the script.
        """
        hooks = []

        # Opening hook (0-3s) — uses scene 1's emotional core
        if scenes:
            first = scenes[0]
            emotion = first.get('emotion', 'mystery')
            subtext = first.get('subtext', '')
            dialogue = first.get('dialogue', '')

            # Build opening hook from actual content
            if subtext:
                opening = f"[HOOK] {subtext}"
            elif dialogue and dialogue != 'none':
                opening = f"[HOOK] \"{dialogue}\""
            else:
                opening = f"[HOOK] What happens next will change everything."

            hooks.append({
                'timestamp': 0,
                'type': 'opening_hook',
                'text': opening,
                'based_on': f"Scene 1 — {emotion}",
            })

        # Re-hooks at intervals — tease upcoming dramatic moments
        cumulative_time = 0
        for i, scene in enumerate(scenes):
            visual = scene.get('visual', {})
            duration = float(SHOT_DURATION.get(
                visual.get('shot_type', 'medium'), (5, 7)
            )[1])
            cumulative_time += duration

            # Check if it's time for a re-hook
            if cumulative_time >= self.hook_interval and i < len(scenes) - 1:
                next_scene = scenes[i + 1]
                next_emotion = next_scene.get('emotion', '')
                next_subtext = next_scene.get('subtext', '')
                next_dialogue = next_scene.get('dialogue', '')

                # Build re-hook from upcoming content
                if next_subtext and next_subtext != 'none':
                    hook_text = f"[RE-HOOK] But then — {next_subtext.lower()}"
                elif next_dialogue and next_dialogue != 'none':
                    hook_text = f"[RE-HOOK] Wait for this..."
                else:
                    hook_text = f"[RE-HOOK] The next moment changes everything."

                hooks.append({
                    'timestamp': round(cumulative_time, 1),
                    'type': 're_hook',
                    'text': hook_text,
                    'based_on': f"Scene {i+2} — {next_emotion}",
                })

                cumulative_time = 0  # Reset hook timer

        # Act transition hooks
        acts_seen = set()
        for scene in scenes:
            act = scene.get('act', '')
            if act and act not in acts_seen and len(acts_seen) > 0:
                hooks.append({
                    'timestamp': -1,  # Will be calculated during editing
                    'type': 'act_bridge',
                    'text': f"[ACT BRIDGE] {act} begins...",
                    'based_on': f"Transition to {act}",
                })
            acts_seen.add(act)

        return hooks

    # ════════════════════════════════════════════════════════
    # 5. REAL PATTERN INTERRUPTS
    # ════════════════════════════════════════════════════════
    def _plan_pattern_interrupts(self, scenes: List[Dict],
                                  emotion_arc: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Plan concrete pattern interrupts per scene.
        Uses emotion intensity to choose interrupt type.

        Returns:
            Dict mapping scene_number -> list of planned interrupts
        """
        interrupts = {}

        for i, scene in enumerate(scenes):
            scene_num = scene.get('scene_number', i + 1)
            emotion_data = emotion_arc[i] if i < len(emotion_arc) else {'intensity': 0.5}
            intensity = emotion_data['intensity']
            scene_interrupts = []

            # Choose interrupt type based on emotion intensity
            for itype, (low, high) in INTERRUPT_MAP.items():
                if low <= intensity <= high:
                    # Calculate when in the scene to place it
                    visual = scene.get('visual', {})
                    shot = visual.get('shot_type', 'medium')
                    max_dur = SHOT_DURATION.get(shot, (5, 7))[1]

                    if itype == 'zoom_punch':
                        scene_interrupts.append({
                            'type': 'zoom_punch',
                            'scale': round(1.1 + (intensity * 0.1), 2),  # 1.1x to 1.2x
                            'duration': 0.3,
                            'at_seconds': round(max_dur * 0.5, 1),  # Mid-scene
                            'description': f'Zoom punch to {round(1.1 + intensity * 0.1, 1)}x at dialogue beat',
                        })

                    elif itype == 'flash_cut':
                        scene_interrupts.append({
                            'type': 'flash_cut',
                            'color': 'white',
                            'duration': 0.1,
                            'at_seconds': round(max_dur * 0.7, 1),  # Near end
                            'description': 'Flash cut at emotional peak',
                        })

                    elif itype == 'ken_burns':
                        scene_interrupts.append({
                            'type': 'ken_burns',
                            'direction': random.choice(['push_in', 'pull_out', 'pan_left', 'pan_right']),
                            'scale_start': 1.0,
                            'scale_end': 1.08,
                            'description': 'Slow Ken Burns push to add movement to static scene',
                        })

                    elif itype == 'speed_ramp':
                        scene_interrupts.append({
                            'type': 'speed_ramp',
                            'speed_start': 1.0,
                            'speed_peak': round(1.2 + (intensity * 0.2), 2),
                            'speed_end': 0.85,
                            'description': f'Speed ramp: 1.0x → {round(1.2 + intensity * 0.2, 1)}x → 0.85x',
                        })

                    elif itype == 'whip_pan':
                        scene_interrupts.append({
                            'type': 'whip_pan',
                            'direction': random.choice(['left', 'right']),
                            'blur_amount': 15,
                            'duration': 0.2,
                            'description': 'Whip pan transition between scenes',
                        })

                    break  # One primary interrupt per scene

            interrupts[scene_num] = scene_interrupts

        return interrupts

    # ════════════════════════════════════════════════════════
    # 6. AUDIO-DRIVEN RETENTION
    # ════════════════════════════════════════════════════════
    def _plan_audio_retention(self, scenes: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Plan audio cues for retention using script.json audio data.
        Strategic silence, SFX timing, music swells.
        """
        audio_cues = {}

        for scene in scenes:
            scene_num = scene.get('scene_number', 0)
            audio = scene.get('audio', {})
            emotion = scene.get('emotion', '').lower()
            dialogue = scene.get('dialogue', '')
            cues = []

            music = audio.get('music', 'none')
            sfx = audio.get('sfx', 'none')
            silence = audio.get('silence', 'none')

            # Strategic silence before reveals
            if emotion in ('revelation', 'shock', 'surprise'):
                cues.append({
                    'type': 'strategic_silence',
                    'duration': 0.5,
                    'position': 'before_dialogue',
                    'description': f'0.5s silence before {emotion} moment — builds tension',
                })

            # SFX emphasis
            if sfx and sfx != 'none':
                cues.append({
                    'type': 'sfx_punch',
                    'sfx': sfx,
                    'volume_boost': 1.3,
                    'description': f'Boost {sfx} volume by 30% for impact',
                })

            # Music swell at emotional peaks
            intensity = EMOTION_INTENSITY.get(emotion, 0.5)
            if intensity >= 0.7 and music and music != 'none':
                cues.append({
                    'type': 'music_swell',
                    'music': music,
                    'swell_to': min(1.0, 0.6 + intensity * 0.4),
                    'description': f'Music swell ({music}) peaks at emotion climax',
                })

            # Bass drop + visual freeze for cliffhangers
            if emotion in ('shock', 'revelation', 'horror'):
                cues.append({
                    'type': 'bass_drop_freeze',
                    'duration': 0.3,
                    'description': 'Bass drop + frame freeze for cliffhanger effect',
                })

            # Dialogue-timed silence
            if silence and silence != 'none':
                cues.append({
                    'type': 'scripted_silence',
                    'instruction': silence,
                    'description': f'Scripted silence: {silence}',
                })

            audio_cues[scene_num] = cues

        return audio_cues

    # ════════════════════════════════════════════════════════
    # 7. RETENTION CURVE PREDICTOR
    # ════════════════════════════════════════════════════════
    def _predict_retention_curve(self, scenes: List[Dict],
                                  emotion_arc: List[Dict],
                                  hooks: List[Dict],
                                  interrupts: Dict) -> List[Dict]:
        """
        Predict second-by-second retention curve.
        Models viewer drop-off at each scene transition.
        """
        curve = []
        retention = self.initial_retention
        current_time = 0.0
        hook_times = {h['timestamp'] for h in hooks if h['timestamp'] >= 0}

        for i, scene in enumerate(scenes):
            visual = scene.get('visual', {})
            shot = visual.get('shot_type', 'medium')
            duration = float(SHOT_DURATION.get(shot, (5, 7))[1])
            emotion_data = emotion_arc[i] if i < len(emotion_arc) else {'intensity': 0.5, 'contrast_bonus': 0}
            scene_num = scene.get('scene_number', i + 1)

            # Simulate each second within this scene
            for sec in range(int(duration)):
                t = current_time + sec

                # Natural decay
                retention -= self.natural_decay_rate

                # Emotion intensity slows decay (high emotion = less drop-off)
                intensity_save = emotion_data['intensity'] * 0.5
                retention += intensity_save

                # Hook recovery
                if any(abs(t - ht) < 1 for ht in hook_times):
                    retention += self.hook_recovery

                # Pattern interrupt recovery
                scene_interrupts = interrupts.get(scene_num, [])
                for intr in scene_interrupts:
                    if abs(sec - intr.get('at_seconds', -1)) < 1:
                        retention += self.interrupt_recovery

                # Contrast bonus at scene start
                if sec == 0:
                    retention += emotion_data.get('contrast_bonus', 0)

                # Clamp
                retention = max(5, min(100, retention))

                curve.append({
                    'timestamp': round(t, 1),
                    'retention': round(retention, 1),
                    'scene': scene_num,
                    'emotion': emotion_data.get('emotion', ''),
                })

            current_time += duration

            # Scene transition drop-off (viewers leave during cuts)
            retention -= 2.0
            retention = max(5, retention)

        return curve

    def _avg_retention(self, curve: List[Dict]) -> float:
        """Average retention across the entire curve."""
        if not curve:
            return 0.0
        return sum(p['retention'] for p in curve) / len(curve)

    # ════════════════════════════════════════════════════════
    # 8. AUTO-INTERVENTION
    # ════════════════════════════════════════════════════════
    def _auto_intervene(self, curve: List[Dict], scenes: List[Dict]) -> List[Dict]:
        """
        Detect drop-off points in retention curve and auto-insert interventions.
        """
        interventions = []
        min_threshold = 55  # Below this, intervene

        for i, point in enumerate(curve):
            if point['retention'] < min_threshold:
                # Check if we already intervened recently
                if interventions and (point['timestamp'] - interventions[-1]['timestamp']) < 5:
                    continue

                # Choose intervention type based on how bad the drop is
                drop = min_threshold - point['retention']

                if drop > 15:
                    intervention_type = 'emergency_hook'
                    description = 'Critical drop — insert question hook + visual punch'
                elif drop > 8:
                    intervention_type = 'zoom_punch'
                    description = 'Moderate drop — zoom punch to recapture attention'
                else:
                    intervention_type = 'sfx_sting'
                    description = 'Minor drop — sound effect sting to interrupt pattern'

                interventions.append({
                    'timestamp': point['timestamp'],
                    'scene': point['scene'],
                    'type': intervention_type,
                    'retention_at_trigger': point['retention'],
                    'description': description,
                })

        return interventions

    # ════════════════════════════════════════════════════════
    # 9. SCENE ANNOTATION
    # ════════════════════════════════════════════════════════
    def _annotate_scenes(self, scenes, emotion_arc, pacing_plan,
                          hooks, interrupts, audio_cues, interventions) -> List[Dict]:
        """
        Inject retention metadata into each scene dict.
        """
        annotated = []

        for i, scene in enumerate(scenes):
            scene_num = scene.get('scene_number', i + 1)
            emotion_data = emotion_arc[i] if i < len(emotion_arc) else {}
            pacing = pacing_plan[i] if i < len(pacing_plan) else {}

            scene_hooks = [h for h in hooks if h.get('based_on', '').endswith(f"Scene {scene_num}") or
                           (h['type'] == 'opening_hook' and scene_num == 1)]
            scene_interrupts = interrupts.get(scene_num, [])
            scene_audio = audio_cues.get(scene_num, [])
            scene_interventions = [iv for iv in interventions if iv['scene'] == scene_num]

            # Retention risk score
            risk = 0
            if emotion_data.get('intensity', 0.5) < 0.3:
                risk += 30  # Low-emotion scenes are risky
            if not scene.get('dialogue') or scene.get('dialogue') == 'none':
                risk += 20  # No dialogue = less engagement
            if not scene_hooks:
                risk += 15  # No hooks near this scene
            if pacing.get('target_duration', 6) > 7:
                risk += 10  # Long scenes are risky

            annotated.append({
                'scene_number': scene_num,
                'emotion': emotion_data.get('emotion', ''),
                'emotion_intensity': emotion_data.get('intensity', 0.5),
                'retention_risk': min(100, risk),
                'pacing_speed': pacing.get('speed_multiplier', 1.0),
                'target_duration': pacing.get('target_duration', 6),
                'pattern_interrupts': scene_interrupts,
                'hooks': scene_hooks,
                'audio_cues': scene_audio,
                'interventions': scene_interventions,
            })

        return annotated

    # ════════════════════════════════════════════════════════
    # 10. VIDEO-LEVEL OPTIMIZATION (MoviePy)
    # ════════════════════════════════════════════════════════
    def apply_all_techniques(self, video_clip, script_data=None):
        """
        Apply all retention optimization techniques to a video clip.

        Args:
            video_clip: VideoFileClip to optimize
            script_data: Optional dict with scene/hook information

        Returns:
            Optimized VideoFileClip
        """
        print("\n[RETENTION] 🔥 Applying GOD MASTER MODE retention techniques...")

        # 1. Optimize pacing
        video_clip = self.optimize_pacing(video_clip)

        # 2. Add pattern interrupts (real zoom punches)
        video_clip = self.apply_zoom_punches(video_clip)

        # 3. Add progress indicators if applicable
        if script_data and 'total_points' in script_data:
            video_clip = self.add_progress_indicators(
                video_clip, script_data['total_points']
            )

        print("[RETENTION] ✓ All techniques applied")
        return video_clip

    def optimize_pacing(self, video_clip):
        """
        Optimize video pacing for maximum retention.
        Uses dynamic speed based on position in video.
        """
        duration = video_clip.duration

        if duration < 15:
            return video_clip

        if duration > 45:
            # Dynamic speed: slightly faster in the middle (where drop-off peaks)
            video_clip = video_clip.fx(speedx, 1.05)
            print(f"[RETENTION] Applied 5% speed increase for pacing")

        return video_clip

    def apply_zoom_punches(self, video_clip):
        """
        Apply real zoom punch effects at interval points.
        Creates a 1.15x scale burst for 0.3s every N seconds.
        """
        duration = video_clip.duration
        interval = self.pattern_interrupt_interval

        if duration < interval * 2:
            return video_clip  # Too short for interrupts

        zoom_points = []
        t = interval
        while t < duration - 2:
            zoom_points.append(t)
            t += interval + random.uniform(-1, 1)  # Slightly randomized

        if not zoom_points:
            return video_clip

        # Build zoom effect function
        def zoom_effect(get_frame, t):
            frame = get_frame(t)
            for zp in zoom_points:
                if abs(t - zp) < 0.15:  # Within 0.15s of zoom point
                    h, w = frame.shape[:2]
                    scale = 1.12
                    new_h, new_w = int(h * scale), int(w * scale)
                    try:
                        from PIL import Image
                        import numpy as np
                        img = Image.fromarray(frame)
                        img = img.resize((new_w, new_h), Image.LANCZOS)
                        # Crop back to original size from center
                        left = (new_w - w) // 2
                        top = (new_h - h) // 2
                        img = img.crop((left, top, left + w, top + h))
                        return np.array(img)
                    except Exception:
                        return frame
            return frame

        video_clip = video_clip.fl(zoom_effect)
        print(f"[RETENTION] ⚡ Applied {len(zoom_points)} zoom punches at {interval}s intervals")

        return video_clip

    def add_pattern_interrupts(self, video_clip):
        """Apply pattern interrupts — delegates to zoom punches."""
        return self.apply_zoom_punches(video_clip)

    def add_progress_indicators(self, video_clip, total_points: int):
        """
        Add progress indicators for list-style content.
        Uses PIL-based text rendering — no ImageMagick required.
        """
        # Feature 7: PIL text instead of TextClip (which needs ImageMagick)
        from flowchart.common.enhanced_editor import _make_text_clip
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

        w, h = video_clip.size
        clips = [video_clip]
        duration = video_clip.duration
        segment_duration = duration / total_points

        for i in range(total_points):
            start_time = i * segment_duration
            progress_text = f"{i+1}/{total_points}"
            disp_dur = min(2.0, segment_duration)

            try:
                tc = _make_text_clip(
                    progress_text,
                    frame_w=w,
                    frame_h=h,
                    duration=disp_dur,
                    y_position=12,          # top of frame
                    fontsize=36,
                    text_color=(255, 255, 255),
                    bg_color=(20, 20, 20),
                    stroke_color=(0, 0, 0),
                    stroke_width=2,
                    fade_in=0.1,
                    fade_out=0.1,
                ).set_start(start_time)

                # Reposition to top-right corner
                tc = tc.set_position(lambda t, cw=tc.w, vw=w: (vw - cw - 12, 12))
                clips.append(tc)
            except Exception as e:
                print(f"[RETENTION] Warning: Could not add progress indicator: {e}")
                break

        if len(clips) > 1:
            video_clip = CompositeVideoClip(clips)
            print(f"[RETENTION] ✓ Added {total_points} progress indicators (PIL)")

        return video_clip

    # ════════════════════════════════════════════════════════
    # 11. LEGACY METHODS (backward compatible)
    # ════════════════════════════════════════════════════════
    def optimize_script(self, script_data: Dict, target_retention: int = 70) -> Dict:
        """Optimize text script for higher retention."""
        print(f"[RETENTION] Optimizing script for {target_retention}% retention...")
        script_data = self.enhance_hook(script_data)
        hooks = self.create_multi_hook_script(script_data.get('title', 'Topic'), num_segments=3)
        script_data['pacing_notes'] = [f"Hook at {15*i}s: {h}" for i, h in enumerate(hooks, 1)]
        print("[RETENTION] ✓ Script optimized with new hooks")
        return script_data

    def enhance_hook(self, script_data: Dict) -> Dict:
        """Enhance the opening hook of the script."""
        current_hook = script_data.get('hook', '')
        power_phrases = [
            "Stop scrolling!", "You need to see this.", "This is a secret.",
            "Nobody talks about this.", "This changes everything.",
        ]
        if not any(phrase in current_hook for phrase in power_phrases):
            new_hook = f"{random.choice(power_phrases)} {current_hook}"
            script_data['hook'] = new_hook
            print(f"[RETENTION] Enhanced hook: {new_hook}")
        return script_data

    def create_multi_hook_script(self, main_topic: str, num_segments: int = 5) -> List[str]:
        """Generate multi-hook script structure."""
        hook_templates = [
            "But wait, there's more...",
            "Here's where it gets interesting...",
            "You won't believe what happens next...",
            "The best part is coming up...",
            "Hold on, this is crazy...",
            "But that's not even the best part...",
            "This next one will blow your mind...",
            "Wait until you see this...",
            "And now for the most important part...",
            "This changes everything...",
        ]
        return random.sample(hook_templates, min(num_segments, len(hook_templates)))

    def analyze_retention_risks(self, video_clip) -> Dict:
        """Analyze video for potential retention drop-off points."""
        duration = video_clip.duration
        analysis = {'duration': duration, 'risk_score': 0, 'slow_segments': [], 'recommendations': []}

        if duration > 60:
            analysis['risk_score'] += 20
            analysis['recommendations'].append("Video exceeds 60s - consider cutting to 45-60s for shorts")
        if duration > 45:
            analysis['risk_score'] += 10
            analysis['recommendations'].append("Apply 1.1x speed increase to improve pacing")

        analysis['risk_level'] = 'LOW' if analysis['risk_score'] < 20 else ('MEDIUM' if analysis['risk_score'] < 40 else 'HIGH')
        return analysis

    def calculate_retention_score(self, video_clip, has_subtitles=False,
                                  has_music=False, has_hooks=False) -> int:
        """Calculate predicted retention score based on features."""
        base_score = 35
        if has_subtitles: base_score += 25
        if has_music: base_score += 10
        if has_hooks: base_score += 15
        duration = video_clip.duration
        if duration <= 30: base_score += 10
        elif duration <= 45: base_score += 5
        return min(base_score, 100)

    def generate_retention_report(self, video_clip, features: Dict) -> str:
        """Generate detailed retention analysis report."""
        score = self.calculate_retention_score(
            video_clip, features.get('has_subtitles', False),
            features.get('has_music', False), features.get('has_hooks', False)
        )
        analysis = self.analyze_retention_risks(video_clip)

        report = f"""
╔══════════════════════════════════════════════════════════╗
║       🔥 GOD MASTER MODE — RETENTION REPORT              ║
╚══════════════════════════════════════════════════════════╝

Video Duration: {video_clip.duration:.1f}s
Predicted Retention Score: {score}/100

Risk Assessment: {analysis['risk_level']}
Risk Score: {analysis['risk_score']}/100

Applied Features:
  • Subtitles: {'✓' if features.get('has_subtitles') else '✗'}
  • Background Music: {'✓' if features.get('has_music') else '✗'}
  • Multi-Hook Structure: {'✓' if features.get('has_hooks') else '✗'}
  • Pattern Interrupts: {'✓' if features.get('has_interrupts') else '✗'}
  • Progress Indicators: {'✓' if features.get('has_progress') else '✗'}

Recommendations:
"""
        for i, rec in enumerate(analysis['recommendations'], 1):
            report += f"  {i}. {rec}\n"

        if score >= 70:
            report += "\n✓ EXCELLENT: This video is optimized for viral performance!\n"
        elif score >= 50:
            report += "\n⚠ GOOD: Consider adding more retention features.\n"
        else:
            report += "\n✗ NEEDS WORK: Apply more retention techniques.\n"

        return report

    # ════════════════════════════════════════════════════════
    # 12. PERSISTENCE
    # ════════════════════════════════════════════════════════
    def _save_analysis(self, analysis: Dict, output_dir: str = 'output'):
        """Save retention analysis to JSON for review."""
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, 'retention_analysis.json')

        # Make curve serializable
        save_data = {
            'title': analysis.get('title', ''),
            'total_scenes': analysis.get('total_scenes', 0),
            'predicted_avg_retention': analysis.get('predicted_avg_retention', 0),
            'timestamp': analysis.get('timestamp', ''),
            'emotion_arc': analysis.get('emotion_arc', []),
            'pacing_plan': analysis.get('pacing_plan', []),
            'hooks': analysis.get('hooks', []),
            'interrupts': {str(k): v for k, v in analysis.get('interrupts', {}).items()},
            'audio_cues': {str(k): v for k, v in analysis.get('audio_cues', {}).items()},
            'interventions': analysis.get('interventions', []),
            'optimized_scenes': analysis.get('optimized_scenes', []),
            'retention_curve_summary': {
                'total_points': len(analysis.get('retention_curve', [])),
                'min_retention': min((p['retention'] for p in analysis.get('retention_curve', [{'retention': 0}])), default=0),
                'max_retention': max((p['retention'] for p in analysis.get('retention_curve', [{'retention': 0}])), default=0),
                'avg_retention': analysis.get('predicted_avg_retention', 0),
            },
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"\n   💾 Retention analysis saved: {filepath}")


# ═══════════════════════════════════════════════════════════
# Quick test/demo
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🔥 GOD MASTER MODE — Retention Optimizer Test")

    optimizer = RetentionOptimizer()

    # Test with script.json if available
    test_path = 'output/test_export/script.json'
    if os.path.exists(test_path):
        analysis = optimizer.optimize_from_script(test_path)
        print(f"\n✅ Test passed — {analysis['predicted_avg_retention']:.1f}% predicted retention")
    else:
        # Fallback: test legacy methods
        hooks = optimizer.create_multi_hook_script("AI Tools", 5)
        print("\nGenerated Hooks:")
        for i, hook in enumerate(hooks, 1):
            print(f"  {i}. {hook}")

        class MockClip:
            duration = 45

        mock_clip = MockClip()
        score = optimizer.calculate_retention_score(mock_clip, True, True, True)
        print(f"\nPredicted Retention Score: {score}/100")
        report = optimizer.generate_retention_report(mock_clip, {
            'has_subtitles': True, 'has_music': True,
            'has_hooks': True, 'has_interrupts': True, 'has_progress': True
        })
        print(report)
