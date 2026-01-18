# AI Legend - Usage Guide

## Overview

**AI Legend** is an intelligent prompt generator that transforms your high-level goals into optimized, context-rich prompts for Antigravity. Think of it as your AI assistant's AI assistant!

## Quick Start

### 1. Install Dependencies
```bash
pip install rich pyperclip
```

### 2. Start Genkit Service (if not running)
```bash
cd genkit-service
go run main.go
```

The service should start on `http://localhost:3400`

### 3. Run AI Legend
```bash
python ai_legend.py "your goal here"
```

## Usage Examples

### Example 1: Fixing a Bug
```bash
python ai_legend.py "fix the parallel director bug"
```

**What AI Legend does:**
- Scans your codebase for files matching "parallel" and "director"
- Checks error logs for related issues
- Sends context to Genkit service for AI analysis
- Generates a structured prompt with:
  - Specific file references
  - Line numbers where issues exist
  - Step-by-step fix instructions
  - Verification steps

**Output Preview:**
```
╔══════════════════════════════════════════════════════════╗
║        AI LEGEND - Antigravity Prompt Generator          ║
╚══════════════════════════════════════════════════════════╝

ℹ Your Goal: fix the parallel director bug

⚙ Gathering codebase context...
✓ Content validation passed!

🎯 Context Understanding
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found parallel_director.py with AttributeError on lines 131, 
150, 153-154. Missing initialization of multi-worker generators.

📊 Estimated Complexity: MEDIUM

📁 Relevant Files:
  • flowchart/character/parallel_director.py
  • modules/generators/image_generator.py
  • modules/generators/video_generator.py

✨ OPTIMIZED PROMPT FOR ANTIGRAVITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I need to fix the AttributeError in `parallel_director.py`...
[Full optimized prompt with context]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Copied to clipboard! Paste to Antigravity.
✓ Saved to: prompts/history/2026-01-18_fix_parallel_director.md

✨ Done! Paste the prompt to Antigravity for best results.
```

### Example 2: Adding a New Feature
```bash
python ai_legend.py "add batch processing to info pipeline"
```

AI Legend will:
- Find all files related to "info" and "pipeline"
- Identify the character pipeline's parallel implementation as reference
- Generate a detailed feature request with:
  - Requirements breakdown
  - Reference implementations to copy from
  - Testing criteria

### Example 3: Optimization Task
```bash
python ai_legend.py "optimize video generation performance"
```

AI Legend generates a prompt that asks Antigravity to:
- Profile the current implementation
- Identify bottlenecks
- Suggest specific optimizations
- Provide benchmarking approach

## How It Works

### 1. Context Gathering
AI Legend's **CodebaseScanner** analyzes your project:
- **File Discovery**: Finds files matching keywords from your goal
- **Project Detection**: Identifies project type (video automation, web app, etc.)
- **Error Analysis**: Reads recent errors from `error_log.txt`
- **Structure Mapping**: Creates a directory tree of key components

### 2. AI Optimization
The gathered context is sent to your **Genkit Service**:
- Uses Gemini 1.5 Flash for intelligent analysis
- Applies Antigravity best practices (file references, structured steps)
- Estimates complexity (simple, medium, complex)
- Suggests relevant files to check

### 3. Output & Delivery
- **Rich Terminal Display**: Beautiful formatted output with colors and tables (via `rich`)
- **Clipboard Integration**: Auto-copies the prompt (via `pyperclip`)
- **History Tracking**: Saves all prompts to `prompts/history/` for reference

## Advanced Usage

### Custom Project Root
```bash
python ai_legend.py "goal" --project-root /path/to/project
```

### View Saved Prompts
All generated prompts are saved in `prompts/history/` with timestamps:
```
prompts/history/
├── 2026-01-18_092530_fix_parallel_director.md
├── 2026-01-18_093045_add_batch_processing.md
└── 2026-01-18_093812_optimize_performance.md
```

Each file includes:
- Original goal
- Context summary
- Complexity rating
- Relevant files list
- Full optimized prompt

## Benefits

### ⚡ Faster Workflow
Instead of manually typing context-heavy prompts, just state your goal:
- **Before**: "I need to fix a bug in parallel_director.py on lines 131, 150, 153-154 where self._multi_img_gen and..."
- **After**: `python ai_legend.py "fix parallel director bug"`

### 🎯 Better Results
AI Legend provides context that Antigravity needs:
- Specific file paths and line numbers
- Related files to check
- Clear step-by-step structure
- Proper verification steps

### 📚 Learning Tool
Review saved prompts to learn:
- How to structure effective AI requests
- What context is most valuable
- Patterns in successful prompts

## Troubleshooting

### "Genkit AI Service is not available"
**Solution**: Start the Genkit service first:
```bash
cd genkit-service
go run main.go
```

### "No module named 'rich'"
**Solution**: Install dependencies:
```bash
pip install rich pyperclip
```

### Clipboard not working
**Solution**: 
- **Windows**: Install `pywin32`: `pip install pywin32`
- **Linux**: Install `xclip` or `xsel`
- **macOS**: Should work out of the box

### No relevant files found
This is normal for very generic goals. Try being more specific:
- ❌ "improve code"
- ✅ "optimize video encoding in video_generator.py"

## Tips for Best Results

### 1. Be Specific but Concise
- ✅ "fix login timeout in browser_utils"
- ❌ "fix bug"
- ❌ "I want to fix the bug that occurs when the user tries to login and it times out after waiting too long"

### 2. Use Domain Keywords
Include technical terms from your project:
- "add caching to **Dreamina** generator"
- "parallelize **scene rendering** in **info pipeline**"

### 3. Trust the Process
AI Legend's context gathering means you don't need to provide all details upfront. Just state the goal!

### 4. Review History
Check `prompts/history/` to see what worked well for similar tasks.

## Integration with Workflow

### Typical Flow
```bash
# 1. State your goal
python ai_legend.py "add error recovery to video generator"

# 2. Review the generated prompt
# (displayed in terminal)

# 3. Paste to Antigravity
# (already in clipboard - just Ctrl+V)

# 4. Let Antigravity work
# It now has all the context it needs!

# 5. Reference history if needed
cat prompts/history/2026-01-18_*.md
```

## Examples of Great Goals

### Bug Fixes
- `"fix parallel director AttributeError"`
- `"resolve OTP timeout in login flow"`
- `"fix video encoding crash on scene 7"`

### Features
- `"add progress bar to video generation"`
- `"implement retry logic for API calls"`
- `"add Tamil language support to voiceover"`

### Optimization
- `"reduce memory usage in image processing"`
- `"speed up parallel video generation"`
- `"optimize database queries in dashboard"`

### Refactoring
- `"extract common code from orchestrators"`
- `"move browser utilities to shared module"`
- `"organize imports in character pipeline"`

## FAQ

**Q: Does it work offline?**  
A: No, it requires the Genkit service (which uses Gemini API).

**Q: Can I customize the prompt template?**  
A: Yes! Edit `genkit-service/prompts/antigravity_optimizer.prompt`

**Q: Does it support other languages?**  
A: Currently optimized for Python projects, but works with any text-based codebase.

**Q: How much does it cost?**  
A: Uses your existing Gemini API key. Each prompt optimization costs ~$0.001 (very cheap).

**Q: Can I use it for non-coding tasks?**  
A: Yes! Try: `python ai_legend.py "write technical documentation for video pipeline"`

## Next Steps

1. **Try it now**: `python ai_legend.py "your first goal"`
2. **Review saved prompts**: Check `prompts/history/` to see examples
3. **Share feedback**: What works? What could be better?

---

**Made with ❤️ to maximize Antigravity's potential**
