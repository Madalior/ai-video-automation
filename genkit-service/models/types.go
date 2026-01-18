package models

// SEO Optimization Types
type SEORequest struct {
	Script         string `json:"script"`
	Niche          string `json:"niche"`
	TargetAudience string `json:"target_audience,omitempty"`
	Duration       int    `json:"duration,omitempty"`
}

type SEOResponse struct {
	Title         string   `json:"title"`
	Description   string   `json:"description"`
	Tags          []string `json:"tags"`
	Hashtags      []string `json:"hashtags"`
	ThumbnailText string   `json:"thumbnail_text"`
	Keywords      []string `json:"keywords"`
}

// Prompt Enhancement Types
type PromptEnhanceRequest struct {
	Prompt           string `json:"prompt"`
	Style            string `json:"style,omitempty"`
	CharacterContext string `json:"character_context,omitempty"`
}

type PromptEnhanceResponse struct {
	EnhancedPrompt string   `json:"enhanced_prompt"`
	Improvements   []string `json:"improvements"`
	StyleGuide     string   `json:"style_guide"`
}

// Quality Validation Types
type Scene struct {
	Duration    int    `json:"duration"`
	Narration   string `json:"narration"`
	VisualDesc  string `json:"visual_description"`
	Keywords    []string `json:"keywords,omitempty"`
}

type ValidationRequest struct {
	Script   string  `json:"script"`
	Scenes   []Scene `json:"scenes"`
	Duration int     `json:"duration"`
}

type ValidationIssue struct {
	SceneIndex int    `json:"scene_index"`
	Type       string `json:"type"`
	Message    string `json:"message"`
	Severity   string `json:"severity"`
	AutoFix    string `json:"auto_fix,omitempty"`
}

type ValidationResponse struct {
	IsValid bool              `json:"is_valid"`
	Issues  []ValidationIssue `json:"issues"`
	Summary string            `json:"summary"`
}

// Error Recovery Types
type ErrorRecoveryRequest struct {
	Error   string                 `json:"error"`
	Context map[string]interface{} `json:"context"`
	Prompt  string                 `json:"prompt,omitempty"`
}

type ErrorRecoveryResponse struct {
	Analysis        string   `json:"analysis"`
	Strategies      []string `json:"strategies"`
	FixedPrompt     string   `json:"fixed_prompt,omitempty"`
	Recommendations []string `json:"recommendations"`
}

// Niche Discovery Types
type NicheDiscoveryRequest struct {
	Category            string `json:"category"`
	CompetitionLevel    string `json:"competition_level,omitempty"`
	MonetizationPotential string `json:"monetization_potential,omitempty"`
}

type NicheInfo struct {
	Name                 string   `json:"name"`
	TrendScore           float64  `json:"trend_score"`
	Competition          string   `json:"competition"`
	EstimatedCPM         string   `json:"estimated_cpm"`
	KeywordVolume        string   `json:"keyword_volume"`
	WhyTrending          string   `json:"why_trending"`
	ContentIdeas         []string `json:"content_ideas"`
	TargetAudience       string   `json:"target_audience"`
	MonetizationPotential string  `json:"monetization_potential"`
}

type NicheDiscoveryResponse struct {
	TrendingNiches []NicheInfo `json:"trending_niches"`
	Analysis       string      `json:"analysis"`
}

// Prompt Optimizer Types
type CodebaseContext struct {
	Files         []string          `json:"files,omitempty"`
	OpenFiles     []string          `json:"open_files,omitempty"`
	ProjectType   string            `json:"project_type,omitempty"`
	RecentErrors  []string          `json:"recent_errors,omitempty"`
	DirectoryTree map[string]string `json:"directory_tree,omitempty"`
}

type PromptOptimizerRequest struct {
	Goal             string           `json:"goal"`
	CodebaseContext  CodebaseContext  `json:"codebase_context,omitempty"`
	AdditionalInfo   string           `json:"additional_info,omitempty"`
}

type PromptOptimizerResponse struct {
	OptimizedPrompt     string   `json:"optimized_prompt"`
	ContextSummary      string   `json:"context_summary"`
	RelevantFiles       []string `json:"relevant_files"`
	EstimatedComplexity string   `json:"estimated_complexity"`
}

// Generic API Response
type APIResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}
