# SERPS Documentation Automation

This directory contains implementation-facing automation for generating dissertation and technical-report artefacts from the SERPS codebase.

Run the current documentation build with:

```bash
python scripts/docs/package_dissertation_assets.py
```

The pipeline currently generates:

- editable Mermaid sources for Chapter Three engineering diagrams;
- FastAPI OpenAPI JSON when the local service package is importable;
- an ER diagram derived from the SQLite schema definition;
- viva scenario catalog data derived from the implementation;
- screenshot and test-evidence plans for Chapter Four;
- Chapter Five evaluation summaries, CSV data, and SVG chart outputs derived from the viva scenario catalog;
- figure captions stored separately from the figures;
- a manifest with SERPS version, Git commit, generation timestamp, script name, and SHA-256 checksums.
- a packaged `dissertation_assets.zip` archive.

PNG/SVG rendering is optional and depends on Mermaid CLI (`mmdc`) being available locally. When the renderer is not installed, the pipeline records a limitation note instead of fabricating static images.

Private dissertation drafts, supervisor notes, and requirement documents must remain untracked. The public repository should contain implementation code, architecture documentation, generated technical artefacts, tests, and development records only.
