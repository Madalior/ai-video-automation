import "./index.css";
import { Composition } from "remotion";
import { GumGumCaption, defaultProps, calculateMetadata, captionsSchema } from "./Composition";
import { SmartReframerVideo, reframerSchema, defaultReframerProps } from "./SmartReframer";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Original GumGum Caption composition */}
      <Composition
        id="GumGumCaption"
        component={GumGumCaption}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        schema={captionsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />

      {/* ViralCaptionComponent alias for CaptionBurner */}
      <Composition
        id="ViralCaptionComponent"
        component={GumGumCaption}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        schema={captionsSchema}
        defaultProps={defaultProps}
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
