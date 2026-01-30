# 🚀 GitHub Actions Video Automation

Run your video automation from **GitHub's servers** - No IP blocking!

## Quick Setup (5 minutes)

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Name: `video-automation` (or any name)
3. **Privacy: PRIVATE** (important!)
4. Click "Create repository"

### Step 2: Add Your Gemini API Key

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `GEMINI_API_KEY`
4. Value: Your Gemini API key
5. Click **Add secret**

### Step 3: Push Your Code

Run these commands in your automation folder:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/video-automation.git
git push -u origin main
```

### Step 4: Run Video Generation!

1. Go to your repo → **Actions** tab
2. Click **Video Automation Runner** (left sidebar)
3. Click **Run workflow** (right side)
4. Fill in:
   - Video type: `character` or `info`
   - Idea: Your video concept
   - Scenes: Number of scenes
5. Click **Run workflow**

### Step 5: Download Your Video

1. Wait for workflow to complete (~30-60 min)
2. Click on the completed run
3. Scroll to **Artifacts**
4. Download `generated-video.zip`
5. Extract and enjoy your video!

---

## Benefits

| Feature | Benefit |
|---------|---------|
| **GitHub IP** | Microsoft Azure IPs - never blocked |
| **Free** | 2000 minutes/month free tier |
| **Reliable** | Professional cloud infrastructure |
| **Easy** | Just click "Run workflow" |

## Troubleshooting

- **Workflow not appearing?** Push code first, then refresh Actions tab
- **API error?** Check your GEMINI_API_KEY secret is set correctly
- **Timeout?** Reduce number of scenes to 3-4
