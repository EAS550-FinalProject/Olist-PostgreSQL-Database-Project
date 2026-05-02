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

## Phase 3 Additions

For the Streamlit application layer (`app/`), AI was used for:

- **Syntax assistance** — Streamlit caching decorators (`@st.cache_data`, `@st.cache_resource`), Altair chart spec syntax (mark_rect heatmaps, encoding shorthand), Render `render.yaml` Blueprint schema
- **Concept explanation** — Streamlit's multi-page convention (`pages/` discovery), `streamlit.testing.v1.AppTest` for headless execution, connection-pool sizing for serverless Postgres
- **Boilerplate generation** — initial scaffolding for the Streamlit pages, `.streamlit/config.toml`, `render.yaml`, and the smoke-test script

Sample Phase 3 prompts:

- "What's the difference between @st.cache_data and @st.cache_resource?"
- "How do I render a heatmap with cell labels in Altair?"
- "What does Render's render.yaml Blueprint schema look like for a Python web service?"
- "How do I write a smoke test for a Streamlit app without a real browser?"

All dashboard design choices (which KPIs, which segmentation thresholds, which charts to expose) and SQL query design were made by the team. AI did not generate the analytical SQL — those queries are reused from Phase 2 with team-authored modifications for parameterization.

## Phase 3 Polish (visual + UX pass)

Later in Phase 3 we used AI to help with the visual polish round:

- CSS for the sidebar brand block, hero cards, and insight callouts
- Picking the color palette (settled on a charcoal + ember red "Volcano" theme)
- Fixing the cohort heatmap (Altair color scale was washing everything out — got help on `clamp=True` and using the actual data range for `domain`)
- Wiring `st.page_link` to build a custom sidebar nav under the brand block

Sample prompts:

- "How do I put my own content above the auto-generated page nav in the Streamlit sidebar?"
- "Why is my Altair heatmap all white when values are between 0 and 1%?"
- "How do I add CSV download buttons next to a Streamlit dataframe?"
- "Which Streamlit config option hides the Deploy button in the top right?"

The actual UX decisions (which colors to pick, what insight text to show below each chart, which numbers became KPIs) were ours.

## Notes
- No AI tool was used to architect the entire pipeline or to write technical justification reports.
- All code was reviewed, tested, and understood by the team before committing.
