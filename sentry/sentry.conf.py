# This file is just Python, with a touch of Django which means
# you can inherit and tweak settings to your hearts content.

from sentry.conf.server import *  # NOQA

import urllib.parse as _urlparse

BYTE_MULTIPLIER = 1024
UNITS = ("K", "M", "G")


def unit_text_to_bytes(text):
    unit = text[-1].upper()
    power = UNITS.index(unit) + 1
    return float(text[:-1]) * (BYTE_MULTIPLIER**power)


# Generously adapted from pynetlinux: https://github.com/rlisagor/pynetlinux/blob/e3f16978855c6649685f0c43d4c3fcf768427ae5/pynetlinux/ifconfig.py#L197-L223
INTERNAL_SYSTEM_IPS = ()

###########
# Database #
###########

# On Railway, DATABASE_URL is provided by the managed Postgres plugin.
# Falls back to individual env vars for non-Railway deployments.
_database_url = env("DATABASE_URL", "")
if _database_url:
    _db = _urlparse.urlparse(_database_url)
    DATABASES = {
        "default": {
            "ENGINE": "sentry.db.postgres",
            "NAME": _db.path.lstrip("/") or "postgres",
            "USER": _db.username or "postgres",
            "PASSWORD": _db.password or "",
            "HOST": _db.hostname or "localhost",
            "PORT": str(_db.port or ""),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "sentry.db.postgres",
            "NAME": env("POSTGRES_DB", "postgres"),
            "USER": env("POSTGRES_USER", "postgres"),
            "PASSWORD": env("POSTGRES_PASSWORD", ""),
            "HOST": env("POSTGRES_HOST", "pgbouncer"),
            "PORT": env("POSTGRES_PORT", ""),
        }
    }

# If you're expecting any kind of real traffic on Sentry, we highly recommend
# configuring the CACHES and Redis settings

###########
# General #
###########

# Instruct Sentry that this install intends to be run by a single organization
# and thus various UI optimizations should be enabled.
SENTRY_SINGLE_ORGANIZATION = True
SENTRY_RELAY_OPEN_REGISTRATIONS = True

# Sentry event retention days specifies how long events are retained in the database.
# This should be set on your `.env` or `.env.custom` file, instead of modifying
# the value here.
# NOTE: The longer the days, the more disk space is required.
SENTRY_OPTIONS["system.event-retention-days"] = int(
    env("SENTRY_EVENT_RETENTION_DAYS", "90")
)

# The secret key is being used for various cryptographic operations, such as
# generating a CSRF token, session token, and registering Relay instances.
# The secret key value should be set on your `.env` or `.env.custom` file
# instead of modifying the value here.
#
# If the key ever becomes compromised, it's important to generate a new key.
# Changing this value will result in all current sessions being invalidated.
# A new key can be generated with `$ sentry config generate-secret-key`
if env("SENTRY_SYSTEM_SECRET_KEY"):
    SENTRY_OPTIONS["system.secret-key"] = env("SENTRY_SYSTEM_SECRET_KEY", "")

# Set the public URL prefix from env (Railway provides RAILWAY_PUBLIC_DOMAIN).
if env("SENTRY_SYSTEM_URL_PREFIX"):
    SENTRY_OPTIONS["system.url-prefix"] = env("SENTRY_SYSTEM_URL_PREFIX")

# Self-hosted Sentry infamously has a lot of Docker containers required to make
# all the features work. Oftentimes, users don't use the full feature set that
# requires all the containers. This is a way to enable only the error monitoring
# feature which also reduces the amount of containers required to run Sentry.
#
# To make Sentry work with all features, set `COMPOSE_PROFILES` to `feature-complete`
# in your `.env` file. To enable only the error monitoring feature, set
# `COMPOSE_PROFILES` to `errors-only`.
#
# See https://develop.sentry.dev/self-hosted/optional-features/errors-only/
SENTRY_SELF_HOSTED_ERRORS_ONLY = env("COMPOSE_PROFILES") != "feature-complete"

# When running in an air-gapped environment, set this to True to entirely disable
# external network calls and features that require Internet connectivity.
#
# Setting the value to False while running in an air-gapped environment will
# cause some containers to raise exceptions. One known example is fetching
# AI model prices from various public APIs.
SENTRY_AIR_GAP = False

################
# Node Storage #
################

# Sentry uses an abstraction layer called "node storage" to store raw events.
# Previously, it used PostgreSQL as the backend, but this didn't scale for
# high-throughput environments. Read more about this in the documentation:
# https://develop.sentry.dev/backend/application-domains/nodestore/
#
# Through this setting, you can use the provided blob storage or
# your own S3-compatible API from your infrastructure.
# Other backend implementations for node storage developed by the community
# are available in public GitHub repositories.

_seaweedfs_url = env("SEAWEEDFS_URL", "http://seaweedfs:8333")
_seaweedfs_access_key = env("SEAWEEDFS_ACCESS_KEY", "sentry")
_seaweedfs_secret_key = env("SEAWEEDFS_SECRET_KEY", "sentry")

SENTRY_NODESTORE = "sentry_nodestore_s3.S3PassthroughDjangoNodeStorage"
SENTRY_NODESTORE_OPTIONS = {
    "compression": True,
    "endpoint_url": _seaweedfs_url,
    "bucket_path": "nodestore",
    "bucket_name": "nodestore",
    "region_name": "us-east-1",
    "aws_access_key_id": _seaweedfs_access_key,
    "aws_secret_access_key": _seaweedfs_secret_key,
}

# Override profiles filestore from env so config.yml placeholder is never used.
SENTRY_OPTIONS["filestore.profiles-options"] = {
    "bucket_acl": "private",
    "default_acl": "private",
    "access_key": _seaweedfs_access_key,
    "secret_key": _seaweedfs_secret_key,
    "bucket_name": "profiles",
    "region_name": "us-east-1",
    "endpoint_url": _seaweedfs_url,
    "addressing_style": "path",
    "signature_version": "s3v4",
}

# Override internal URL prefix so Relay and workers can reach web.
_internal_url = env("SENTRY_INTERNAL_URL_PREFIX", "")
if _internal_url:
    SENTRY_OPTIONS["system.internal-url-prefix"] = _internal_url

#########
# Redis #
#########

# Generic Redis configuration used as defaults for various things including:
# Buffers, Quotas, TSDB
#
# On Railway, REDIS_URL is provided by the managed Redis plugin.
_redis_url = env("REDIS_URL", "")
if _redis_url:
    _r = _urlparse.urlparse(_redis_url)
    _redis_host = _r.hostname or "redis"
    _redis_port = str(_r.port or "6379")
    _redis_pass = _r.password or ""
else:
    _redis_host = env("REDIS_HOST", "redis")
    _redis_port = env("REDIS_PORT", "6379")
    _redis_pass = env("REDIS_PASSWORD", "")

SENTRY_OPTIONS["redis.clusters"] = {
    "default": {
        "hosts": {0: {"host": _redis_host, "password": _redis_pass, "port": _redis_port, "db": "0"}}
    }
}

#########
# Cache #
#########

# Sentry currently utilizes two separate mechanisms. While CACHES is not a
# requirement, it will optimize several high throughput patterns.

_memcached_host = env("MEMCACHED_HOST", "memcached")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": [f"{_memcached_host}:11211"],
        "TIMEOUT": 3600,
        "OPTIONS": {"ignore_exc": True},
    }
}

# A primary cache is required for things such as processing events
SENTRY_CACHE = "sentry.cache.redis.RedisCache"

_kafka_brokers = env("KAFKA_BROKERS", "kafka:9092")

DEFAULT_KAFKA_OPTIONS = {
    "bootstrap.servers": _kafka_brokers,
    "message.max.bytes": 50000000,
    "socket.timeout.ms": 1000,
}

SENTRY_EVENTSTREAM = "sentry.eventstream.kafka.KafkaEventStream"
SENTRY_EVENTSTREAM_OPTIONS = {"producer_configuration": DEFAULT_KAFKA_OPTIONS}

KAFKA_CLUSTERS["default"] = DEFAULT_KAFKA_OPTIONS

###############
# Rate Limits #
###############

# Rate limits apply to notification handlers and are enforced per-project
# automatically.

SENTRY_RATELIMITER = "sentry.ratelimits.redis.RedisRateLimiter"

##################
# Update Buffers #
##################

# Buffers (combined with queueing) act as an intermediate layer between the
# database and the storage API. They will greatly improve efficiency on large
# numbers of the same events being sent to the API in a short amount of time.
# (read: if you send any kind of real data to Sentry, you should enable buffers)

SENTRY_BUFFER = "sentry.buffer.redis.RedisBuffer"

##########
# Quotas #
##########

# Quotas allow you to rate limit individual projects or the Sentry install as
# a whole.

SENTRY_QUOTAS = "sentry.quotas.redis.RedisQuota"

########
# TSDB #
########

# The TSDB is used for building charts as well as making things like per-rate
# alerts possible.

SENTRY_TSDB = "sentry.tsdb.redissnuba.RedisSnubaTSDB"

#########
# SNUBA #
#########

SENTRY_SEARCH = "sentry.search.snuba.EventsDatasetSnubaSearchBackend"
SENTRY_SEARCH_OPTIONS = {}
SENTRY_TAGSTORE_OPTIONS = {}

###########
# Digests #
###########

# The digest backend powers notification summaries.

SENTRY_DIGESTS = "sentry.digests.backends.redis.RedisBackend"

##############
# Web Server #
##############

SENTRY_WEB_HOST = "0.0.0.0"
SENTRY_WEB_PORT = 9000
SENTRY_WEB_OPTIONS = {
    "http": "%s:%s" % (SENTRY_WEB_HOST, SENTRY_WEB_PORT),
    "protocol": "uwsgi",
    # This is needed in order to prevent https://github.com/getsentry/sentry/blob/c6f9660e37fcd9c1bbda8ff4af1dcfd0442f5155/src/sentry/services/http.py#L70
    "uwsgi-socket": None,
    "so-keepalive": True,
    # Keep this between 15s-75s as that's what Relay supports
    "http-keepalive": 15,
    "http-chunked-input": True,
    # the number of web workers
    "workers": 3,
    "threads": 4,
    "memory-report": False,
    # The `harakiri` option terminates requests that take longer than the
    # defined amount of time (in seconds) which can help avoid stuck workers
    # caused by GIL issues or deadlocks.
    # Ensure nginx `proxy_read_timeout` configuration (default: 30)
    # on your `nginx.conf` file to be at least 5 seconds longer than this.
    # "harakiri": 25,
    # Some stuff so uwsgi will cycle workers sensibly
    "max-requests": 100000,
    "max-requests-delta": 500,
    "max-worker-lifetime": 86400,
    # Duplicate options from sentry default just so we don't get
    # bit by sentry changing a default value that we depend on.
    "thunder-lock": True,
    "log-x-forwarded-for": False,
    "buffer-size": 32768,
    "limit-post": 209715200,
    "disable-logging": True,
    "reload-on-rss": 600,
    "ignore-sigpipe": True,
    "ignore-write-errors": True,
    "disable-write-exception": True,
}

###########
# SSL/TLS #
###########

# Railway terminates TLS at the edge and forwards via X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

########
# Mail #
########

SENTRY_OPTIONS["mail.list-namespace"] = env("SENTRY_MAIL_HOST", "localhost")
SENTRY_OPTIONS["mail.from"] = f"sentry@{SENTRY_OPTIONS['mail.list-namespace']}"

############
# Features #
############

# Sentry uses feature flags to enable certain features. Some features may
# require additional configuration or containers. To learn more about how
# Sentry uses feature flags, see https://develop.sentry.dev/backend/application-domains/feature-flags/
#
# The features listed here are stable and generally available on SaaS.
# To enable preview features, see https://develop.sentry.dev/self-hosted/configuration/#enabling-preview-features

SENTRY_FEATURES["projects:sample-events"] = False
SENTRY_FEATURES.update(
    {
        feature: True
        for feature in (
            "organizations:discover",
            "organizations:global-views",
            "organizations:issue-views",
            "organizations:incidents",
            "organizations:integrations-issue-basic",
            "organizations:integrations-issue-sync",
            "organizations:invite-members",
            "organizations:sso-basic",
            "organizations:sso-saml2",
            "organizations:advanced-search",
            "organizations:issue-platform",
            "organizations:monitors",
            "organizations:dashboards-mep",
            "organizations:mep-rollout-flag",
            "organizations:dashboards-rh-widget",
            "organizations:dynamic-sampling",
            "projects:custom-inbound-filters",
            "projects:data-forwarding",
            "projects:discard-groups",
            "projects:plugins",
            "projects:rate-limits",
            "projects:servicehooks",
        )
        # Performance/Tracing/Spans related flags
        + (
            "organizations:performance-view",
            "organizations:span-stats",
            "organizations:visibility-explore-view",
            "organizations:visibility-explore-range-high",
            "organizations:transaction-metrics-extraction",
            "organizations:indexed-spans-extraction",
            "organizations:insights-entry-points",
            "organizations:insights-initial-modules",
            "organizations:insights-addon-modules",
            "organizations:insights-modules-use-eap",
            "organizations:starfish-mobile-appstart",
            "organizations:on-demand-metrics-extraction",
            "projects:span-metrics-extraction",
            "projects:span-metrics-extraction-addons",
        )
        # Session Replay related flags
        + (
            "organizations:session-replay",
        )
        # User Feedback related flags
        + (
            "organizations:user-feedback-ui",
        )
        # Profiling related flags
        + (
            "organizations:profiling",
            "organizations:profiling-view",
        )
        # Continuous Profiling related flags
        + (
            "organizations:continuous-profiling",
            "organizations:continuous-profiling-stats",
        )
        # Uptime Monitoring related flags
        + (
            "organizations:uptime",
            "organizations:uptime-create-issues",
        )
        # Logs related flags
        + (
            "organizations:ourlogs-enabled",
            "organizations:ourlogs-ingestion",
            "organizations:ourlogs-stats",
            "organizations:ourlogs-replay-ui",
        )
        # Metrics related flags
        + (
            "organizations:tracemetrics-enabled",
            "organizations:tracemetrics-alerts",
            "organizations:tracemetrics-ingestion",
            "organizations:tracemetrics-equations-in-alerts",
            "organizations:tracemetrics-equations-in-explore",
            "organizations:tracemetrics-multi-metric-selection-in-dashboards",
            "organizations:tracemetrics-units-ui",
            "organizations:tracemetrics-stats-bytes-ui",
            "organizations:tracemetrics-pii-scrubbing-ui",
        )
    }
)

#######################
# MaxMind Integration #
#######################

GEOIP_PATH_MMDB = "/geoip/GeoLite2-City.mmdb"

#########################
# Bitbucket Integration #
#########################

# BITBUCKET_CONSUMER_KEY = 'YOUR_BITBUCKET_CONSUMER_KEY'
# BITBUCKET_CONSUMER_SECRET = 'YOUR_BITBUCKET_CONSUMER_SECRET'

##############################################
# Content Security Policy settings
##############################################

# CSP_REPORT_URI = "https://{your-sentry-installation}/api/{csp-project}/security/?sentry_key={sentry-key}"
CSP_REPORT_ONLY = True

############################
# Sentry Endpoint Settings #
############################

# If your Sentry installation has different hostnames for ingestion and web UI,
# in which your web UI is accessible via private corporate network, yet your
# ingestion hostname is accessible from the public internet, you can uncomment
# this following options in order to have the ingestion hostname rendered
# correctly on the SDK configuration UI.
#
# SENTRY_ENDPOINT = "https://sentry.ingest.example.com"

#################
# CSRF Settings #
#################

# Since version 24.1.0, Sentry migrated to Django 4 which contains stricter CSRF protection.
# If you are accessing Sentry from multiple domains behind a reverse proxy, you should set
# this to match your IPs/domains. Ports should be included if you are using custom ports.
# https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-CSRF_TRUSTED_ORIGINS

# CSRF_TRUSTED_ORIGINS = ["https://example.com", "http://127.0.0.1:9000"]

#################
# JS SDK Loader #
#################

# Configure Sentry JS SDK bundle URL template for Loader Scripts.
# Learn more about the Loader Scripts: https://docs.sentry.io/platforms/javascript/install/loader/
# If you wish to host your own JS SDK bundles, set `SETUP_JS_SDK_ASSETS` environment variable to `1`
# on your `.env` or `.env.custom` file. Then, replace the value below with your own public URL.
# For example: "https://sentry.example.com/js-sdk/%s/bundle%s.min.js"
#
# By default, the previous JS SDK assets version will be pruned during upgrades, if you wish
# to keep the old assets, set `SETUP_JS_SDK_KEEP_OLD_ASSETS` environment variable to any value on
# your `.env` or `.env.custom` file. The files should only be a few KBs, and this might be useful
# if you're using it directly like a CDN instead of using the loader script.
JS_SDK_LOADER_DEFAULT_SDK_URL = "https://browser.sentry-cdn.com/%s/bundle%s.min.js"

#####################
# Insights Settings #
#####################

# Since version 24.3.0, Insights features are available on self-hosted. For Requests module,
# there are scrubbing logic done on Relay to prevent high cardinality of stored HTTP hosts.
# However in self-hosted scenario, the amount of stored HTTP hosts might be consistent,
# and you may have allow list of hosts that you want to keep. Uncomment the following line
# to allow specific hosts. It might be IP addresses or domain names (without `http://` or `https://`).

# SENTRY_OPTIONS["relay.span-normalization.allowed_hosts"] = ["example.com", "192.168.10.1"]

##############
# Monitoring #
##############

# By default, Sentry uses dummy statsd monitoring backend that is a no-op.
# If you have a statsd server, you can utilize that to monitor self-hosted
# Sentry for "sentry"-related containers.
#
# To start, uncomment the following line and adjust the options as needed.

SENTRY_STATSD_ADDR = env("SENTRY_STATSD_ADDR")
if SENTRY_STATSD_ADDR:
    host, _, port = SENTRY_STATSD_ADDR.partition(":")
    port = int(port or 8125)
    SENTRY_METRICS_BACKEND = 'sentry.metrics.statsd.StatsdMetricsBackend'
    SENTRY_METRICS_OPTIONS: dict[str, Any] = {
        'host': host,
        'port': port,
    }
# SENTRY_METRICS_SAMPLE_RATE = 1.0   # Adjust this to your needs, default is 1.0
# SENTRY_METRICS_PREFIX = "sentry."  # Adjust this to your needs, default is "sentry."
