ARG BASE_IMAGE=altinity/clickhouse-server:25.3.6.10034.altinitystable
FROM ${BASE_IMAGE}

COPY config.xml /etc/clickhouse-server/config.d/sentry.xml
COPY default-password.xml /etc/clickhouse-server/users.d/default-password.xml
