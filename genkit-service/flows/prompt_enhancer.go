package flows

import (
	"context"
	"encoding/json"
	"fmt"

	"genkit-service/models"

	"github.com/firebase/genkit/go/ai"
	"github.com/firebase/genkit/go/genkit"
	"github.com/firebase/genkit/go/plugins/googleai"
)

var promptEnhanceFlow *genkit.Flow[*models.PromptEnhanceRequest, *models.PromptEnhanceResponse, struct{}]

// DefinePromptEnhanceFlow creates the prompt enhancement flow
func DefinePromptEnhanceFlow() {
	promptEnhanceFlow = genkit.DefineFlow(
		"enhance-prompt",
		func(ctx context.Context, input *models.PromptEnhanceRequest) (*models.PromptEnhanceResponse, error) {
			model := googleai.Model("gemini-1.5-flash-latest")

			promptText := fmt.Sprintf(`You are an expert prompt engineer specializing in AI image generation (Dreamina, Midjourney, DALL-E style).

Original Prompt: %s
Desired Style: %s
Character Context: %s

Transform this basic prompt into a professional, detailed prompt that will produce stunning, high-quality images.

Enhancement Guidelines:
1. Subject Details: Add specific physical characteristics, age, expression, clothing
2. Composition: Camera angle, framing, rule of thirds
3. Lighting: Type, direction, quality, shadows and highlights
4. Artistic Style: Photography style, references, color grading
5. Technical: Camera/lens simulation, depth of field, resolution (8K, photorealistic)
6. Mood & Atmosphere: Emotional tone, color palette, environmental details
7. Consistency: Maintain character appearance if character_context provided

Return ONLY valid JSON:
{
  "enhanced_prompt": "complete enhanced prompt",
  "improvements": ["improvement 1", "improvement 2"],
  "style_guide": "brief consistency guide"
}`,
				input.Prompt,
				getOrDefaultStr(input.Style, "photorealistic"),
				getOrDefaultStr(input.CharacterContext, ""),
			)

			resp, err := model.Generate(ctx,
				ai.NewGenerateRequest(
					&ai.GenerationCommonConfig{
						Temperature: 0.8,
					},
					ai.NewUserTextMessage(promptText),
				),
			)
			if err != nil {
				return nil, fmt.Errorf("prompt enhancement failed: %w", err)
			}

			var result models.PromptEnhanceResponse
			if err := json.Unmarshal([]byte(resp.Text()), &result); err != nil {
				return nil, fmt.Errorf("failed to parse enhancement response: %w", err)
			}

			return &result, nil
		},
	)
}

func getOrDefaultStr(value, defaultValue string) string {
	if value == "" {
		return defaultValue
	}
	return value
}
