#!/bin/sh

PROD_URL="http://prod:5000/health"
UPSTREAM_CONF="/etc/nginx/conf.d/upstream.conf"
NGINX_RELOAD="nginx -s reload"

# Health check using curl
if curl --max-time 3 --silent --fail "$PROD_URL" > /dev/null; then
    echo "✅ Production is UP"
    cp /etc/nginx/conf.d/prod.conf $UPSTREAM_CONF
else
    echo "❌ Production is DOWN — Switching to STAGING"
    cp /etc/nginx/conf.d/staging.conf $UPSTREAM_CONF
fi

# Reload nginx to apply changes
$NGINX_RELOAD
