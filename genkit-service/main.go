package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"genkit-service/config"
	"genkit-service/flows"
	"genkit-service/models"

	"github.com/firebase/genkit/go/genkit"
	"github.com/firebase/genkit/go/plugins/googleai"
)

func main() {
	// Load configuration
	cfg := config.Load()
	if err := cfg.Validate(); err != nil {
		log.Fatal(err)
	}

	// Initialize Genkit with Google AI plugin
	ctx := context.Background()
	if err := googleai.Init(ctx, &googleai.Config{
		APIKey: cfg.GoogleAPIKey,
	}); err != nil {
		log.Fatalf("Failed to initialize Google AI: %v", err)
	}

	// Define all flows
	flows.DefineSEOFlow()
	flows.DefinePromptEnhanceFlow()
	flows.DefineQualityValidationFlow()
	flows.DefineErrorRecoveryFlow()
	flows.DefineNicheDiscoveryFlow()
	flows.DefinePromptOptimizerFlow()
	flows.DefineEmotionalScriptFlow()

	// Setup HTTP server
	mux := http.NewServeMux()

	// Health check endpoint
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{
			"status": "healthy",
			"service": "genkit-ai-service",
		})
	})

	// SEO Optimization endpoint
	mux.HandleFunc("/optimize-seo", enableCORS(handleSEO))

	// Prompt Enhancement endpoint
	mux.HandleFunc("/enhance-prompt", enableCORS(handlePromptEnhance))

	// Quality Validation endpoint
	mux.HandleFunc("/validate-content", enableCORS(handleValidation))

	// Error Recovery endpoint
	mux.HandleFunc("/recover-error", enableCORS(handleErrorRecovery))

	// Niche Discovery endpoint
	mux.HandleFunc("/discover-niches", enableCORS(handleNicheDiscovery))

	// Prompt Optimizer endpoint
	mux.HandleFunc("/optimize-antigravity-prompt", enableCORS(handlePromptOptimizer))

	// Emotional Script endpoint
	mux.HandleFunc("/enhance-script-emotions", enableCORS(handleEmotionalScript))

	// Start server
	addr := fmt.Sprintf(":%s", cfg.Port)
	log.Printf("🚀 Genkit AI Service starting on http://localhost%s", addr)
	log.Printf("📊 Genkit Developer UI: http://localhost:4000")
	log.Println("\nAvailable endpoints:")
	log.Println("  POST /optimize-seo - SEO optimization")
	log.Println("  POST /enhance-prompt - Prompt enhancement")
	log.Println("  POST /validate-content - Quality validation")
	log.Println("  POST /recover-error - Error recovery")
	log.Println("  POST /discover-niches - Niche discovery")
	log.Println("  POST /optimize-antigravity-prompt - Antigravity prompt optimization")
	log.Println("  POST /enhance-script-emotions - Emotional script generation")
	log.Println("  GET  /health - Health check")

	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal(err)
	}
}

// Handler functions
func handleSEO(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req models.SEORequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	flow := genkit.LookupFlow("optimize-seo")
	result, err := flow.Run(r.Context(), &req)
	if err != nil {
		log.Printf("SEO flow error: %v", err)
		sendError(w, err.Error(), http.StatusInternalServerError)
		return
	}

	sendSuccess(w, result)
}

func handlePromptEnhance(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req models.PromptEnhanceRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	flow := genkit.LookupFlow("enhance-prompt")
	result, err := flow.Run(r.Context(), &req)
	if err != nil {
		log.Printf("Prompt enhancement error: %v", err)
		sendError(w, err.Error(), http.StatusInternalServerError)
		return
	}

	sendSuccess(w, result)
}

func handleValidation(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req models.ValidationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	flow := genkit.LookupFlow("validate-content")
	result, err := flow.Run(r.Context(), &req)
	if err != nil {
		log.Printf("Validation error: %v", err)
		sendError(w, err.Error(), http.StatusInternalServerError)
		return
	}

	sendSuccess(w, result)
}

func handleErrorRecovery(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req models.ErrorRecoveryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	flow := genkit.LookupFlow("recover-error")
	result, err := flow.Run(r.Context(), &req)
	if err != nil {
		log.Printf("Error recovery error: %v", err)
		sendError(w, err.Error(), http.StatusInternalServerError)
		return
	}

	sendSuccess(w, result)
}

func handleNicheDiscovery(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req models.NicheDiscoveryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	flow := genkit.LookupFlow("discover-niches")
	result, err := flow.Run(r.Context(), &req)
	if err != nil {
		log.Printf("Niche discovery error: %v", err)
		sendError(w, err.Error(), http.StatusInternalServerError)
		return
	}

	sendSuccess(w, result)
}

func handlePromptOptimizer(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req models.PromptOptimizerRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	flow := genkit.LookupFlow("optimize-antigravity-prompt")
	result, err := flow.Run(r.Context(), &req)
	if err != nil {
		log.Printf("Prompt optimizer error: %v", err)
		sendError(w, err.Error(), http.StatusInternalServerError)
		return
	}

	sendSuccess(w, result)
}

func handleEmotionalScript(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req models.EmotionalScriptRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	flow := genkit.LookupFlow("enhance-script-emotions")
	result, err := flow.Run(r.Context(), &req)
	if err != nil {
		log.Printf("Emotional script error: %v", err)
		sendError(w, err.Error(), http.StatusInternalServerError)
		return
	}

	sendSuccess(w, result)
}

// Utility functions
func enableCORS(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next(w, r)
	}
}

func sendSuccess(w http.ResponseWriter, data interface{}) {
	response := models.APIResponse{
		Success: true,
		Data:    data,
	}
	json.NewEncoder(w).Encode(response)
}

func sendError(w http.ResponseWriter, message string, code int) {
	w.WriteHeader(code)
	response := models.APIResponse{
		Success: false,
		Error:   message,
	}
	json.NewEncoder(w).Encode(response)
}
