/**
 * Captik Video Caption Engine
 * Built-in Templates:
 *  1) "delhi" — Minimalist editorial elegance (Instrument Sans + glowing italic Instrument Serif keywords, karaoke flow)
 *  2) "editor_masala" — Dynamic 3-tier kinetic sandwich (Montserrat context lines + massive center Hero word in Persona A/B)
 *  3) "gum_gum" — High-energy Deep Glow + Drop Shadow 2-line AE style
 */

import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  Video,
  staticFile,
  interpolate,
  spring,
  CalculateMetadataFunction,
} from "remotion";
import { z } from "zod";

// ─── Types & Controls Schema ──────────────────────────────────────────────────

export const transcriptSchema = z.array(
  z.object({
    text: z.string(),
    start: z.number(),
    end: z.number(),
  })
);

export const captionsSchema = z.object({
  template: z.enum(["delhi", "editor_masala", "gum_gum"]).default("editor_masala"),
  personaMode: z.enum(["auto", "A", "B"]).default("auto"),
  videoPath: z.string().optional(),
  transparentOverlay: z.boolean().default(false),
  durationInFrames: z.number().optional(),
  fps: z.number().optional(),
  transcript: transcriptSchema,
  trackingData: z.array(z.object({ f: z.number(), x: z.number() })).optional(),

  // Visual Customizations
  textColor: z.string().default("#FFFFFF"),
  line1Color: z.string().default("#CCCCCC"),
  line2Color: z.string().default("#FFFFFF"),
  keywordColor: z.string().default("#00FF66"),
  heroColor: z.string().default("#FFD700"),
  glowIntensity: z.number().min(0).max(5).step(0.1).default(1.0),
  shadowIntensity: z.number().min(0).max(3).step(0.1).default(1.0),
  fontSize: z.number().min(20).max(200).default(42),
  line1FontSize: z.number().min(20).max(200).default(34),
  line2FontSize: z.number().min(20).max(250).default(40),
  keywordFontSize: z.number().min(20).max(300).default(42),
  letterSpacing: z.number().min(0).max(20).step(0.5).default(2),
  popScaleAmount: z.number().min(1).max(2).step(0.05).default(1.08),
  lineGap: z.number().min(0).max(40).step(1).default(2),
  captionYPercent: z.number().min(10).max(95).default(54),
  keywords: z.array(z.string()).default([]),
  overlayText: z.string().optional(),
});

export type CaptionsProps = z.infer<typeof captionsSchema>;
export type WordInfo = CaptionsProps["transcript"][0];

export const defaultProps: CaptionsProps = {
  template: "editor_masala",
  personaMode: "auto",
  videoPath: "meta_preview_clip.mp4",
  transparentOverlay: false,
  textColor: "#FFFFFF",
  line1Color: "#CCCCCC",
  line2Color: "#FFFFFF",
  keywordColor: "#00FF66",
  heroColor: "#FFD700",
  glowIntensity: 1.0,
  shadowIntensity: 1.0,
  fontSize: 42,
  line1FontSize: 34,
  line2FontSize: 40,
  keywordFontSize: 42,
  letterSpacing: 2,
  popScaleAmount: 1.08,
  lineGap: 2,
  captionYPercent: 54,
  keywords: ["META", "FUTURE"],
  transcript: [
    { text: "THE", start: 0.2, end: 0.4 },
    { text: "TEAM", start: 0.4, end: 0.6 },
    { text: "AT", start: 0.6, end: 0.8 },
    { text: "META", start: 0.8, end: 1.1 },
    { text: "ARE", start: 1.1, end: 1.3 },
    { text: "IMAGINING", start: 1.3, end: 1.8 },
    { text: "A", start: 1.8, end: 2.0 },
    { text: "FUTURE", start: 2.0, end: 2.8 },
  ],
  trackingData: [],
};

export const calculateMetadata: CalculateMetadataFunction<CaptionsProps> = ({
  props,
}) => {
  const fps = props.fps ? Math.round(props.fps) : 30;
  let durationInFrames = props.durationInFrames ?? 300;
  if (!props.durationInFrames) {
    if (props.transcript && props.transcript.length > 0) {
      const lastEnd = props.transcript[props.transcript.length - 1].end;
      durationInFrames = Math.max(durationInFrames, Math.ceil(lastEnd * fps));
    }
    if (props.trackingData && props.trackingData.length > 0) {
      const lastFrame = props.trackingData[props.trackingData.length - 1].f;
      durationInFrames = Math.max(durationInFrames, lastFrame + 5);
    }
  }
  return {
    props,
    durationInFrames,
    fps,
  };
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function cleanToken(w: string): string {
  return (w || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
}

function isKeywordMatch(wordText: string, keywords: string[]): boolean {
  if (!keywords || keywords.length === 0) return false;
  const c = cleanToken(wordText);
  if (!c) return false;
  return keywords.some((k) => cleanToken(k) === c || c.includes(cleanToken(k)));
}

function findLastIndexHelper<T>(arr: T[], predicate: (item: T) => boolean): number {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (predicate(arr[i])) return i;
  }
  return -1;
}

// ─── TEMPLATE 1: DELHI (Captik Style) ─────────────────────────────────────────

type DelhiPhrase = {
  words: WordInfo[];
  startTime: number;
  endTime: number;
};

function buildDelhiPhrases(transcript: WordInfo[]): DelhiPhrase[] {
  if (!transcript || transcript.length === 0) return [];
  const phrases: DelhiPhrase[] = [];
  let currentWords: WordInfo[] = [];

  for (let i = 0; i < transcript.length; i++) {
    const w = transcript[i];
    const prev = currentWords[currentWords.length - 1];

    const pause = prev ? w.start - prev.end : 0;
    const endsSentence = prev ? /[.!?]$/.test(prev.text.trim()) : false;
    const phraseDuration = currentWords.length > 0 ? w.end - currentWords[0].start : 0;

    if (currentWords.length > 0 && (pause > 0.45 || endsSentence || currentWords.length >= 5 || phraseDuration > 2.2)) {
      phrases.push({
        words: currentWords,
        startTime: currentWords[0].start,
        endTime: currentWords[currentWords.length - 1].end,
      });
      currentWords = [];
    }
    currentWords.push(w);
  }

  if (currentWords.length > 0) {
    phrases.push({
      words: currentWords,
      startTime: currentWords[0].start,
      endTime: currentWords[currentWords.length - 1].end,
    });
  }
  return phrases;
}

export const DelhiCaption: React.FC<CaptionsProps> = (props) => {
  const {
    videoPath,
    transcript = [],
    keywords = [],
    transparentOverlay = false,
    fontSize = 44,
    captionYPercent = 54,
    textColor = "#FFFFFF",
    keywordColor = "#FFFFFF",
  } = props;

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const phrases = buildDelhiPhrases(transcript);
  const activePhraseIdx = findLastIndexHelper(
    phrases,
    (p: DelhiPhrase) => currentTime >= p.startTime - 0.05
  );
  let activePhrase = activePhraseIdx >= 0 ? phrases[activePhraseIdx] : null;
  if (activePhrase && currentTime > activePhrase.endTime + 0.35) {
    activePhrase = null;
  }

  const isTransparent = transparentOverlay || !videoPath;

  return (
    <AbsoluteFill style={{ backgroundColor: isTransparent ? "transparent" : "black" }}>
      {!isTransparent && videoPath ? (
        <AbsoluteFill>
          <Video
            src={staticFile(videoPath)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      ) : null}

      {/* Compliance / Discount Badge */}
      {props.overlayText ? (
        <div
          style={{
            position: "absolute",
            top: 140,
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "rgba(10, 15, 25, 0.88)",
            border: "2px solid #FFFFFF",
            boxShadow: "0 0 20px rgba(255, 255, 255, 0.35)",
            borderRadius: 30,
            padding: "8px 28px",
            color: "#FFFFFF",
            fontFamily: "'Instrument Sans', sans-serif",
            fontSize: 28,
            fontWeight: 700,
            letterSpacing: 1.5,
            textTransform: "uppercase",
            zIndex: 100,
          }}
        >
          🏷️ {props.overlayText}
        </div>
      ) : null}

      {/* Delhi Caption Flow */}
      {activePhrase && (
        <div
          style={{
            position: "absolute",
            top: `${captionYPercent}%`,
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "90%",
            maxWidth: 1000,
            display: "flex",
            gap: 14,
            flexWrap: "wrap",
            justifyContent: "center",
            alignItems: "baseline",
            pointerEvents: "none",
            padding: "0 20px",
          }}
        >
          {activePhrase.words.map((word, idx) => {
            const isEmphasized = isKeywordMatch(word.text, keywords);
            const isSpoken = currentTime >= word.start;
            const isActive = currentTime >= word.start && currentTime <= word.end;

            // Spring pop for active spoken word
            const popProgress = spring({
              frame: frame - Math.floor(word.start * fps),
              fps,
              config: { damping: 14, stiffness: 220 },
            });
            const scale = isSpoken
              ? isActive
                ? interpolate(popProgress, [0, 1], [0.85, 1.1])
                : 1.0
              : 1.0;

            const opacity = isSpoken ? 1.0 : 0.22;

            return (
              <span
                key={idx}
                style={{
                  display: "inline-block",
                  fontFamily: isEmphasized
                    ? "'Shelley', 'Instrument Serif', cursive"
                    : "'Instrument Sans', -apple-system, sans-serif",
                  fontStyle: "normal",
                  fontWeight: isEmphasized ? 400 : 700,
                  fontSize: isEmphasized ? `${fontSize * 1.35}px` : `${fontSize}px`,
                  color: isEmphasized ? keywordColor : textColor,
                  textShadow: isEmphasized
                    ? "0 0 18px rgba(255,255,255,0.85), 0 0 35px rgba(255,255,255,0.4), 0 3px 12px rgba(0,0,0,0.95)"
                    : "0 2px 10px rgba(0,0,0,0.95)",
                  opacity,
                  transform: `scale(${scale})`,
                  letterSpacing: isEmphasized ? "0.5px" : "1.5px",
                  lineHeight: 1.15,
                  userSelect: "none",
                }}
              >
                {word.text}
              </span>
            );
          })}
        </div>
      )}
    </AbsoluteFill>
  );
};

// ─── TEMPLATE 2: EDITOR MASALA (Captik Signature Kinetic Sandwich) ─────────────

type MasalaPhrase = {
  phraseIndex: number;
  topWords: WordInfo[];
  heroWord: WordInfo;
  bottomWords: WordInfo[];
  startTime: number;
  endTime: number;
  persona: "A" | "B";
};

const STOP_WORDS = new Set(["THE", "A", "AN", "AND", "OR", "BUT", "OF", "IN", "ON", "AT", "TO", "FOR", "WITH", "IS", "ARE", "WAS", "WERE"]);

function buildMasalaPhrases(
  transcript: WordInfo[],
  keywords: string[],
  forcedPersona: "auto" | "A" | "B"
): MasalaPhrase[] {
  if (!transcript || transcript.length === 0) return [];
  const phrases: MasalaPhrase[] = [];
  let chunk: WordInfo[] = [];

  for (let i = 0; i < transcript.length; i++) {
    const w = transcript[i];
    const prev = chunk[chunk.length - 1];
    const pause = prev ? w.start - prev.end : 0;
    const endsSentence = prev ? /[.!?]$/.test(prev.text.trim()) : false;

    if (chunk.length > 0 && (pause > 0.45 || endsSentence || chunk.length >= 6)) {
      processChunk(chunk, phrases.length);
      chunk = [];
    }
    chunk.push(w);
  }
  if (chunk.length > 0) {
    processChunk(chunk, phrases.length);
  }

  function processChunk(words: WordInfo[], pIdx: number) {
    if (words.length === 0) return;

    // Find the hero word
    let heroIdx = -1;
    // 1. Look for explicit keyword
    heroIdx = words.findIndex((w) => isKeywordMatch(w.text, keywords));

    // 2. Look for longest non-stopword (>3 chars)
    if (heroIdx === -1) {
      let maxLen = 3;
      for (let j = 0; j < words.length; j++) {
        const clean = cleanToken(words[j].text);
        if (clean.length > maxLen && !STOP_WORDS.has(clean)) {
          maxLen = clean.length;
          heroIdx = j;
        }
      }
    }

    // 3. Fallback to middle word
    if (heroIdx === -1) {
      heroIdx = Math.floor(words.length / 2);
    }

    const heroWord = words[heroIdx];
    const topWords = words.slice(0, heroIdx);
    const bottomWords = words.slice(heroIdx + 1);

    // Alternate personas in auto mode for dynamic reel variety
    let persona: "A" | "B" = "B";
    if (forcedPersona === "A") persona = "A";
    else if (forcedPersona === "B") persona = "B";
    else persona = pIdx % 2 === 0 ? "B" : "A";

    phrases.push({
      phraseIndex: pIdx,
      topWords,
      heroWord,
      bottomWords,
      startTime: words[0].start,
      endTime: words[words.length - 1].end,
      persona,
    });
  }

  return phrases;
}

export const EditorMasalaCaption: React.FC<CaptionsProps> = (props) => {
  const {
    videoPath,
    transcript = [],
    keywords = [],
    personaMode = "auto",
    transparentOverlay = false,
    fontSize = 38,
    captionYPercent = 54,
    heroColor = "#FFD700",
  } = props;

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const phrases = buildMasalaPhrases(transcript, keywords, personaMode);
  const activePhraseIdx = findLastIndexHelper(
    phrases,
    (p: MasalaPhrase) => currentTime >= p.startTime - 0.05
  );
  let activePhrase = activePhraseIdx >= 0 ? phrases[activePhraseIdx] : null;
  if (activePhrase && currentTime > activePhrase.endTime + 0.35) {
    activePhrase = null;
  }

  const isTransparent = transparentOverlay || !videoPath;

  return (
    <AbsoluteFill style={{ backgroundColor: isTransparent ? "transparent" : "black" }}>
      {!isTransparent && videoPath ? (
        <AbsoluteFill>
          <Video
            src={staticFile(videoPath)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      ) : null}

      {/* Compliance / Discount Badge */}
      {props.overlayText ? (
        <div
          style={{
            position: "absolute",
            top: 140,
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "rgba(10, 15, 25, 0.9)",
            border: "2px solid #FFD700",
            boxShadow: "0 0 25px rgba(255, 215, 0, 0.45)",
            borderRadius: 30,
            padding: "8px 28px",
            color: "#FFFFFF",
            fontFamily: "'Montserrat', sans-serif",
            fontSize: 28,
            fontWeight: 800,
            letterSpacing: 2,
            textTransform: "uppercase",
            zIndex: 100,
          }}
        >
          🏷️ {props.overlayText}
        </div>
      ) : null}

      {/* Kinetic 3-Tier Sandwich */}
      {activePhrase && (
        <div
          style={{
            position: "absolute",
            top: `${captionYPercent}%`,
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "92%",
            maxWidth: 1000,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            pointerEvents: "none",
            gap: 4,
          }}
        >
          {/* 1. TOP CONTEXT LINE (Words before Hero) — Low captions: white and bold */}
          {activePhrase.topWords.length > 0 && (
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                justifyContent: "center",
                gap: 10,
                transform: "translateX(16px)", // Signature kinetic diagonal offset
                willChange: "transform",
              }}
            >
              {activePhrase.topWords.map((w, idx) => {
                const isSpoken = currentTime >= w.start;
                const pop = spring({
                  frame: frame - Math.floor(w.start * fps),
                  fps,
                  config: { damping: 14, stiffness: 220 },
                });
                const scale = isSpoken ? interpolate(pop, [0, 1], [0.8, 1]) : 1;
                return (
                  <span
                    key={idx}
                    style={{
                      fontFamily: "'Montserrat', sans-serif",
                      fontWeight: 800,
                      fontSize: `${fontSize}px`,
                      color: "#FFFFFF",
                      textTransform: "uppercase",
                      letterSpacing: "2px",
                      opacity: isSpoken ? 1.0 : 0.25,
                      transform: `scale(${scale})`,
                      textShadow: "0 3px 14px rgba(0,0,0,0.95), 0 1px 4px rgba(0,0,0,1)",
                      lineHeight: 1,
                      userSelect: "none",
                    }}
                  >
                    {w.text}
                  </span>
                );
              })}
            </div>
          )}

          {/* 2. CENTER HERO WORD — Big main part caption (Shelley script or Gold Montserrat) */}
          {(() => {
            const hw = activePhrase.heroWord;
            const isSpoken = currentTime >= hw.start;
            const heroPop = spring({
              frame: frame - Math.floor(hw.start * fps),
              fps,
              config: { damping: 12, stiffness: 180 },
            });
            const scale = isSpoken ? interpolate(heroPop, [0, 1], [0.55, 1.0]) : 0.9;
            const isPersonaA = activePhrase.persona === "A";

            return (
              <div
                style={{
                  zIndex: 10,
                  margin: "2px 0",
                  transform: `scale(${scale})`,
                  opacity: isSpoken ? 1.0 : 0.25,
                  userSelect: "none",
                }}
              >
                <span
                  style={{
                    display: "inline-block",
                    fontFamily: isPersonaA
                      ? "'Shelley', 'Instrument Serif', cursive"
                      : "'Montserrat', sans-serif",
                    fontStyle: "normal",
                    fontWeight: isPersonaA ? 400 : 900,
                    fontSize: isPersonaA ? `${fontSize * 2.8}px` : `${fontSize * 2.2}px`,
                    textTransform: isPersonaA ? "lowercase" : "uppercase",
                    color: isPersonaA ? "#FFFFFF" : heroColor,
                    letterSpacing: isPersonaA ? "1px" : "3px",
                    lineHeight: 0.95,
                    textShadow: isPersonaA
                      ? "0 0 18px rgba(255,255,255,0.85), 0 0 35px rgba(255,255,255,0.4), 0 4px 16px rgba(0,0,0,0.95)"
                      : `0 0 18px ${heroColor}CC, 0 0 38px ${heroColor}66, 0 4px 18px rgba(0,0,0,0.95)`,
                  }}
                >
                  {hw.text}
                </span>
              </div>
            );
          })()}

          {/* 3. BOTTOM CONTEXT LINE (Words after Hero) — Low captions: white and bold */}
          {activePhrase.bottomWords.length > 0 && (
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                justifyContent: "center",
                gap: 10,
                transform: "translateX(-16px)", // Opposite diagonal offset
                willChange: "transform",
              }}
            >
              {activePhrase.bottomWords.map((w, idx) => {
                const isSpoken = currentTime >= w.start;
                const pop = spring({
                  frame: frame - Math.floor(w.start * fps),
                  fps,
                  config: { damping: 14, stiffness: 220 },
                });
                const scale = isSpoken ? interpolate(pop, [0, 1], [0.8, 1]) : 1;
                return (
                  <span
                    key={idx}
                    style={{
                      fontFamily: "'Montserrat', sans-serif",
                      fontWeight: 800,
                      fontSize: `${fontSize}px`,
                      color: "#FFFFFF",
                      textTransform: "uppercase",
                      letterSpacing: "2px",
                      opacity: isSpoken ? 1.0 : 0.25,
                      transform: `scale(${scale})`,
                      textShadow: "0 3px 14px rgba(0,0,0,0.95), 0 1px 4px rgba(0,0,0,1)",
                      lineHeight: 1,
                      userSelect: "none",
                    }}
                  >
                    {w.text}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};

// ─── TEMPLATE 3: GUM GUM (2-Sword AE Style) ───────────────────────────────────

export const TWO_SWORD_ACCENT_COLORS = [
  "#FF2A4D", // Punchy Red
  "#00FF66", // Electric Green
  "#2563EB", // Vibrant Royal / Dark Blue
  "#FFD700", // Bright Gold
  "#00E5FF", // Neon Cyan
  "#FF007F", // Neon Magenta / Hot Pink
  "#FF6B00", // Electric Orange
  "#8B5CF6", // Deep Purple / Violet
];

type Phrase = {
  phraseIndex: number;
  line1Words: WordInfo[];
  line2Words: WordInfo[];
  keywords: string[];
  startTime: number;
  endTime: number;
  accentColor: string;
};

function buildPhrases(transcript: WordInfo[], globalKeywords: string[]): Phrase[] {
  if (!transcript || transcript.length === 0) return [];

  const keywordSet = new Set(
    globalKeywords.map((k) => cleanToken(k))
  );

  const sentences: WordInfo[][] = [];
  let currentGroup: WordInfo[] = [];

  for (let i = 0; i < transcript.length; i++) {
    const w = transcript[i];
    const prev = currentGroup[currentGroup.length - 1];
    const pause = prev ? w.start - prev.end : 0;
    const endsSentence = prev ? /[.!?]$/.test(prev.text.trim()) : false;

    if (currentGroup.length > 0 && (pause > 0.4 || endsSentence || currentGroup.length >= 6)) {
      sentences.push(currentGroup);
      currentGroup = [];
    }
    currentGroup.push(w);
  }
  if (currentGroup.length > 0) sentences.push(currentGroup);

  const phrases: Phrase[] = [];
  let pIdx = 0;
  for (const group of sentences) {
    const accentColor = TWO_SWORD_ACCENT_COLORS[pIdx % TWO_SWORD_ACCENT_COLORS.length];
    if (group.length <= 3) {
      phrases.push({
        phraseIndex: pIdx,
        line1Words: [],
        line2Words: group,
        keywords: Array.from(keywordSet),
        startTime: group[0].start,
        endTime: group[group.length - 1].end,
        accentColor,
      });
    } else {
      const splitIdx = Math.ceil(group.length / 2);
      phrases.push({
        phraseIndex: pIdx,
        line1Words: group.slice(0, splitIdx),
        line2Words: group.slice(splitIdx),
        keywords: Array.from(keywordSet),
        startTime: group[0].start,
        endTime: group[group.length - 1].end,
        accentColor,
      });
    }
    pIdx++;
  }
  return phrases;
}

function buildGlowShadow(
  color: string,
  isKeyword: boolean,
  glowIntensity: number,
  shadowIntensity: number
): string {
  if (!isKeyword) {
    return [
      `2px 2px 0px rgba(0,0,0, 1)`,
      `-2px -2px 0px rgba(0,0,0, 1)`,
      `2px -2px 0px rgba(0,0,0, 1)`,
      `-2px 2px 0px rgba(0,0,0, 1)`,
      `0 4px ${16 * shadowIntensity}px rgba(0,0,0, 0.95)`,
    ].join(", ");
  }

  const c = color.startsWith("#") ? color : "#00FF66";
  const r = parseInt(c.slice(1, 3), 16) || 0;
  const g = parseInt(c.slice(3, 5), 16) || 255;
  const b = parseInt(c.slice(5, 7), 16) || 102;

  const glow = glowIntensity;
  const shadow = shadowIntensity;

  return [
    `2px 2px 0px rgba(0,0,0, 1)`,
    `-2px -2px 0px rgba(0,0,0, 1)`,
    `2px -2px 0px rgba(0,0,0, 1)`,
    `-2px 2px 0px rgba(0,0,0, 1)`,
    `0 0 ${12 * glow}px rgba(${r},${g},${b}, 0.85)`,
    `0 0 ${32 * glow}px rgba(${r},${g},${b}, 0.50)`,
    `0 4px ${16 * shadow}px rgba(0,0,0, 0.95)`,
  ].join(", ");
}

export const GumGumCaption: React.FC<CaptionsProps> = (props) => {
  const { videoPath, transcript, keywords = [], transparentOverlay = false } = props;
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const phrases = buildPhrases(transcript, keywords);
  const activePhraseIdx = findLastIndexHelper(
    phrases,
    (p: Phrase) => currentTime >= p.startTime - 0.05
  );

  let activePhrase = activePhraseIdx >= 0 ? phrases[activePhraseIdx] : null;
  if (activePhrase && currentTime > activePhrase.endTime + 0.4) {
    activePhrase = null;
  }

  const isTransparent = transparentOverlay || !videoPath;

  return (
    <AbsoluteFill style={{ backgroundColor: isTransparent ? "transparent" : "black" }}>
      {!isTransparent && videoPath ? (
        <AbsoluteFill>
          <Video
            src={staticFile(videoPath)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      ) : null}

      {props.overlayText ? (
        <div
          style={{
            position: "absolute",
            top: 140,
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "rgba(10, 15, 25, 0.88)",
            border: "2.5px solid #00FF66",
            boxShadow: "0 0 25px rgba(0, 255, 102, 0.5), inset 0 0 10px rgba(0, 255, 102, 0.2)",
            borderRadius: 35,
            padding: "10px 32px",
            color: "#FFFFFF",
            fontFamily: "'Komika Axis', 'Impact', 'Arial Black', sans-serif",
            fontSize: 32,
            fontWeight: 900,
            letterSpacing: 2,
            textTransform: "uppercase",
            zIndex: 100,
          }}
        >
          🏷️ {props.overlayText}
        </div>
      ) : null}

      <div
        style={{
          position: "absolute",
          top: `${props.captionYPercent ?? 54}%`,
          left: 0,
          right: 0,
          transform: "translateY(-50%)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          pointerEvents: "none",
          padding: "0 24px",
        }}
      >
        {activePhrase && (
          <PhraseBlock
            phrase={activePhrase}
            currentTime={currentTime}
            fps={fps}
            frame={frame}
            styleProps={props}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};

type StyleProps = Omit<CaptionsProps, "videoPath" | "transcript" | "trackingData">;

const PhraseBlock: React.FC<{
  phrase: Phrase;
  currentTime: number;
  fps: number;
  frame: number;
  styleProps: StyleProps;
}> = ({ phrase, currentTime, fps, frame, styleProps }) => {
  const exitStart = phrase.endTime + 0.1;
  const exitProgress =
    currentTime > exitStart
      ? Math.min(1, (currentTime - exitStart) / 0.3)
      : 0;
  const blockOpacity = 1 - exitProgress;
  const blockTranslateY = -exitProgress * 8;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        opacity: blockOpacity,
        transform: `translateY(${blockTranslateY}px)`,
        gap: `${styleProps.lineGap}px`,
      }}
    >
      {phrase.line1Words.length > 0 && (
        <div style={{ display: "flex", flexWrap: "nowrap", justifyContent: "center" }}>
          {phrase.line1Words.map((word, i) => (
            <WordItem
              key={i}
              word={word}
              wordType="line1"
              currentTime={currentTime}
              fps={fps}
              frame={frame}
              styleProps={styleProps}
              keywords={phrase.keywords}
              accentColor={phrase.accentColor}
            />
          ))}
        </div>
      )}

      {phrase.line2Words.length > 0 && (
        <div style={{ display: "flex", flexWrap: "nowrap", justifyContent: "center" }}>
          {phrase.line2Words.map((word, i) => (
            <WordItem
              key={i}
              word={word}
              wordType="line2"
              currentTime={currentTime}
              fps={fps}
              frame={frame}
              styleProps={styleProps}
              keywords={phrase.keywords}
              accentColor={phrase.accentColor}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const WordItem: React.FC<{
  word: WordInfo;
  wordType: "line1" | "line2";
  currentTime: number;
  fps: number;
  frame: number;
  styleProps: StyleProps;
  keywords: string[];
  accentColor: string;
}> = ({ word, wordType, currentTime, fps, frame, styleProps, keywords, accentColor }) => {
  const isKeyword = isKeywordMatch(word.text, keywords);

  const startFrame = Math.round(word.start * fps);
  const framesSinceStart = frame - startFrame;

  let opacity = 0;
  let translateY = 0;
  let scale = 1;

  if (currentTime < word.start) {
    opacity = 0;
  } else {
    opacity = 1;
    const popProgress = spring({
      frame: framesSinceStart,
      fps,
      config: { damping: 14, stiffness: 220, mass: 0.8 },
    });
    translateY = interpolate(popProgress, [0, 1], [-12, 0]);
    scale = interpolate(popProgress, [0, 1], [styleProps.popScaleAmount, 1]);
  }

  // Line 1: Pure crisp white bold. Line 2: Big dynamic rotating accent color (red, green, dark blue, gold, etc.)
  const color =
    wordType === "line1"
      ? (styleProps.line1Color || "#FFFFFF")
      : accentColor;

  const fontSize =
    wordType === "line1"
      ? (styleProps.line1FontSize || 38)
      : (styleProps.line2FontSize || 50);

  const isGlowTarget = wordType === "line2" || isKeyword;
  const textShadow = buildGlowShadow(
    color,
    isGlowTarget,
    styleProps.glowIntensity,
    styleProps.shadowIntensity
  );

  return (
    <span
      style={{
        display: "inline-block",
        opacity,
        transform: `translateY(${translateY}px) scale(${scale})`,
        margin: "0 6px",
        fontFamily: "'Komika Axis', 'Impact', 'Arial Black', sans-serif",
        fontWeight: 900,
        fontSize: `${fontSize}px`,
        letterSpacing: `${styleProps.letterSpacing ?? 2}px`,
        textTransform: "uppercase",
        lineHeight: 1.2,
        color,
        textShadow,
        userSelect: "none",
      }}
    >
      {word.text}
    </span>
  );
};

// ─── MASTER VIRAL CAPTION COMPONENT (Template Router) ─────────────────────────

export const ViralCaptionComponent: React.FC<CaptionsProps> = (props) => {
  const template = props.template || "gum_gum";
  if (template === "delhi") {
    return <DelhiCaption {...props} />;
  }
  if (template === "editor_masala") {
    return <EditorMasalaCaption {...props} />;
  }
  // Default to 2_sword style (GumGum)
  return <GumGumCaption {...props} />;
};
