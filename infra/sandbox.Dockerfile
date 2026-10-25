# infra/sandbox.Dockerfile
# Lightweight, isolated test runner container for Coder specialist (T-40).
# Limits: non-root user, no host mounts, memory limit 1GB, cpu limit 1.5.

FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    NODE_VERSION=20.x

# Install base tools, git, node, and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install python test runners
RUN pip install --no-cache-dir pytest pytest-asyncio ruff

# Create sandbox user and workspace directory
RUN groupadd -g 1000 sandbox && \
    useradd -u 1000 -g sandbox -m -s /bin/bash sandbox && \
    mkdir -p /workspace && \
    chown -R sandbox:sandbox /workspace

USER sandbox
WORKDIR /workspace

CMD ["/bin/bash"]
