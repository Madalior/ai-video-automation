# Genkit AI Service - Setup Script
# This script helps you set up the Genkit Go microservice

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Genkit AI Service Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Node.js
Write-Host "[1/5] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check Go
Write-Host "[2/5] Checking Go..." -ForegroundColor Yellow
try {
    $goVersion = go version
    Write-Host "✓ Go found: $goVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Go not found. Please install Go 1.24+ from https://go.dev/dl/" -ForegroundColor Red
    exit 1
}

# Install Genkit CLI
Write-Host "[3/5] Installing Genkit CLI..." -ForegroundColor Yellow
try {
    npm install -g genkit
    Write-Host "✓ Genkit CLI installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Genkit CLI installation may have failed" -ForegroundColor Yellow
}

# Install Go dependencies
Write-Host "[4/5] Installing Go dependencies..." -ForegroundColor Yellow
cd "genkit-service"
go mod download
if ($?) {
    Write-Host "✓ Go dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install Go dependencies" -ForegroundColor Red
    exit 1
}

# Setup environment file
Write-Host "[5/5] Setting up environment..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file from template" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠ ACTION REQUIRED:" -ForegroundColor Yellow
    Write-Host "1. Get a FREE Google AI API key from: https://ai.google.dev/" -ForegroundColor White
    Write-Host "2. Edit genkit-service\.env and add your API key" -ForegroundColor White
    Write-Host "3. Run: go run main.go" -ForegroundColor White
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Get API key: https://ai.google.dev/" -ForegroundColor White
Write-Host "2. Edit: genkit-service\.env" -ForegroundColor White
Write-Host "3. Start service: cd genkit-service && go run main.go" -ForegroundColor White
Write-Host "4. Test with Python: python genkit-service\example_integration.py" -ForegroundColor White
Write-Host ""
