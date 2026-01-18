package flows

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"genkit-service/models"

	"github.com/firebase/genkit/go/ai"
	"github.com/firebase/genkit/go/genkit"
	"github.com/firebase/genkit/go/plugins/googleai"
)

var promptOptimizerFlow *genkit.Flow[*models.PromptOptimizerRequest, *models.PromptOptimizerResponse, struct{}]

// DefinePromptOptimizerFlow creates the Antigravity prompt optimization flow
func DefinePromptOptimizerFlow() {
	promptOptimizerFlow = genkit.DefineFlow(
		"optimize-antigravity-prompt",
		func(ctx context.Context, input *models.PromptOptimizerRequest) (*models.PromptOptimizerResponse, error) {
			model := googleai.Model("gemini-1.5-flash-latest")

			// Load the system prompt template
			promptTemplate, err := os.ReadFile("prompts/antigravity_optimizer.prompt")
			if err != nil {
				return nil, fmt.Errorf("failed to load prompt template: %w", err)
			}

			// Build context summary
			contextParts := []string{}
			if len(input.CodebaseContext.OpenFiles) > 0 {
				contextParts = append(contextParts, fmt.Sprintf("Open Files: %s", strings.Join(input.CodebaseContext.OpenFiles, ", ")))
			}
			if len(input.CodebaseContext.RecentErrors) > 0 {
				contextParts = append(contextParts, fmt.Sprintf("Recent Errors: %s", strings.Join(input.CodebaseContext.RecentErrors, "; ")))
			}
			if input.CodebaseContext.ProjectType != "" {
				contextParts = append(contextParts, fmt.Sprintf("Project Type: %s", input.CodebaseContext.ProjectType))
			}
			if len(input.CodebaseContext.Files) > 0 {
				contextParts = append(contextParts, fmt.Sprintf("Relevant Files: %s", strings.Join(input.CodebaseContext.Files, ", ")))
			}

			contextStr := strings.Join(contextParts, "\n")
			if contextStr == "" {
				contextStr = "No specific context provided"
			}

			// Construct the user message
			userMessage := fmt.Sprintf(`Analyze this request and generate an optimized prompt for Antigravity.

User Goal: %s

Codebase Context:
%s

Additional Information: %s

Generate a structured, context-rich prompt following the guidelines in the system prompt.
Return ONLY valid JSON with the required fields: optimized_prompt, context_summary, relevant_files, estimated_complexity.`,
				input.Goal,
				contextStr,
				getOrDefaultStr(input.AdditionalInfo, "None"),
			)

			resp, err := model.Generate(ctx,
				ai.NewGenerateRequest(
					&ai.GenerationCommonConfig{
						Temperature: 0.7,
					},
					ai.NewUserTextMessage(string(promptTemplate)),
					ai.NewUserTextMessage(userMessage),
				),
			)
			if err != nil {
				return nil, fmt.Errorf("prompt optimization failed: %w", err)
			}

			var result models.PromptOptimizerResponse
			responseText := resp.Text()
			
			// Try to extract JSON from markdown code blocks if present
			responseText = extractJSON(responseText)
			
			if err := json.Unmarshal([]byte(responseText), &result); err != nil {
				return nil, fmt.Errorf("failed to parse optimizer response: %w (response: %s)", err, responseText)
			}

			return &result, nil
		},
	)
}

// extractJSON tries to extract JSON from markdown code blocks
func extractJSON(text string) string {
	// Check if wrapped in ```json ... ```
	if strings.Contains(text, "```json") {
		start := strings.Index(text, "```json") + 7
		end := strings.LastIndex(text, "```")
		if start > 0 && end > start {
			return strings.TrimSpace(text[start:end])
		}
	}
	
	// Check for generic code blocks
	if strings.Contains(text, "```") {
		start := strings.Index(text, "```") + 3
		end := strings.LastIndex(text, "```")
		if start > 0 && end > start {
			extracted := strings.TrimSpace(text[start:end])
			// Remove language identifier if present
			if idx := strings.Index(extracted, "\n"); idx > 0 && idx < 10 {
				extracted = extracted[idx+1:]
			}
			return extracted
		}
	}
	
	return text
}
