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

var seoFlow *genkit.Flow[*models.SEORequest, *models.SEOResponse, struct{}]

// DefineSEOFlow creates the SEO optimization flow
func DefineSEOFlow() {
	seoFlow = genkit.DefineFlow(
		"optimize-seo",
		func(ctx context.Context, input *models.SEORequest) (*models.SEOResponse, error) {
			// Use Gemini 1.5 Flash for SEO optimization
			model := googleai.Model("gemini-1.5-flash-latest")

			// Create prompt
			promptText := fmt.Sprintf(`You are an expert YouTube SEO specialist. Analyze the following video content and create highly optimized metadata for maximum visibility and engagement.

Video Script:
%s

Niche: %s
Target Audience: %s
Duration: %d seconds

Generate SEO-optimized metadata with:
1. Title (60 chars max): Click-worthy, curiosity-driven, includes primary keyword
2. Description (300-500 words): First 150 chars crucial, relevant keywords, call-to-action
3. Tags (15-20 tags): Mix of broad and specific, niche-specific, trending related tags
4. Hashtags (5-8): Most relevant to content, mix of popular and niche-specific
5. Thumbnail Text (3-6 words max): Bold, attention-grabbing, all caps
6. Keywords: LSI keywords, related search terms, long-tail keywords

Return ONLY valid JSON matching this structure:
{
  "title": "string",
  "description": "string",
  "tags": ["string"],
  "hashtags": ["string"],
  "thumbnail_text": "string",
  "keywords": ["string"]
}`,
				input.Script,
				input.Niche,
				getOrDefault(input.TargetAudience, "general audience"),
				getOrDefaultInt(input.Duration, 60),
			)

			// Generate response
			resp, err := model.Generate(ctx,
				ai.NewGenerateRequest(
					&ai.GenerationCommonConfig{
						Temperature: 0.7,
					},
					ai.NewUserTextMessage(promptText),
				),
			)
			if err != nil {
				return nil, fmt.Errorf("SEO generation failed: %w", err)
			}

			// Parse JSON response
			responseText := resp.Text()
			var result models.SEOResponse
			if err := json.Unmarshal([]byte(responseText), &result); err != nil {
				return nil, fmt.Errorf("failed to parse SEO response: %w", err)
			}

			return &result, nil
		},
	)
}

func getOrDefault(value, defaultValue string) string {
	if value == "" {
		return defaultValue
	}
	return value
}

func getOrDefaultInt(value, defaultValue int) int {
	if value == 0 {
		return defaultValue
	}
	return value
}
