#!/usr/bin/env bash
set -euo pipefail

ROOT=$(pwd)
TMPDIR=$(mktemp -d)
echo "Building pgmq in: $TMPDIR"
cd "$TMPDIR"

REPO=https://github.com/tembo-io/pgmq.git
echo "Cloning $REPO"
git clone "$REPO" pgmq || { echo "git clone failed"; exit 1; }
cd pgmq

echo "Repository layout:"
ls -la
echo

# Try building the native extension (where Makefile typically lives)
if [ -d pgmq-extension ]; then
  echo "Building pgmq-extension"
  cd pgmq-extension
  if make -n >/dev/null 2>&1; then
    make
    echo "Attempting 'make install' (may require sudo to install to system dirs)"
    mkdir -p "$TMPDIR/pgmq-staging"
    # Try to install into staging directory using DESTDIR if supported
    if make install DESTDIR="$TMPDIR/pgmq-staging" >/dev/null 2>&1; then
      echo "Installed into staging: $TMPDIR/pgmq-staging"
    else
      echo "make install did not support DESTDIR or failed, attempting regular make install (may need sudo)"
      sudo make install || true
    fi
    # If we produced a staging tree, copy it into the repo build context so
    # Docker can pick it up and include the native extension without compiling
    # inside the image.
    if [ -d "$TMPDIR/pgmq-staging" ]; then
      TARGET_DIR="$ROOT/deploy/docker/postgres-pgmq/pgmq-staging"
      echo "Copying staging artifacts to repo build context: $TARGET_DIR"
      rm -rf "$TARGET_DIR"
      mkdir -p "$TARGET_DIR"
      cp -a "$TMPDIR/pgmq-staging/." "$TARGET_DIR/"
      echo "Staging artifacts copied into repo: $TARGET_DIR"
    fi
  else
    echo "Make not available or no Makefile in pgmq-extension"
  fi
else
  echo "pgmq-extension directory not found; listing repo:(first two levels)"
  find . -maxdepth 2 -type f -print
fi

echo
echo "Build complete. Artifacts (if any) are in: $TMPDIR/pgmq-staging"
echo "You can inspect the staging dir and either copy files into a custom Docker image or run 'make install' on the host." 
echo "Temporary build dir left at: $TMPDIR (remove when done)"
