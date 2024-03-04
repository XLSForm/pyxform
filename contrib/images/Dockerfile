ARG PYTHON_IMG_TAG
FROM python:${PYTHON_IMG_TAG}-slim-bookworm as base


FROM base as build
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "build-essential" \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /code
COPY ../../ ./
# Install with dev dependencies for tests
RUN pip install .[dev] \
    --user --no-warn-script-location --no-cache-dir


FROM base as runtime
ENV PATH="/root/.local/bin:$PATH"
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "openjdk-17-jdk" \
    && rm -rf /var/lib/apt/lists/*
# Copy Python deps from build to runtime
COPY --from=build \
    /root/.local \
    /root/.local
WORKDIR /code
ENTRYPOINT ["xlsform"]
