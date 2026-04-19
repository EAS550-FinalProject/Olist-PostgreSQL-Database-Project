# Generative AI Disclosure

In line with the course's Generative AI Policy, this document discloses the use of AI tools during the development of this project.

## Tool Used
- **Claude** (Anthropic)
- **ChatGPT** (OpenAI)

## Tasks Assisted
AI was used for the following permitted purposes:

- **Syntax assistance** — SQL syntax (CTEs, window functions), dbt Jinja templating, YAML formatting for GitHub Actions and dbt configs
- **Concept explanation** — clarifying concepts like star schema design, dbt materialization strategies, SQLFluff rules, and PostgreSQL EXPLAIN ANALYZE output
- **Boilerplate generation** — initial scaffolding for dbt model files, CI workflow YAML, and SQLFluff configuration

All architectural decisions, query design, schema modeling choices, and technical justifications were made by the team.

## Sample Prompts
- "What's the correct Jinja syntax for referencing a source table in dbt?"
- "Explain what ST06 rule in SQLFluff checks for"
- "How do I write a window function to calculate a rolling average in PostgreSQL?"
- "Show me the YAML format for adding an env variable to a GitHub Actions step"
- "What does 'Parallel Seq Scan' mean in EXPLAIN ANALYZE output?"

## Notes
- No AI tool was used to architect the entire pipeline or to write technical justification reports.
- All code was reviewed, tested, and understood by the team before committing.
