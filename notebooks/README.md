```markdown
# Notebooks (notebooks/) — UNDER ACTIVE DEVELOPMENT

Role:
- Interactive examples, tutorials, and exploratory experiments. Notebooks are *educational-first* and live examples of the platform's capabilities.

Guidelines:
- Keep notebooks small and focused. Use clear headings and short text explaining the experiment and expected outputs.
- Where notebooks are used for long-running experiments, extract core functionality into `ai/` or `backend/` modules so it can be tested.
- Mark notebooks with their purpose and the date.

Development status:
- Example notebooks are UNDER ACTIVE DEVELOPMENT; treat outputs as non-authoritative and for demo/education.

```
# Notebooks (notebooks/) — UNDER ACTIVE DEVELOPMENT

Jupyter notebooks used for interactive exploration, demonstrations, and lightweight experiments.

Guidelines:
- Keep notebooks focused and reproducible: pin random seeds and record environment information.
- Large datasets should not be committed; instead reference them in `data/` or external storage.
- Add a short README in each notebook subfolder describing purpose and kernel requirements.

Status: UNDER ACTIVE DEVELOPMENT
