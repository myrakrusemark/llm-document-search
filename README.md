# 📃 llm-document-search 🔍
Experimental fast document processing and search using an LLM. The intention is to use this code in an autoGPT environment, boiling down a page to only the relevant information seeked by the LLM. By returning only the smallest amount of relevant information from a web page, token usage is minimized.

- Any loaded page is converted to raw text and split into overlapping content blocks.
- GPT-4 iterates over each block, and responds with "Yes" or "No" depending on whether the block is relevant to the search query.
- Matching blocks are returned.
- Block content overlaps in case relevant content spans multiple blocks

## Future enhancements
- Incorporate a confidence score to return only the most relevant results.
- Stitch together adjacent matching blocks to return a more complete result.
- Further pre-process text to condense meaning into smallest possible space. I don't like this very much though, given the arbitrary nature of general web browsing.

## Disadvantages
- Slow search process
- Costs money

## Advantages
- Low resource usage
- Extremely fast pre-processing
- Saves some overhead in not having to process or embed the entire page ahead of each search
- Pretty cheap!

## Features
- Cost Estimation
- Progress Indicator
