ARG RELAY_IMAGE=ghcr.io/getsentry/relay:nightly
FROM ${RELAY_IMAGE}

USER root
RUN apt-get update && apt-get install -y --no-install-recommends gettext-base && rm -rf /var/lib/apt/lists/*

COPY config.template.yml /work/.relay/config.template.yml
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER relay
ENTRYPOINT ["/entrypoint.sh"]
