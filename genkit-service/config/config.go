package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	GoogleAPIKey string
	Port         string
	Environment  string
}

func Load() *Config {
	// Load .env file if it exists
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using environment variables")
	}

	return &Config{
		GoogleAPIKey: getEnv("GOOGLE_API_KEY", ""),
		Port:         getEnv("PORT", "3400"),
		Environment:  getEnv("ENVIRONMENT", "development"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func (c *Config) Validate() error {
	if c.GoogleAPIKey == "" {
		log.Fatal("GOOGLE_API_KEY is required. Get one from https://ai.google.dev/")
	}
	return nil
}
