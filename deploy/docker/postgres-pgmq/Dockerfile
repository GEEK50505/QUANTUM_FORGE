FROM postgres:16

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ca-certificates \
    postgresql-server-dev-16 \
    cargo \
    rustc \
    pkg-config \
    libreadline-dev \
    zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

# If a prebuilt staging tree is provided in the build context at
# `pgmq-staging/`, copy it into the image and install the files directly.
# This allows building the native extension on the host and then including
# it in the image without requiring the image build to compile sources.
COPY pgmq-staging /tmp/pgmq-staging
RUN if [ -d /tmp/pgmq-staging ] && [ "$(ls -A /tmp/pgmq-staging)" ]; then \
      echo "Found prebuilt pgmq staging in build context, copying into filesystem root"; \
        cp -a /tmp/pgmq-staging/* /; \
        ls -la /usr/share/postgresql/16/extension || true; \
    else \
      echo "No prebuilt staging present, will build from source"; \
    fi

# Clone and build pgmq; try common locations for Makefile to support
# repository layout changes. If no Makefile is found, print a tree
# to help debugging.
RUN bash -lc "if [ -d /tmp/pgmq-staging ] && [ \"$(ls -A /tmp/pgmq-staging)\" ]; then echo 'Prebuilt staging found; skipping source build'; else git clone https://github.com/tembo-io/pgmq.git /tmp/pgmq && cd /tmp/pgmq && \
  if [ -f Makefile ]; then \
    echo 'Found Makefile at repo root - running make'; \
    make && make install; \
  elif [ -f postgres/Makefile ]; then \
    echo 'Found Makefile at postgres/ - running make there'; \
    cd postgres && make && make install; \
  elif [ -f extension/Makefile ]; then \
    echo 'Found Makefile at extension/ - running make there'; \
    cd extension && make && make install; \
  elif [ -f pgmq-extension/Makefile ]; then \
    echo 'Found Makefile at pgmq-extension/ - running make there'; \
    cd pgmq-extension && make && make install; \
  elif [ -f src/Makefile ]; then \
    echo 'Found Makefile at src/ - running make there'; \
    cd src && make && make install; \
  else \
    echo 'No Makefile found in pgmq repo; printing listing for debugging'; \
    ls -la /tmp/pgmq || true; \
    find /tmp/pgmq -maxdepth 2 -type f -print || true; \
    false; \
  fi && rm -rf /tmp/pgmq; fi"

# Ensure permissions and cleanup
RUN if [ -d /usr/local/lib/postgresql ]; then chmod -R a+rX /usr/local/lib/postgresql || true; else echo '/usr/local/lib/postgresql not present, skipping chmod'; fi

# Use default postgres entrypoint/cmd
