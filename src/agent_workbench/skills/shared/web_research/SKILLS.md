---
name: web_research
description: "Search and retrieve content from the web. Use when the user asks about current information, references a URL, or needs content from an online source. NOT for documents already attached to this conversation (use document_retrieval)."
---

# Web Research Skills

## scrape
Retrieve the full text content of a single known URL the user has referenced
explicitly. Use when a specific page URL is provided or implied.
NOT for topic searches (use search). NOT for structured data (use extract).

## search
Find and retrieve information about a topic when no specific URL is known.
Searches the web and returns synthesized results from top sources.
NOT when a URL is already known (use scrape).

## crawl
Retrieve content from a site and all its linked pages. Use when the user needs
comprehensive coverage of a domain or documentation site, not a single page.

## extract
Pull specific structured data from a known URL — prices, specs, tables, lists.
Use when the user asks for specific data points rather than prose content.
