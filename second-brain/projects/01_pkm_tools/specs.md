# Project: Local-First Second Brain

## Core Philosophy
1. **Source of Truth:** Local Markdown files (not SaaS, not Notion).
2. **Interface:** Chat-based, but grounded in files.
3. **No Cloud Lock-In:** No Telegram, No Discord.
4. **The "Loop":** An Agent periodically review past notes.

## Architecture Stack (Draft)
* **Storage:** Local Folder (`~/scratchpad/second-brain`)
* **Editor:** Neovim / SilverBullet
* **Sync:** Syncthing / Tailscale
* **Intelligence:** Remote API (Gemini/Groq) via Python Script
