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

var errorRecoveryFlow *genkit.Flow[*models.ErrorRecoveryRequest, *models.ErrorRecoveryResponse, struct{}]

// DefineErrorRecoveryFlow creates the error recovery flow
func DefineErrorRecoveryFlow() {
	errorRecoveryFlow = genkit.DefineFlow(
		"recover-error",
		func(ctx context.Context, input *models.ErrorRecoveryRequest) (*models.ErrorRecoveryResponse, error) {
			model := googleai.Model("gemini-1.5-flash-latest")

			// Convert context map to JSON string
			contextJSON, _ := json.Marshal(input.Context)

			promptText := fmt.Sprintf(`You are an AI debugging expert specializing in image/video generation APIs (Dreamina, Veo, DALL-E, etc.).

Error Encountered:
%s

Context:
%s

Original Prompt: %s

Analyze this error and provide recovery strategies.

Common Error Patterns:
1. Timeout: Prompt too complex → Simplify prompt, retry with backoff
2. Content Policy: Inappropriate content → Rephrase to be policy-compliant
3. Invalid Parameters: Wrong dimensions/features → Adjust to valid ranges
4. Generation Failures: Vague prompt, conflicting instructions → Make specific and realistic
5. Rate Limiting: Too many requests → Exponential backoff, different worker
6. Quality Issues: Poor results → Improve detail, add style references

Return ONLY valid JSON:
{
  "analysis": "root cause explanation",
  "strategies": ["strategy 1", "strategy 2", "strategy 3"],
  "fixed_prompt": "corrected prompt if prompt-related",
  "recommendations": ["long-term improvement 1", "improvement 2"]
}`,
				input.Error,
				string(contextJSON),
				getOrEmpty(input.Prompt),
			)

			resp, err := model.Generate(ctx,
				ai.NewGenerateRequest(
					&ai.GenerationCommonConfig{
						Temperature: 0.5,
					},
					ai.NewUserTextMessage(promptText),
				),
			)
			if err != nil {
				return nil, fmt.Errorf("error recovery failed: %w", err)
			}

			var result models.ErrorRecoveryResponse
			if err := json.Unmarshal([]byte(resp.Text()), &result); err != nil {
				return nil, fmt.Errorf("failed to parse recovery response: %w", err)
			}

			return &result, nil
		},
	)
}

func getOrEmpty(value string) string {
	if value == "" {
		return "N/A"
	}
	return value
}
