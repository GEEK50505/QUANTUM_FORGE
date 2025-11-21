# VS Code Extensions and Development Tools

This directory contains configuration and support files for VS Code extensions used in the development workflow. These tools enhance the development experience but are not part of the main QUANTUM_FORGE platform.

## Directory Structure

- `cline/` - Configuration for Cline extension
- `roo/` - Configuration for Roo Code extension
- `vscode/` - VS Code workspace settings and launch configurations

## Extension Setup

### Roo Code
- Key management and testing scripts are in `.devtools/scripts/`
- Configuration templates are provided in `vscode/settings.json.example`

### Cline
- Memory bank and rules for code assistance
- Configuration files for maintaining development context

## Important Notes

1. These tools are for development workflow only
2. Do not commit sensitive API keys or tokens
3. Use example files as templates for your local setup
4. Keep extension configurations separate from platform code