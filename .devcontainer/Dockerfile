FROM mcr.microsoft.com/vscode/devcontainers/python:3.10

# Install Node.js
ARG NODE_VERSION="18"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# Install additional OS packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends curl ca-certificates gnupg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --upgrade pip \
    && pip install pylint black autopep8 pytest

# Install Node.js development tools
RUN su vscode -c "npm install -g npm@latest" 2>&1

USER vscode
