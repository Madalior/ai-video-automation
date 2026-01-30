# GitHub Upload Instructions

## Step 1: Create GitHub Repository

1. Go to https://github.com
2. Click "New Repository" or go to https://github.com/new
3. Repository settings:
   - **Name**: `ai-video-automation`
   - **Description**: `AI-powered video automation with Veo 3.1 consistency`
   - **Visibility**: Public or Private
   - **DO NOT** initialize with README (we have one)
4. Click "Create repository"

## Step 2: Connect Local to GitHub

GitHub will show you commands. Use these:

```bash
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/ai-video-automation.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username!

## Step 3: Verify Upload

1. Go to your repository: `https://github.com/YOUR_USERNAME/ai-video-automation`
2. Check all files are uploaded
3. README.md should display automatically

## Alternative: GitHub Desktop

If you prefer GUI:

1. Download GitHub Desktop: https://desktop.github.com/
2. Open GitHub Desktop
3. File → Add Local Repository
4. Select: `c:\Users\vijay\OneDrive\Pictures\automation tool`
5. Publish repository to GitHub

## Quick Commands

```powershell
cd "c:\Users\vijay\OneDrive\Pictures\automation tool"

# Check status
git status

# Add remote (replace YOUR_USERNAME!)
git remote add origin https://github.com/YOUR_USERNAME/ai-video-automation.git

# Push to GitHub
git push -u origin main
```

## After Upload

Your repository will be available at:
`https://github.com/YOUR_USERNAME/ai-video-automation`

Share this link with others!

## Future Updates

After making changes:

```bash
git add .
git commit -m "Description of changes"
git push
```

## Troubleshooting

**Authentication required:**
- Use personal access token instead of password
- Generate at: https://github.com/settings/tokens

**Remote already exists:**
```bash
git remote remove origin
git remote add origin YOUR_REPO_URL
```

**Large files:**
- Already excluded in .gitignore
- Videos, outputs, and caches won't be uploaded

## Files Prepared

✅ `.gitignore` - Excludes outputs and sensitive data
✅ `README.md` - Project documentation
✅ Git initialized
✅ Initial commit created

**Ready to push to GitHub!** 🚀
