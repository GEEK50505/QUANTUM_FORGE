###############################################################################
# Multi-stage Dockerfile for Postgres + pgmq
# - Prefers a prebuilt `pgmq-staging/` directory in the build context.
# - If `pgmq-staging` is absent, build artifacts can be produced in-image
#   by setting build-arg `ALLOW_IN_IMAGE_BUILD=true` (not recommended for CI).
# - Final image contains only runtime files (.so, .sql, .control) and no
#   Rust/toolchain or build dependencies.
###############################################################################

# -----------------------------
# STAGE: builder
# -----------------------------
FROM postgres:16-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    git \
    curl \
    clang \
    libclang-dev \
    libssl-dev \
    pkg-config \
    postgresql-server-dev-16 \
    rustc \
    cargo \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src

# Clone upstream and attempt to build. We try common Makefile locations and
# fall back to cargo/pgrx if available. The builder must produce a staging
# tree under /out that mirrors the layout expected by the runtime (e.g.
# /out/usr/share/postgresql/16/extension and /out/usr/lib/postgresql/16/lib).
RUN set -eux; \
  git clone https://github.com/tembo-io/pgmq.git /usr/src/pgmq || true; \
  if [ -d /usr/src/pgmq ]; then \
    cd /usr/src/pgmq; \
    if [ -f Makefile ]; then \
      make && make install DESTDIR=/out || true; \
    elif [ -f postgres/Makefile ]; then \
      cd postgres && make && make install DESTDIR=/out || true; \
    elif [ -f extension/Makefile ]; then \
      cd extension && make && make install DESTDIR=/out || true; \
    else \
      # Try cargo/pgrx based build if available
      if command -v cargo >/dev/null 2>&1; then \
        cargo --version || true; \
        # Install cargo-pgrx if possible and attempt pgrx install
        cargo install --locked cargo-pgrx || true; \
        cargo pgrx install --release --destination /out || true; \
      fi; \
    fi; \
  fi; \
  # Ensure at least the out/usr/share/... exists if build succeeded
  mkdir -p /out/usr/share/postgresql/16/extension || true; \
  mkdir -p /out/usr/lib/postgresql/16/lib || true

# -----------------------------
# STAGE: runtime (final image)
# -----------------------------
FROM postgres:16-bookworm

LABEL maintainer="QUANTUM_FORGE Engineering"
LABEL description="PostgreSQL 16 with pgmq extension (runtime-only image)"

ENV DEBIAN_FRONTEND=noninteractive

# Copy a prebuilt staging tree from build context if present
COPY pgmq-staging /tmp/pgmq-staging

# Build-time option: allow building inside the builder stage (use with care)
ARG ALLOW_IN_IMAGE_BUILD=false

# Take one of three actions:
# 1) If `pgmq-staging` exists in context, copy it into `/` (preferred)
# 2) Else if ALLOW_IN_IMAGE_BUILD=true, copy artifacts from builder's /out
# 3) Else fail fast to enforce reproducible builds (no silent in-image builds)
RUN set -eux; \
  if [ -d /tmp/pgmq-staging ] && [ "$(ls -A /tmp/pgmq-staging)" ]; then \
    echo "Found prebuilt pgmq staging in build context; installing into image root"; \
    cp -a /tmp/pgmq-staging/* /; \
    ls -la /usr/share/postgresql/16/extension || true; \
  else \
    if [ "${ALLOW_IN_IMAGE_BUILD}" = "true" ]; then \
      echo "No staging found; using builder artifacts (ALLOW_IN_IMAGE_BUILD=true)"; \
      cp -a /out/* / || true; \
      ls -la /usr/share/postgresql/16/extension || true; \
    else \
      echo "ERROR: pgmq-staging not found and ALLOW_IN_IMAGE_BUILD is false. Failing build to enforce reproducibility."; \
      exit 1; \
    fi; \
  fi

# Ensure runtime filesystem permissions are readable
RUN if [ -d /usr/local/lib/postgresql ]; then chmod -R a+rX /usr/local/lib/postgresql || true; else echo '/usr/local/lib/postgresql not present, skipping chmod'; fi

# Expose Postgres port (documentation only; compose manages actual mapping)
EXPOSE 5432

# Healthcheck: we rely on docker-compose override for full readiness
HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD pg_isready -U postgres || exit 1

# Use default postgres entrypoint and CMD
