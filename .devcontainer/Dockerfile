FROM mcr.microsoft.com/vscode/devcontainers/python:3.10

# Lightweight additions for Node support and common tooling.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER vscode
