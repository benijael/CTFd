FROM python:3.11-slim-bookworm AS build
WORKDIR /opt/CTFd
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        git \
        curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g yarn \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY . /opt/CTFd
RUN pip install --no-cache-dir -r requirements.txt \
    && for d in CTFd/plugins/*; do \
        if [ -f "$d/requirements.txt" ]; then \
            pip install --no-cache-dir -r "$d/requirements.txt";\
        fi; \
    done;
# Build frontend assets
RUN yarn install && yarn build

FROM python:3.11-slim-bookworm AS release
WORKDIR /opt/CTFd
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libffi8 \
        libssl3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY --chown=1001:1001 . /opt/CTFd
RUN useradd \
    --no-log-init \
    --shell /bin/bash \
    -u 1001 \
    ctfd \
    && mkdir -p /var/log/CTFd /var/uploads \
    && chown -R 1001:1001 /var/log/CTFd /var/uploads /opt/CTFd \
    && chmod +x /opt/CTFd/docker-entrypoint.sh
COPY --chown=1001:1001 --from=build /opt/venv /opt/venv
# Copy compiled frontend assets from build stage
COPY --chown=1001:1001 --from=build /opt/CTFd/CTFd/themes/core/static /opt/CTFd/CTFd/themes/core/static
ENV PATH="/opt/venv/bin:$PATH"
USER 1001
EXPOSE 8000
ENTRYPOINT ["/opt/CTFd/docker-entrypoint.sh"]
