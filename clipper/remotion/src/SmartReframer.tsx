/**
 * SmartReframer v2 — Zero-Glitch Remotion Reframer
 *
 * KEY INSIGHT: Always render exactly 2 video panels.
 *   - Single mode: Both panels overlap to form one full 9:16 crop
 *   - Split mode: Panels separate into top/bottom stacked layout
 *   - Transition: Smooth CSS interpolation between the two states
 *   - NO layer swapping, NO crossfade, NO extra video instances
 */

import React from "react";
import { z } from "zod";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
  staticFile,
  interpolate,
  Easing,
} from "remotion";

// ─── Schema ──────────────────────────────────────────────────────────────────

const faceSchema = z.object({
  id: z.number().optional(),
  x: z.number(),
  box: z.array(z.number()).optional(),
});

const frameDataSchema = z.object({
  f: z.number(),
  faces: z.array(faceSchema).optional(),
  x: z.number().optional(),
});

export const reframerSchema = z.object({
  videoSrc: z.string(),
  trackingData: z.object({
    fps: z.number(),
    data: z.array(frameDataSchema),
  }),
  sourceWidth: z.number().default(1280),
  sourceHeight: z.number().default(720),
  faceDistanceThreshold: z.number().default(0.22),
  debounceSeconds: z.number().default(1.5),
  transitionFrames: z.number().default(10),
});

export type ReframerProps = z.infer<typeof reframerSchema>;

export const defaultReframerProps: ReframerProps = {
  videoSrc: "",
  trackingData: { fps: 25, data: [] },
  sourceWidth: 1280,
  sourceHeight: 720,
  faceDistanceThreshold: 0.22,
  debounceSeconds: 1.5,
  transitionFrames: 10,
};

// ─── Types ──────────────────────────────────────────────────────────────────

type FrameMode = "single" | "split";

interface ClassifiedFrame {
  frame: number;
  mode: FrameMode;
  centerX: number;
  leftX: number;
  rightX: number;
}

interface Segment {
  mode: FrameMode;
  startFrame: number;
  endFrame: number;
  avgCenterX: number;
  avgLeftX: number;
  avgRightX: number;
}

// ─── Classification ─────────────────────────────────────────────────────────

function classifyFrames(
  data: z.infer<typeof frameDataSchema>[],
  threshold: number
): ClassifiedFrame[] {
  return data.map((pt) => {
    const faces = pt.faces || [];
    const f = pt.f;

    if (faces.length >= 2) {
      const dist = Math.abs(faces[0].x - faces[1].x);
      if (dist > threshold) {
        const sorted = [...faces].sort((a, b) => a.x - b.x);
        return { frame: f, mode: "split" as FrameMode, centerX: (sorted[0].x + sorted[1].x) / 2, leftX: sorted[0].x, rightX: sorted[1].x };
      } else {
        const avg = (faces[0].x + faces[1].x) / 2;
        return { frame: f, mode: "single" as FrameMode, centerX: avg, leftX: avg, rightX: avg };
      }
    } else if (faces.length === 1) {
      return { frame: f, mode: "single" as FrameMode, centerX: faces[0].x, leftX: faces[0].x, rightX: faces[0].x };
    } else {
      const x = pt.x ?? 0.5;
      return { frame: f, mode: "single" as FrameMode, centerX: x, leftX: x, rightX: x };
    }
  });
}

function buildSegments(classified: ClassifiedFrame[], fps: number, debounceSeconds: number): Segment[] {
  if (classified.length === 0) return [];

  const raw: Segment[] = [];
  let curr = classified[0];
  let startF = curr.frame;
  let cxAcc = [curr.centerX], lxAcc = [curr.leftX], rxAcc = [curr.rightX];

  for (let i = 1; i < classified.length; i++) {
    const c = classified[i];
    if (c.mode !== curr.mode) {
      raw.push({
        mode: curr.mode, startFrame: startF, endFrame: c.frame,
        avgCenterX: cxAcc.reduce((a, b) => a + b, 0) / cxAcc.length,
        avgLeftX: lxAcc.reduce((a, b) => a + b, 0) / lxAcc.length,
        avgRightX: rxAcc.reduce((a, b) => a + b, 0) / rxAcc.length,
      });
      curr = c; startF = c.frame;
      cxAcc = [c.centerX]; lxAcc = [c.leftX]; rxAcc = [c.rightX];
    } else {
      cxAcc.push(c.centerX); lxAcc.push(c.leftX); rxAcc.push(c.rightX);
    }
  }
  raw.push({
    mode: curr.mode, startFrame: startF, endFrame: classified[classified.length - 1].frame + 1,
    avgCenterX: cxAcc.reduce((a, b) => a + b, 0) / cxAcc.length,
    avgLeftX: lxAcc.reduce((a, b) => a + b, 0) / lxAcc.length,
    avgRightX: rxAcc.reduce((a, b) => a + b, 0) / rxAcc.length,
  });

  // Debounce
  const debounceFrames = debounceSeconds * fps;
  const clean: Segment[] = [];
  for (const s of raw) {
    if ((s.endFrame - s.startFrame) < debounceFrames && clean.length > 0) {
      clean[clean.length - 1] = { ...clean[clean.length - 1], endFrame: s.endFrame };
    } else {
      clean.push(s);
    }
  }
  return clean;
}

// Interpolate face position at any frame from sparse keyframes
function getFrameX(classified: ClassifiedFrame[], frame: number, key: "centerX" | "leftX" | "rightX"): number {
  if (classified.length === 0) return 0.5;
  let lo = classified[0], hi = classified[classified.length - 1];
  for (let i = 0; i < classified.length; i++) {
    if (classified[i].frame <= frame) lo = classified[i];
    if (classified[i].frame >= frame) { hi = classified[i]; break; }
  }
  if (lo.frame === hi.frame) return lo[key];
  const t = (frame - lo.frame) / (hi.frame - lo.frame);
  return lo[key] + t * (hi[key] - lo[key]);
}

// ─── Compute split progress with easing ─────────────────────────────────────

function computeSplitProgress(frame: number, segments: Segment[], transitionFrames: number): number {
  // Find current and adjacent segments
  let currentSeg: Segment | null = null;
  for (const s of segments) {
    if (frame >= s.startFrame && frame < s.endFrame) { currentSeg = s; break; }
  }
  if (!currentSeg) {
    // Past the end — use last segment
    currentSeg = segments[segments.length - 1];
  }

  const targetProgress = currentSeg.mode === "split" ? 1 : 0;

  // Animate from the boundary
  const framesIntoSegment = frame - currentSeg.startFrame;

  if (framesIntoSegment >= transitionFrames) {
    return targetProgress; // Fully transitioned
  }

  // We're in the transition zone — find what the previous mode was
  const prevTarget = targetProgress === 1 ? 0 : 1;

  const t = interpolate(
    framesIntoSegment,
    [0, transitionFrames],
    [prevTarget, targetProgress],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) }
  );

  return t;
}

// ─── Main Component ─────────────────────────────────────────────────────────

export const SmartReframerVideo: React.FC<ReframerProps> = (props) => {
  const { videoSrc, trackingData, sourceWidth, sourceHeight, faceDistanceThreshold, debounceSeconds, transitionFrames } = props;
  const frame = useCurrentFrame();
  const { width: outW, height: outH } = useVideoConfig();

  const classified = React.useMemo(() => classifyFrames(trackingData.data, faceDistanceThreshold), [trackingData.data, faceDistanceThreshold]);
  const segments = React.useMemo(() => buildSegments(classified, trackingData.fps, debounceSeconds), [classified, trackingData.fps, debounceSeconds]);

  // splitProgress: 0 = single, 1 = split (smoothly animated)
  const splitProgress = computeSplitProgress(frame, segments, transitionFrames);

  // Get interpolated face positions
  const centerX = getFrameX(classified, frame, "centerX");
  const leftX = getFrameX(classified, frame, "leftX");
  const rightX = getFrameX(classified, frame, "rightX");

  // ─── Geometry calculations ──────────────────────────────────────────────

  const panelH = outH / 2; // 960px each panel in split mode

  // Single mode crop dimensions
  const singleCropW = sourceHeight * (outW / outH); // ~405px
  const singleScale = Math.max(outW / singleCropW, outH / sourceHeight);
  const singleCropX = Math.max(0, Math.min(centerX * sourceWidth - singleCropW / 2, sourceWidth - singleCropW));
  const singleTx = -(singleCropX + singleCropW / 2) * singleScale + outW / 2;
  const singleTy = -(sourceHeight / 2) * singleScale + outH / 2;

  // Split mode crop dimensions
  const splitCropW = Math.min(sourceHeight * (outW / panelH), sourceWidth / 2);
  const splitScale = Math.max(outW / splitCropW, panelH / sourceHeight);

  const leftCropX = Math.max(0, Math.min(leftX * sourceWidth - splitCropW / 2, sourceWidth - splitCropW));
  const rightCropX = Math.max(0, Math.min(rightX * sourceWidth - splitCropW / 2, sourceWidth - splitCropW));

  const splitTopTx = -(leftCropX + splitCropW / 2) * splitScale + outW / 2;
  const splitTopTy = -(sourceHeight / 2) * splitScale + panelH / 2;
  const splitBotTx = -(rightCropX + splitCropW / 2) * splitScale + outW / 2;
  const splitBotTy = -(sourceHeight / 2) * splitScale + panelH / 2;

  // ─── Interpolated panel transforms ──────────────────────────────────────
  // Panel A (top): In single mode, covers full screen. In split, covers top half.
  // Panel B (bottom): In single mode, hidden behind Panel A. In split, covers bottom half.

  const p = splitProgress;

  // Panel A: top position
  const panelATop = 0; // Always starts at top
  const panelAHeight = interpolate(p, [0, 1], [outH, panelH]); // Full height → half height
  const panelAScale = interpolate(p, [0, 1], [singleScale, splitScale]);
  const panelATx = interpolate(p, [0, 1], [singleTx, splitTopTx]);
  const panelATy = interpolate(p, [0, 1], [singleTy, splitTopTy]);

  // Panel B: bottom position
  const panelBTop = interpolate(p, [0, 1], [0, panelH]); // Overlapping → below panel A
  const panelBHeight = interpolate(p, [0, 1], [outH, panelH]);
  const panelBScale = interpolate(p, [0, 1], [singleScale, splitScale]);
  const panelBTx = interpolate(p, [0, 1], [singleTx, splitBotTx]);
  const panelBTy = interpolate(p, [0, 1], [singleTy, splitBotTy]);
  const panelBOpacity = interpolate(p, [0, 0.3, 1], [0, 1, 1]); // Fade in during first 30% of transition

  // Divider line between panels
  const dividerOpacity = interpolate(p, [0.5, 1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const videoW = sourceWidth * panelAScale;
  const videoH = sourceHeight * panelAScale;
  const videoW_B = sourceWidth * panelBScale;
  const videoH_B = sourceHeight * panelBScale;

  return (
    <AbsoluteFill style={{ backgroundColor: "black", overflow: "hidden" }}>
      {/* Panel A — Top / Full */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: panelATop,
          width: outW,
          height: panelAHeight,
          overflow: "hidden",
        }}
      >
        <OffthreadVideo
          src={staticFile(videoSrc)}
          style={{
            position: "absolute",
            width: videoW,
            height: videoH,
            left: panelATx,
            top: panelATy,
          }}
        />
      </div>

      {/* Panel B — Bottom / Hidden behind A in single mode */}
      {p > 0.01 && (
        <div
          style={{
            position: "absolute",
            left: 0,
            top: panelBTop,
            width: outW,
            height: panelBHeight,
            overflow: "hidden",
            opacity: panelBOpacity,
          }}
        >
          <OffthreadVideo
            src={staticFile(videoSrc)}
            style={{
              position: "absolute",
              width: videoW_B,
              height: videoH_B,
              left: panelBTx,
              top: panelBTy,
            }}
          />
        </div>
      )}

      {/* Divider line */}
      {dividerOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            left: 0,
            top: panelH - 1,
            width: outW,
            height: 3,
            backgroundColor: "rgba(0,0,0,0.9)",
            opacity: dividerOpacity,
            zIndex: 10,
          }}
        />
      )}
    </AbsoluteFill>
  );
};

