import "./index.css";
import { Composition } from "remotion";
import {
  ViralCaptionComponent,
  DelhiCaption,
  EditorMasalaCaption,
  GumGumCaption,
  defaultProps,
  calculateMetadata,
  captionsSchema,
} from "./Composition";
import { SmartReframerVideo, reframerSchema, defaultReframerProps } from "./SmartReframer";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Dynamic Master Caption Router (supports template: "delhi" | "editor_masala" | "gum_gum") */}
      <Composition
        id="ViralCaptionComponent"
        component={ViralCaptionComponent}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        schema={captionsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />

      {/* Captik Template 1: Delhi (Editorial Elegance) */}
      <Composition
        id="DelhiCaption"
        component={DelhiCaption}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        schema={captionsSchema}
        defaultProps={{ ...defaultProps, template: "delhi" }}
        calculateMetadata={calculateMetadata}
      />

      {/* Captik Template 2: Editor Masala (Kinetic 3-Tier Sandwich) */}
      <Composition
        id="EditorMasalaCaption"
        component={EditorMasalaCaption}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        schema={captionsSchema}
        defaultProps={{ ...defaultProps, template: "editor_masala" }}
        calculateMetadata={calculateMetadata}
      />

      {/* Legacy GumGum 2-Sword AE Style */}
      <Composition
        id="GumGumCaption"
        component={GumGumCaption}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        schema={captionsSchema}
        defaultProps={{ ...defaultProps, template: "gum_gum" }}
        calculateMetadata={calculateMetadata}
      />

      {/* Smart Reframer — Scene-Adaptive 9:16 crop with smooth transitions */}
      <Composition
        id="SmartReframer"
        component={SmartReframerVideo}
        durationInFrames={1000}
        fps={25}
        width={1080}
        height={1920}
        schema={reframerSchema}
        defaultProps={defaultReframerProps}
      />
    </>
  );
};
