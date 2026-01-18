# Project: News Sentiment & 2nd Order Effect Analyzer

## The Goal
Build a pipeline that scrapes news/macro events and uses an LLM to deduce non-obvious market impacts (2nd and 3rd order effects).

## The Pipeline (Draft)
1.  **Ingest:** Scrape news sources (Bloomberg, Reuters, Twitter lists?) or use an API.
2.  **Analysis (The Core):**
    * Feed headline/article to LLM.
    * *Prompt Logic:* "Don't just say 'Oil up'. Ask: If Oil is up, what happens to Airlines? If Airlines down, what happens to Boeing suppliers? What happens to tourism stocks in Bali?"
3.  **Output:** A list of Tickers/Sectors with "Bullish/Bearish" confidence scores.

## Tech Stack
* **Scraper:** Python (`beautifulsoup` or `newsapi`).
* **Reasoning Engine:** Gemini 1.5 Pro (Good context) or DeepSeek R1 (Good at "thinking" steps).
* **Database:** Simple SQLite or JSON to track predictions vs reality.

## TODO
- [ ] Define the specific "Sources" list (which URLs?).
- [ ] Write the "2nd Order" Prompt template in `prompts.md`.
