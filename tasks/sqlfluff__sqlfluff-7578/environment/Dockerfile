FROM ubuntu:24.04

# Base system packages (common to all languages)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    patch \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python runtime
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

# Clone repo at HEAD commit (with fix applied)
RUN git clone https://github.com/sqlfluff/sqlfluff.git src && \
    cd src && \
    (git fetch --depth 1 origin faff0a02c7f3f09b97799abb859dd6bbf5faa1c2 || git fetch --depth 1 origin "+refs/pull/7578/head:refs/remotes/origin/pr/7578") && \
    git checkout --detach FETCH_HEAD && \
    git submodule update --init --recursive

WORKDIR /app/src

ENV CI=true

# Create venv and install sqlfluff (editable) plus the test/dev dependencies
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python -e . && \
    uv pip install --python /opt/venv/bin/python pytest pytest-xdist hypothesis
ENV PATH="/opt/venv/bin:${PATH}"

# If install/build steps touched tracked files, reset them so bug.patch applies cleanly,
RUN git reset --hard

# Apply bug.patch to revert to buggy state (BASE)
COPY bug.patch /tmp/bug.patch
RUN patch -p1 < /tmp/bug.patch && rm /tmp/bug.patch

RUN rm -rf /app/src/.git

WORKDIR /app/src
