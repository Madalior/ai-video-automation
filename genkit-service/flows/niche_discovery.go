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

var nicheDiscoveryFlow *genkit.Flow[*models.NicheDiscoveryRequest, *models.NicheDiscoveryResponse, struct{}]

// DefineNicheDiscoveryFlow creates the niche discovery flow
func DefineNicheDiscoveryFlow() {
	nicheDiscoveryFlow = genkit.DefineFlow(
		"discover-niches",
		func(ctx context.Context, input *models.NicheDiscoveryRequest) (*models.NicheDiscoveryResponse, error) {
			model := googleai.Model("gemini-1.5-flash-latest")

			promptText := fmt.Sprintf(`You are a YouTube trend analyst and content strategist with deep knowledge of viral content and monetization.

Category: %s
Preferred Competition Level: %s
Monetization Potential: %s

Discover trending niches within this category suitable for automated AI video production (January 2026).

Analysis Framework:
1. Current Trends: What's trending NOW, emerging topics, seasonal opportunities
2. Competition: Low (<1K channels), Medium (1-10K), High (>10K)
3. Monetization: Estimated CPM, sponsor interest, affiliate opportunities
4. Content Viability: Can be produced with AI images/videos, stock footage availability
5. Audience: Target demographic, engagement potential, share-ability

For each niche provide:
- name: Clear niche name
- trend_score: 1-10 rating
- competition: "low", "medium", "high"
- estimated_cpm: "$X-Y"
- keyword_volume: "XK/month"
- why_trending: Brief explanation
- content_ideas: [3-5 specific video ideas]
- target_audience: Who watches this
- monetization_potential: Revenue opportunities

Return ONLY valid JSON with 5-10 niches ranked by opportunity:
{
  "trending_niches": [
    {
      "name": "string",
      "trend_score": 8.5,
      "competition": "low",
      "estimated_cpm": "$12-18",
      "keyword_volume": "50K/month",
      "why_trending": "string",
      "content_ideas": ["idea 1", "idea 2"],
      "target_audience": "string",
      "monetization_potential": "string"
    }
  ],
  "analysis": "overall analysis"
}

Focus on niches that are:
- Trending NOW (not outdated)
- Suitable for AI video production
- Have clear monetization paths
- Realistic to succeed in`,
				input.Category,
				getOrDefaultNiche(input.CompetitionLevel, "any"),
				getOrDefaultNiche(input.MonetizationPotential, "any"),
			)

			resp, err := model.Generate(ctx,
				ai.NewGenerateRequest(
					&ai.GenerationCommonConfig{
						Temperature: 0.7,
					},
					ai.NewUserTextMessage(promptText),
				),
			)
			if err != nil {
				return nil, fmt.Errorf("niche discovery failed: %w", err)
			}

			var result models.NicheDiscoveryResponse
			if err := json.Unmarshal([]byte(resp.Text()), &result); err != nil {
				return nil, fmt.Errorf("failed to parse niche response: %w", err)
			}

			return &result, nil
		},
	)
}

func getOrDefaultNiche(value, defaultValue string) string {
	if value == "" {
		return defaultValue
	}
	return value
}
