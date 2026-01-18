package flows

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"genkit-service/models"

	"github.com/firebase/genkit/go/ai"
	"github.com/firebase/genkit/go/genkit"
	"github.com/firebase/genkit/go/plugins/googleai"
)

var qualityValidationFlow *genkit.Flow[*models.ValidationRequest, *models.ValidationResponse, struct{}]

// DefineQualityValidationFlow creates the quality validation flow
func DefineQualityValidationFlow() {
	qualityValidationFlow = genkit.DefineFlow(
		"validate-content",
		func(ctx context.Context, input *models.ValidationRequest) (*models.ValidationResponse, error) {
			model := googleai.Model("gemini-1.5-flash-latest")

			// Build scenes description
			var scenesDesc strings.Builder
			for i, scene := range input.Scenes {
				scenesDesc.WriteString(fmt.Sprintf("\nScene %d:\n", i))
				scenesDesc.WriteString(fmt.Sprintf("- Duration: %ds\n", scene.Duration))
				scenesDesc.WriteString(fmt.Sprintf("- Narration: %s\n", scene.Narration))
				scenesDesc.WriteString(fmt.Sprintf("- Visual: %s\n", scene.VisualDesc))
				if len(scene.Keywords) > 0 {
					scenesDesc.WriteString(fmt.Sprintf("- Keywords: %s\n", strings.Join(scene.Keywords, ", ")))
				}
			}

			promptText := fmt.Sprintf(`You are a quality control specialist for video production. Analyze this video script and scenes for potential issues.

Complete Script:
%s

Total Duration: %d seconds

Scenes:%s

Validation Criteria:
1. Timing: Narration length vs scene duration, total duration matches, no scenes <3s or >12s
2. Content: Visual matches narration, logical flow, no contradictions, consistent tone
3. Character: Consistent descriptions, no conflicting attributes, personality alignment
4. Production: Clear visuals, engaging narration, keywords align, no vague descriptions
5. Technical: All required fields present, complete sentences, detailed enough

For each issue, provide:
- scene_index: Which scene (or -1 for script-wide)
- type: Category of issue
- message: Clear description
- severity: "critical", "warning", or "info"
- auto_fix: Suggested fix (if applicable)

Return ONLY valid JSON:
{
  "is_valid": boolean,
  "issues": [{"scene_index": 0, "type": "timing", "message": "...", "severity": "warning", "auto_fix": "..."}],
  "summary": "brief summary"
}`,
				input.Script,
				input.Duration,
				scenesDesc.String(),
			)

			resp, err := model.Generate(ctx,
				ai.NewGenerateRequest(
					&ai.GenerationCommonConfig{
						Temperature: 0.3,
					},
					ai.NewUserTextMessage(promptText),
				),
			)
			if err != nil {
				return nil, fmt.Errorf("quality validation failed: %w", err)
			}

			var result models.ValidationResponse
			if err := json.Unmarshal([]byte(resp.Text()), &result); err != nil {
				return nil, fmt.Errorf("failed to parse validation response: %w", err)
			}

			return &result, nil
		},
	)
}
