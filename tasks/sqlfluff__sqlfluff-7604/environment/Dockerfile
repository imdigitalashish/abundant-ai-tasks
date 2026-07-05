FROM ubuntu:24.04

# Base system packages (common to all languages)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    patch \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.12 (default in Ubuntu 24.04) and development headers
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

# Clone repo at HEAD commit (with fix applied)
RUN git clone https://github.com/sqlfluff/sqlfluff.git src && \
    cd src && \
    (git fetch --depth 1 origin 34f8ea04ac293cfc53edef7934205de9b6969f69 || git fetch --depth 1 origin "+refs/pull/7604/head:refs/remotes/origin/pr/7604") && \
    git checkout --detach FETCH_HEAD && \
    git submodule update --init --recursive

WORKDIR /app/src

ENV CI=true
ENV SQLFLUFF_TESTENV=1

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install sqlfluff in editable mode with dev dependencies, then the example plugin
RUN uv pip install -e . -r requirements_dev.txt && \
    uv pip install plugins/sqlfluff-plugin-example

# If install/build steps touched tracked files, reset them so bug.patch applies cleanly,
RUN git reset --hard

# Apply bug.patch to revert to buggy state (BASE)
COPY bug.patch /tmp/bug.patch
RUN patch -p1 < /tmp/bug.patch && rm /tmp/bug.patch

RUN rm -rf /app/src/.git

WORKDIR /app/src
