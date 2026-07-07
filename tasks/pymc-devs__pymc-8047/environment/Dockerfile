FROM ubuntu:24.04

# Base system packages (common to all languages)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    patch \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python (Ubuntu 24.04 ships Python 3.12, which satisfies pymc's requirements)
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

# Clone repo at HEAD commit (with fix applied)
RUN git clone https://github.com/pymc-devs/pymc.git src && \
    cd src && \
    (git fetch --depth 1 origin b2b019b47621b59de055df102da77b6bafafbcfe || git fetch --depth 1 origin "+refs/pull/8047/head:refs/remotes/origin/pr/8047") && \
    git checkout --detach FETCH_HEAD && \
    git submodule update --init --recursive

WORKDIR /app/src

ENV CI=true
ENV PATH="/opt/venv/bin:${PATH}"

# Install pymc and its test dependencies into a venv.
# arviz>=1.0 is a major rewrite that drops APIs (e.g. arviz.concat) still used
# by this version of pymc, so pin it below 1.0 to match the supported range.
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python -e . "arviz<1.0" pytest pytest-cov

# If install/build steps touched tracked files, reset them so bug.patch applies cleanly,
RUN git reset --hard

# Apply bug.patch to revert to buggy state (BASE)
COPY bug.patch /tmp/bug.patch
RUN patch -p1 < /tmp/bug.patch && rm /tmp/bug.patch

RUN rm -rf /app/src/.git

WORKDIR /app/src
