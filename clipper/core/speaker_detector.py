"""
Speaker Detector
================
Uses pyannote.audio (Speaker Diarization) to determine "Who spoke when?".

Outputs a timeline of speaker turns, which is fed into the SmartReframer
to decide which face to focus on (or when to split screen).
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

class SpeakerDetector:
    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        self.pipeline = None
        
        if not self.hf_token:
            print("[SPEAKER] ⚠️  Warning: HUGGINGFACE_TOKEN not found in .env")
            print("[SPEAKER] Get a free token at https://huggingface.co/settings/tokens")
            print("[SPEAKER] Ensure you accepted terms for pyannote/speaker-diarization-3.1")
            
    def _load_model(self):
        if self.pipeline is not None:
            return
            
        if not self.hf_token:
            raise ValueError("HUGGINGFACE_TOKEN is required for speaker diarization.")
            
        print("[SPEAKER] Loading pyannote.audio 3.1 model...")
        try:
            import torch
            from pyannote.audio import Pipeline
            
            # Use GPU if available, else CPU
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=self.hf_token
            )
            self.pipeline.to(device)
            print(f"[SPEAKER] Model loaded successfully on {device}")
            
        except ImportError:
            print("[SPEAKER] Error: pyannote.audio not installed. Run: pip install pyannote.audio")
            raise
        except Exception as e:
            print(f"[SPEAKER] Failed to load model: {e}")
            raise

    def detect(self, audio_path: str, output_json: str) -> list:
        """
        Analyze audio and return speaker timeline.
        
        Returns:
            list of dicts: [{"start": 0.0, "end": 2.5, "speaker": "SPEAKER_00"}, ...]
        """
        print(f"[SPEAKER] Analyzing audio for speakers: {audio_path}")
        self._load_model()
        # Load audio manually to bypass broken torchcodec on Windows
        import soundfile as sf
        import torch
        temp_wav = None
        try:
            audio_data, sample_rate = sf.read(audio_path)
        except Exception as read_err:
            import subprocess
            temp_wav = audio_path + ".diarize.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-i", audio_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", temp_wav],
                capture_output=True
            )
            if os.path.exists(temp_wav):
                audio_data, sample_rate = sf.read(temp_wav)
            else:
                raise read_err
        finally:
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

        if len(audio_data.shape) == 1:
            audio_data = audio_data.reshape(-1, 1)
        waveform = torch.from_numpy(audio_data).float().t()
        audio_in_memory = {"waveform": waveform, "sample_rate": sample_rate}
        
        # Run diarization (can take a minute depending on clip length and hardware)
        diarization = self.pipeline(audio_in_memory)
        
        # Pyannote 3.1+ sometimes returns a DiarizeOutput dataclass instead of pure Annotation
        if hasattr(diarization, 'speaker_diarization'):
            diarization = diarization.speaker_diarization
            
        speaker_turns = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_turns.append({
                "start": round(turn.start, 2),
                "end": round(turn.end, 2),
                "speaker": speaker
            })
            
        # Clean up very short segments or merge adjacent segments from the same speaker
        merged_turns = self._merge_adjacent_turns(speaker_turns)
        
        # Save to JSON for the SmartReframer
        with open(output_json, 'w') as f:
            json.dump({"speaker_turns": merged_turns}, f, indent=2)
            
        print(f"[SPEAKER] Found {len(merged_turns)} speaker turns. Saved to {output_json}")
        return merged_turns
        
    def _merge_adjacent_turns(self, turns: list, gap_threshold: float = 0.5) -> list:
        """Merge adjacent turns from the same speaker if the gap is small."""
        if not turns:
            return []
            
        merged = [turns[0]]
        
        for turn in turns[1:]:
            last_turn = merged[-1]
            
            if turn["speaker"] == last_turn["speaker"] and (turn["start"] - last_turn["end"]) <= gap_threshold:
                # Merge
                last_turn["end"] = max(last_turn["end"], turn["end"])
            else:
                merged.append(turn)
                
        return merged

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        detector = SpeakerDetector()
        detector.detect(sys.argv[1], "speakers.json")
