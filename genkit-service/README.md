# Genkit AI Service

AI-powered microservice for enhancing the video automation tool with 5 intelligent features.

## Features

🎯 **SEO Optimization** - Generate optimized titles, descriptions, tags for maximum YouTube visibility  
✨ **Prompt Enhancement** - Transform basic prompts into professional AI image generation prompts  
✅ **Quality Validation** - Catch content errors before expensive video production  
🔄 **Error Recovery** - Automatic failure handling with intelligent retry strategies  
📈 **Niche Discovery** - Find trending profitable video topics with data-driven insights

## Quick Start

### Prerequisites

- **Node.js 18+** (for Genkit CLI)
- **Go 1.24+**
- **Google AI API Key** (free from [https://ai.google.dev/](https://ai.google.dev/))

### Installation

```bash
# 1. Navigate to the service directory
cd "c:/Users/vijay/OneDrive/Pictures/automation tool/genkit-service"

# 2. Install Genkit CLI
npm install -g genkit

# 3. Install Go dependencies
go mod download

# 4. Setup environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Get Google AI API Key (FREE)

1. Visit [https://ai.google.dev/](https://ai.google.dev/)
2. Click "Get API Key"
3. Create a new API key in Google AI Studio
4. Copy the key to your `.env` file

**Free Tier**: 1,500 requests/day with Gemini 1.5 Flash

### Running the Service

```bash
# Start the service
go run main.go

# The service will start on http://localhost:3400
# Genkit Developer UI will be available at http://localhost:4000
```

## API Endpoints

### 1. SEO Optimization
```bash
POST /optimize-seo
```

**Request:**
```json
{
  "script": "Your video script...",
  "niche": "luxury travel",
  "target_audience": "affluent millennials",
  "duration": 60
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "7 Secret Luxury Destinations Billionaires Hide From You",
    "description": "Discover the world's most exclusive...",
    "tags": ["luxury travel", "exclusive destinations", ...],
    "hashtags": ["#LuxuryTravel", "#ExclusiveDestinations"],
    "thumbnail_text": "BILLIONAIRES ONLY",
    "keywords": ["luxury vacations", "high-end travel", ...]
  }
}
```

### 2. Prompt Enhancement
```bash
POST /enhance-prompt
```

**Request:**
```json
{
  "prompt": "woman in hotel lobby",
  "style": "cinematic",
  "character_context": "25yo, long brown hair, green eyes"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "enhanced_prompt": "Elegant woman, 25 years old, long flowing brown hair, striking green eyes, standing in a luxurious hotel lobby, marble floors, golden chandelier lighting, photorealistic, cinematic composition, shot on Sony A7IV with 85mm f/1.8, shallow depth of field, warm color grading, 8K ultra-detailed",
    "improvements": ["Added specific age and features", "Included lighting details", ...],
    "style_guide": "Maintain cinematic look with warm tones..."
  }
}
```

### 3. Quality Validation
```bash
POST /validate-content
```

**Request:**
```json
{
  "script": "Complete script text...",
  "scenes": [
    {
      "duration": 8,
      "narration": "Welcome to luxury travel...",
      "visual_description": "Woman at beach resort",
      "keywords": ["luxury", "beach"]
    }
  ],
  "duration": 60
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "is_valid": false,
    "issues": [
      {
        "scene_index": 3,
        "type": "timing",
        "message": "Narration too long (12s) for 8s scene",
        "severity": "warning",
        "auto_fix": "Shorten narration to: '...'"
      }
    ],
    "summary": "Found 3 issues: 1 critical, 2 warnings"
  }
}
```

### 4. Error Recovery
```bash
POST /recover-error
```

**Request:**
```json
{
  "error": "Request timeout",
  "context": {
    "service": "dreamina",
    "scene_index": 3,
    "attempt": 1
  },
  "prompt": "woman at night city skyline"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis": "Timeout likely due to complex scene with many details",
    "strategies": [
      "Simplify prompt to reduce generation time",
      "Retry with exponential backoff",
      "Split into simpler elements"
    ],
    "fixed_prompt": "woman standing, city lights background at night",
    "recommendations": [
      "Reduce scene complexity for night scenes",
      "Add timeout buffer for city scenes"
    ]
  }
}
```

### 5. Niche Discovery
```bash
POST /discover-niches
```

**Request:**
```json
{
  "category": "lifestyle",
  "competition_level": "low",
  "monetization_potential": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "trending_niches": [
      {
        "name": "Quiet Luxury Fashion",
        "trend_score": 8.5,
        "competition": "medium",
        "estimated_cpm": "$12-18",
        "keyword_volume": "50K/month",
        "why_trending": "Viral on TikTok, low YouTube competition",
        "content_ideas": [
          "10 Quiet Luxury Brands You Need to Know",
          "How to Dress Like Old Money"
        ],
        "target_audience": "Fashion-conscious millennials",
        "monetization_potential": "High - luxury brand partnerships"
      }
    ],
    "analysis": "Lifestyle category shows strong growth..."
  }
}
```

## Python Integration

### Import the Client

```python
from modules.genkit_client import genkit

# The client automatically connects to localhost:3400
```

### Example Usage

```python
# SEO Optimization
seo = genkit.optimize_seo(
    script=video_script,
    niche="luxury travel"
)
print(f"Title: {seo['title']}")

# Prompt Enhancement
enhanced = genkit.enhance_prompt(
    prompt="woman at beach",
    style="cinematic"
)
improved_prompt = enhanced['enhanced_prompt']

# Quality Validation
validation = genkit.validate_content(
    script=script,
    scenes=scenes,
    duration=60
)
if not validation['is_valid']:
    print(f"Issues found: {validation['summary']}")

# Error Recovery
recovery = genkit.recover_error(
    error=str(exception),
    context={'service': 'dreamina', 'scene': 3}
)
for strategy in recovery['strategies']:
    print(f"Try: {strategy}")

# Niche Discovery
niches = genkit.discover_niches(
    category="lifestyle",
    competition_level="low"
)
for niche in niches['trending_niches']:
    print(f"{niche['name']}: {niche['trend_score']}/10")
```

## Integration with Automation Tool

The Genkit service works alongside your existing Python automation tool:

```
Your Python Tool                Genkit Go Service
    ↓                                 ↓
1. Generate script         →    [Validate content]
    ↓                                 ↓
2. Create prompts          →    [Enhance prompts]
    ↓                                 ↓
3. Generate images              (Better quality)
    ↓                                 ↓
4. Handle errors           →    [Auto recovery]
    ↓                                 ↓
5. Upload video            →    [Optimize SEO]
    ↓
   Done!
```

## Development

### View Logs
```bash
# Start with verbose logging
go run main.go

# Logs show each request:
# 2026/01/17 09:00:00 POST /optimize-seo - 200 OK (1.2s)
```

### Genkit Developer UI

Access at [http://localhost:4000](http://localhost:4000) to:
- Test flows interactively
- View request traces
- Monitor performance
- Debug prompts

## Cost Estimation

**Using Gemini 1.5 Flash (Recommended)**:
- FREE tier: 1,500 requests/day
- Paid: ~$0.075 per 1M input tokens

**Typical costs**:
- SEO optimization: ~2,000 tokens = $0.0002
- Prompt enhancement: ~1,000 tokens = $0.0001
- Quality validation: ~3,000 tokens = $0.0003

**100 videos/day**: ~$0.05/day = **$1.50/month** (well within free tier)

## Troubleshooting

**Service won't start?**
- Check Go version: `go version` (must be 1.24+)
- Verify API key in `.env`
- Check port 3400 is available

**Python client can't connect?**
- Make sure Genkit service is running
- Check firewall isn't blocking localhost:3400
- Verify no other service using port 3400

**AI responses are slow?**
- Using Gemini Flash (fast): 1-3 seconds
- Using Gemini Pro (slower): 3-8 seconds
- Check your internet connection

## License

Part of the automation tool project.
