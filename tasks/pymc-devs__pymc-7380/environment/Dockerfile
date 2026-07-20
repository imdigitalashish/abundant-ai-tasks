FROM ubuntu:24.04

# Base system packages (common to all languages)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    patch \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 3.11+ runtime (project requires python_requires=">=3.11")
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    && rm -rf /var/lib/apt/lists/*

# uv for fast dependency installation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

# Clone repo at HEAD commit (with fix applied)
RUN git clone https://github.com/pymc-devs/pymc.git src && \
    cd src && \
    (git fetch --depth 1 origin e4a36eb7fffb0d47736f7b5846ae6508b665958b || git fetch --depth 1 origin "+refs/pull/7380/head:refs/remotes/origin/pr/7380") && \
    git checkout --detach FETCH_HEAD && \
    git submodule update --init --recursive

WORKDIR /app/src

ENV CI=true

# pymc's requirements.txt pulls pytensor from the moving "v3" branch HEAD, which
# has since renamed pytensor.tensor.random.var -> .variable (breaking the pinned
# pymc commit). Pin pytensor to the commit that was current when this pymc commit
# landed, install pymc without letting its deps re-resolve pytensor to branch HEAD,
# then install the remaining runtime/test dependencies (including jax/numpyro/
# blackjax needed by tests/sampling/test_jax.py) explicitly.
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python \
        "pytensor @ git+https://github.com/pymc-devs/pytensor.git@13419f0f8" && \
    uv pip install --python /opt/venv/bin/python -e . --no-deps && \
    uv pip install --python /opt/venv/bin/python \
        "arviz>=0.13.0,<1.0" "cachetools>=4.2.1,<7" cloudpickle "numpy>=1.25.0" \
        "pandas>=0.24.0" "rich>=13.7.1" "scipy>=1.13.0" "threadpoolctl>=3.1.0,<4.0.0" \
        "typing-extensions>=3.7.4" \
        pytest pytest-cov numdifftools "jax[cpu]" jaxlib numpyro blackjax fastprogress

ENV PATH="/opt/venv/bin:${PATH}"

# If install/build steps touched tracked files, reset them so bug.patch applies cleanly,
RUN git reset --hard

# Apply bug.patch to revert to buggy state (BASE)
COPY bug.patch /tmp/bug.patch
RUN patch -p1 < /tmp/bug.patch && rm /tmp/bug.patch

RUN rm -rf /app/src/.git

WORKDIR /app/src
