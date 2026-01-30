package flows

import (
	"context"
	"fmt"

	"genkit-service/models"

	"github.com/firebase/genkit/go/ai"
	"github.com/firebase/genkit/go/genkit"
)

// DefineEmotionalScriptFlow defines the emotional script enhancement flow
func DefineEmotionalScriptFlow() {
	genkit.DefineFlow(
		"enhance-script-emotions",
		func(ctx context.Context, req *models.EmotionalScriptRequest) (*models.EmotionalScriptResponse, error) {
			// Load the emotional script prompt
			prompt, err := ai.DefinePrompt(
				"emotional-script",
				"prompts/emotional_script.prompt",
				ai.WithPromptMetadata(map[string]any{
					"description": "Enhance video scripts with emotional depth and human-like storytelling",
				}),
			)
			if err != nil {
				return nil, fmt.Errorf("failed to load emotional script prompt: %w", err)
			}

			// Set defaults
			videoType := req.VideoType
			if videoType == "" {
				videoType = "info"
			}

			emotionStyle := req.EmotionStyle
			if emotionStyle == "" {
				emotionStyle = "auto"
			}

			numScenes := req.NumScenes
			if numScenes == 0 {
				numScenes = 7
			}

			// Execute the prompt
			response, err := prompt.Generate(
				ctx,
				ai.WithPromptInput(map[string]any{
					"script":        req.Script,
					"video_type":    videoType,
					"emotion_style": emotionStyle,
					"num_scenes":    numScenes,
				}),
			)
			if err != nil {
				return nil, fmt.Errorf("emotional script generation failed: %w", err)
			}

			// Parse the structured output
			var result models.EmotionalScriptResponse
			if err := response.StructuredOutput(&result); err != nil {
				return nil, fmt.Errorf("failed to parse emotional script response: %w", err)
			}

			return &result, nil
		},
	)
}
