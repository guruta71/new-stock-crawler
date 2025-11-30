# Use a Python image with uv pre-installed
# Project uses Python 3.11
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Ensure installed tools can be executed out of the box
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Add virtual environment to PATH to use installed packages (like playwright)
ENV PATH="/app/.venv/bin:$PATH"

# Install Playwright browsers and system dependencies
# This must be done as root before switching user
RUN playwright install-deps \
    && playwright install chromium

# Then, add the rest of the project source code and install it
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Change ownership of the app directory to nonroot user
RUN chown -R nonroot:nonroot /app

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Use the non-root user to run our application
USER nonroot

# Default command
CMD ["crawler", "--help"]
