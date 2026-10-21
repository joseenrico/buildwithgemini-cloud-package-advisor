# My agent: Cloud Package Advisor
One-liner: A conversational agent that helps developers and engineering leads select optimal cloud VM packages from a dummy local catalog priced in IDR, compare them against comparable hyperscaler packages priced in USD converted via live exchange rates, and visualize the recommended architecture.

Tool coverage:
- Memory: User's budget constraint, preferred tech stack/OS, and previous sizing inquiries across sessions
- Tools: Dummy local catalog search (`query_cloud_catalog`), live exchange rate fetch (`get_usd_to_idr_rate`), and side-by-side cost conversion
- Catalog/UI: Catalog of cloud VM packages priced in IDR (local provider) with comparable hyperscaler equivalents priced in USD, rendered as side-by-side comparison tables and cards
- Image gen: Illustrative architecture/infrastructure diagram of the recommended cloud setup
- Sandbox: Cost projection calculations (monthly/annual run-rate comparison in IDR, converting hyperscaler USD prices with live rate)

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for multi-tier cost calculations and live currency exchange API lookup
