ARG SENTRY_IMAGE=ghcr.io/getsentry/sentry:nightly
FROM ${SENTRY_IMAGE}

RUN pip install https://github.com/getsentry/sentry-nodestore-s3/archive/main.zip

COPY . /usr/src/sentry

RUN if [ -s /usr/src/sentry/enhance-image.sh ]; then \
    /usr/src/sentry/enhance-image.sh; \
    fi

RUN if [ -s /usr/src/sentry/requirements.txt ]; then \
    echo "sentry/requirements.txt is deprecated, use sentry/enhance-image.sh - see https://develop.sentry.dev/self-hosted/#enhance-sentry-image"; \
    pip install -r /usr/src/sentry/requirements.txt; \
    fi

# On Railway there is no bind mount for ./sentry:/etc/sentry, so copy the
# config files directly into the image. entrypoint.sh is already provided
# by the base image at /docker-entrypoint.sh (sourced by /etc/sentry/entrypoint.sh).
RUN mkdir -p /etc/sentry
COPY sentry.conf.py /etc/sentry/sentry.conf.py
COPY config.yml /etc/sentry/config.yml
COPY entrypoint.sh /etc/sentry/entrypoint.sh
RUN chmod +x /etc/sentry/entrypoint.sh
