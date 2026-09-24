/**
 * GumGumCaption — Deep Glow + Drop Shadow Style
 *
 * Exact replica of the AE tutorial:
 *  - Deep Glow plugin: Radius=1000, Exposure=0.30, Blend=Screen, Unmult=on
 *  - Drop Shadow 1: Color=Black, Opacity=100%, Distance=0, Softness=50
 *  - Drop Shadow 2: Color=Black, Opacity=100%, Distance=0, Softness=200
 *  - Drop Shadow 3: Color=Black, Opacity=100%, Distance=0, Softness=200
 *  - Condensed sans-serif, ALL CAPS, wide letter spacing
 *  - Word-by-word pop-in animation
 *  - Normal words = white, Keywords = green highlight
 *  - 2-line layout: Line 1 (small gray), Line 2 (larger colored)
 */

import React from "react";
import { CalculateMetadataFunction, Solid } from "remotion";
import { z } from "zod";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  Video,
  staticFile,
  interpolate,
  spring,
} from "remotion";

// ─── Types & Controls Schema ──────────────────────────────────────────────────

export const transcriptSchema = z.array(
  z.object({
    text: z.string(),
    start: z.number(),
    end: z.number(),
  })
);

// These controls appear in the Remotion Studio Sidebar!
export const captionsSchema = z.object({
  videoPath: z.string(),
  transcript: transcriptSchema,
  trackingData: z.array(z.object({ f: z.number(), x: z.number() })).optional(),
  
  // Visual Tweaks
  line1Color: z.string().default("#CCCCCC"),
  line2Color: z.string().default("#FFFFFF"),
  keywordColor: z.string().default("#00FF66"),
  glowIntensity: z.number().min(0).max(5).step(0.1).default(1.0),
  shadowIntensity: z.number().min(0).max(3).step(0.1).default(1.0),
  line1FontSize: z.number().min(20).max(200).default(34),
  line2FontSize: z.number().min(20).max(250).default(40),
  keywordFontSize: z.number().min(20).max(300).default(42),
  letterSpacing: z.number().min(0).max(20).step(0.5).default(3),
  popScaleAmount: z.number().min(1).max(2).step(0.05).default(1.08),
  lineGap: z.number().min(0).max(40).step(1).default(2),
  captionYPercent: z.number().min(10).max(95).default(68),
  // LLM-detected keywords to highlight in green (passed from Python)
  keywords: z.array(z.string()).default([]),
  // Compliance / promotion overlay badge (e.g. 20% OFF CODE: AF527550)
  overlayText: z.string().optional(),
});

export type CaptionsProps = z.infer<typeof captionsSchema>;
export type WordInfo = CaptionsProps["transcript"][0];

export const defaultProps: CaptionsProps = {
  videoPath: "meta_preview_clip.mp4",
  line1Color: "#CCCCCC",
  line2Color: "#FFFFFF",
  keywordColor: "#00FF66",
  glowIntensity: 1.0,
  shadowIntensity: 1.0,
  line1FontSize: 34,
  line2FontSize: 40,
  keywordFontSize: 42,
  letterSpacing: 3,
  popScaleAmount: 1.08,
  lineGap: 2,
  captionYPercent: 68,
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
  let durationInFrames = 300;
  if (props.transcript && props.transcript.length > 0) {
    const lastEnd = props.transcript[props.transcript.length - 1].end;
    durationInFrames = Math.max(durationInFrames, Math.ceil(lastEnd * 30));
  }
  if (props.trackingData && props.trackingData.length > 0) {
    const lastFrame = props.trackingData[props.trackingData.length - 1].f;
    durationInFrames = Math.max(durationInFrames, lastFrame + 5);
  }
  return {
    props,
    durationInFrames,
  };
};

// ─── Phrase Builder ───────────────────────────────────────────────────────────

type Phrase = {
  line1Words: WordInfo[];  // Top line (smaller, greyed)
  line2Words: WordInfo[];  // Bottom line (larger, with keywords)
  keywords: string[];      // Words to highlight with color
  startTime: number;
  endTime: number;
};

/**
 * Build 2-line phrases with natural cadence, pause detection, and sentence boundaries.
 */
function buildPhrases(transcript: WordInfo[], globalKeywords: string[]): Phrase[] {
  if (transcript.length === 0) return [];

  const keywordSet = new Set(
    globalKeywords.map((k) => k.toUpperCase().replace(/[^A-Z0-9]/g, ""))
  );

  // 1. Group words into natural sentence/pause chunks
  const chunks: WordInfo[][] = [];
  let currentChunk: WordInfo[] = [];

  for (let i = 0; i < transcript.length; i++) {
    const w = transcript[i];
    currentChunk.push(w);

    const hasPunctuation = /[.!?]$/.test(w.text.trim());
    const nextW = transcript[i + 1];
    const isLongPause = nextW ? (nextW.start - w.end >= 0.35) : false;
    const totalChars = currentChunk.reduce((acc, curr) => acc + curr.text.length, 0);
    const isChunkFull = currentChunk.length >= 8 || totalChars >= 38;

    if (hasPunctuation || isLongPause || isChunkFull || !nextW) {
      chunks.push(currentChunk);
      currentChunk = [];
    }
  }

  // 2. Build phrases from chunks with balanced 2-line layouts
  const phrases: Phrase[] = [];

  for (const chunk of chunks) {
    if (chunk.length === 0) continue;

    let line1: WordInfo[] = [];
    let line2: WordInfo[] = [];

    if (chunk.length <= 3) {
      // 1-3 words: punchy single line on bottom
      line1 = [];
      line2 = chunk;
    } else {
      // 4-7 words: split evenly between line1 and line2
      const splitIdx = Math.ceil(chunk.length / 2);
      line1 = chunk.slice(0, splitIdx);
      line2 = chunk.slice(splitIdx);
    }

    const allWords = [...line1, ...line2];
    const phraseKeywords = keywordSet.size > 0
      ? allWords
          .map((w) => w.text.toUpperCase().replace(/[^A-Z0-9]/g, ""))
          .filter((t) => keywordSet.has(t))
      : (line2.length > 0 ? [line2[0].text.toUpperCase().replace(/[^A-Z0-9]/g, "")] : []);

    phrases.push({
      line1Words: line1,
      line2Words: line2,
      keywords: phraseKeywords,
      startTime: allWords[0].start,
      endTime: allWords[allWords.length - 1].end,
    });
  }

  return phrases;
}

// ─── Deep Glow Text Shadow Generator ──────────────────────────────────────────

/**
 * Generates the CSS textShadow that replicates:
 * - Deep Glow: Radius=1000, Exposure=0.30, Screen blend
 * - Drop Shadow 1: Softness=50, Distance=0, Color=Black
 * - Drop Shadow 2: Softness=200, Distance=0, Color=Black
 * - Drop Shadow 3: Softness=200, Distance=0, Color=Black
 */
function buildGlowShadow(
  color: string,
  glowIntensity: number,
  shadowIntensity: number,
): string {
  // Parse the color for rgba manipulation (with fallback)
  const c = color || "#FFFFFF";
  const r = parseInt(c.slice(1, 3), 16) || 255;
  const g = parseInt(c.slice(3, 5), 16) || 255;
  const b = parseInt(c.slice(5, 7), 16) || 255;

  const glow = glowIntensity;
  const shadow = shadowIntensity;

  return [
    // ─── Drop Shadow stack (drawn behind the text, before the glow) ───
    // A tight, hard black shadow to give the text a crisp edge against the glow
    `2px 2px 0px rgba(0,0,0, 1)`,
    
    // ─── Deep Glow layers (simulates Radius=1000, Exposure=0.30) ───
    // Tight inner bloom (low opacity so the base text stays sharp!)
    `0 0 ${5 * glow}px rgba(${r},${g},${b}, 0.4)`,
    `0 0 ${10 * glow}px rgba(${r},${g},${b}, 0.3)`,
    // Medium bloom  
    `0 0 ${20 * glow}px rgba(${r},${g},${b}, 0.2)`,
    `0 0 ${40 * glow}px rgba(${r},${g},${b}, 0.15)`,
    // Wide bloom
    `0 0 ${80 * glow}px rgba(${r},${g},${b}, 0.1)`,
    `0 0 ${120 * glow}px rgba(${r},${g},${b}, 0.05)`,

    // ─── Drop Shadow stack (3 layers, Softness 50, 200, 200) ───
    // Drop Shadow 1: Softness=50
    `0 0 ${25 * shadow}px rgba(0,0,0, 0.9)`,
    // Drop Shadow 2: Softness=200
    `0 0 ${100 * shadow}px rgba(0,0,0, 0.7)`,
    // Drop Shadow 3: Softness=200
    `0 0 ${100 * shadow}px rgba(0,0,0, 0.5)`,
  ].join(", ");
}

// ─── Main Component ───────────────────────────────────────────────────────────

export const GumGumCaption: React.FC<CaptionsProps> = (props) => {
  const { videoPath, transcript, keywords = [] } = props;
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const phrases = buildPhrases(transcript, keywords);

  // Find active phrase
  const activePhraseIdx = phrases.findLastIndex((p) => {
    return currentTime >= p.startTime - 0.05;
  });

  let activePhrase = activePhraseIdx >= 0 ? phrases[activePhraseIdx] : null;
  
  // Clear if phrase has ended
  if (activePhrase && currentTime > activePhrase.endTime + 0.4) {
    activePhrase = null;
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Video layer */}
      {videoPath ? (
        <AbsoluteFill>
          <Video
            src={staticFile(videoPath)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      ) : null}

      {/* Compliance / Discount Code Overlay Badge */}
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
            whiteSpace: "nowrap",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <span style={{ color: "#00FF66" }}>🏷️</span>
          <span>{props.overlayText}</span>
        </div>
      ) : null}

      {/* Caption overlay */}
      <div
        style={{
          position: "absolute",
          top: `${props.captionYPercent ?? 68}%`,
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

// ─── Phrase Block (2-line caption group) ──────────────────────────────────────

type StyleProps = Omit<CaptionsProps, "videoPath" | "transcript" | "trackingData">;

const PhraseBlock: React.FC<{
  phrase: Phrase;
  currentTime: number;
  fps: number;
  frame: number;
  styleProps: StyleProps;
}> = ({ phrase, currentTime, fps, frame, styleProps }) => {
  // Exit fade
  const exitStart = phrase.endTime + 0.1;
  const exitProgress =
    currentTime > exitStart
      ? Math.min(1, (currentTime - exitStart) / 0.3)
      : 0;
  const opacity = 1 - exitProgress;

  // Subtle organic pulse (1.00x → 1.03x) instead of jarring 25% scale jumps
  const zoomScale = interpolate(
    currentTime,
    [phrase.startTime, Math.max(phrase.startTime + 0.01, phrase.endTime)],
    [1.0, 1.03],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        opacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: `${styleProps.lineGap}px`,
        padding: "0 60px",
        maxWidth: "960px",
        width: "100%",
        boxSizing: "border-box",
        transform: `scale(${zoomScale})`,
        // NO CSS transition here — Remotion controls timing frame-by-frame
      }}
    >
      {/* Line 1 — smaller, grey/dim setup text */}
      {phrase.line1Words.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "0.3em",
          }}
        >
          {phrase.line1Words.map((w, i) => (
            <AnimatedWord
              key={`L1-${i}`}
              word={w}
              fps={fps}
              frame={frame}
              wordType="line1"
              styleProps={styleProps}
            />
          ))}
        </div>
      )}

      {/* Line 2 — larger, with keyword highlights */}
      {phrase.line2Words.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            alignItems: "baseline",
            gap: "0.3em",
          }}
        >
          {phrase.line2Words.map((w, i) => (
            <AnimatedWord
              key={`L2-${i}`}
              word={w}
              fps={fps}
              frame={frame}
              wordType={phrase.keywords.includes(w.text) ? "keyword" : "line2"}
              styleProps={styleProps}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Animated Word ──────────────────────────────────────────────────────────────

type WordType = "line1" | "line2" | "keyword";

const AnimatedWord: React.FC<{
  word: WordInfo;
  fps: number;
  frame: number;
  wordType: WordType;
  styleProps: StyleProps;
}> = ({ word, fps, frame, wordType, styleProps }) => {
  const entryFrame = Math.round(word.start * fps);
  const isKeyword = wordType === "keyword";
  
  // Spring pop-in animation — keywords pop harder
  const entrySpring = spring({
    fps,
    frame,
    from: 0,
    to: 1,
    delay: entryFrame,
    config: isKeyword
      ? { damping: 12, stiffness: 250, mass: 0.6 }  // snappier pop for keywords
      : { damping: 14, stiffness: 200, mass: 0.7 },
  });

  const popScale = isKeyword ? styleProps.popScaleAmount : (wordType === "line2" ? 1.08 : 1.0);
  const translateY = interpolate(entrySpring, [0, 1], [isKeyword ? 30 : 15, 0]);
  const scale = interpolate(entrySpring, [0, 1], [popScale, 1]);
  const opacity = interpolate(entrySpring, [0, 1], [0, 1]);

  // Determine color & size based on word type
  let color: string;
  let fontSize: number;
  let fontWeight: number;
  let glowMult: number;

  switch (wordType) {
    case "line1":
      color = styleProps.line1Color;
      fontSize = styleProps.line1FontSize;
      fontWeight = 700;
      glowMult = 0.5;  // subtle glow for line1
      break;
    case "keyword":
      color = styleProps.keywordColor;
      fontSize = styleProps.keywordFontSize;
      fontWeight = 900;
      glowMult = 1.5;  // slightly stronger glow for keyword color pop
      break;
    case "line2":
    default:
      color = styleProps.line2Color;
      fontSize = styleProps.line2FontSize;
      fontWeight = 700;
      glowMult = 1.0;  // normal glow for line2
      break;
  }

  // Build the Deep Glow + Drop Shadow textShadow
  const textShadow = buildGlowShadow(
    color,
    styleProps.glowIntensity * glowMult,
    styleProps.shadowIntensity,
  );

  return (
    <span
      style={{
        display: "inline-block",
        opacity,
        transform: `translateY(${translateY}px) scale(${scale})`,
        margin: "0 6px",
        
        // Typography — condensed sans-serif, ALL CAPS, wide tracking
        fontFamily: "'Komika Axis', 'Impact', 'Arial Black', sans-serif",
        fontWeight: fontWeight,
        fontSize: `${fontSize}px`,
        letterSpacing: wordType === "line1" ? `${styleProps.letterSpacing + 2}px` : `${styleProps.letterSpacing}px`,
        textTransform: "uppercase" as const,
        lineHeight: 1.2,
        
        // Color & glow
        color: color,
        textShadow: textShadow,
        
        // No stroke — using a hard drop shadow for edge definition instead
        WebkitTextStroke: "none",
        
        userSelect: "none" as const,
      }}
    >
      {word.text}
    </span>
  );
};
