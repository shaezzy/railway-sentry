#!/bin/sh
set -e

# Ensure the relay config directory exists
mkdir -p /work/.relay

# Template the config file with environment variables
# SENTRY_WEB_INTERNAL_URL, KAFKA_BROKERS, and REDIS_URL must be set
envsubst < /work/.relay/config.template.yml > /work/.relay/config.yml

exec relay run
