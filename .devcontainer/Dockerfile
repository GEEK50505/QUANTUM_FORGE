FROM mcr.microsoft.com/vscode/devcontainers/python:3.10

ARG USERNAME=vscode
ENV DEBIAN_FRONTEND=noninteractive

# Install OS packages and Node.js 20 via NodeSource (ensures npm/node compatibility)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg lsb-release build-essential git jq \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Ensure python command is available
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1 || true

WORKDIR /workspace

# Copy helper scripts into image for initial setup
COPY .devcontainer/postCreateCommand.sh /tmp/postCreateCommand.sh
COPY .devcontainer/postStartCommand.sh /tmp/postStartCommand.sh
RUN chmod +x /tmp/postCreateCommand.sh /tmp/postStartCommand.sh || true

# Install Python development tools
RUN pip install --upgrade pip \
    && pip install pylint black autopep8 pytest || true

USER vscode

CMD ["sleep", "infinity"]
