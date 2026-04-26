#!/bin/sh
# Runtime config injection for CentralMemory UI
# Replaces __API_KEY__ placeholder in built JS with the actual key from environment

API_KEY="${ADMIN_API_KEY:-}"
JS_FILE=$(find /usr/share/nginx/html/assets -name 'index-*.js' | head -1)

if [ -n "$JS_FILE" ] && [ -n "$API_KEY" ]; then
  echo "Injecting API key into $JS_FILE"
  sed -i "s|__API_KEY_PLACEHOLDER__|$API_KEY|g" "$JS_FILE"
else
  echo "Warning: No API key or JS file found. UI will need manual auth."
fi

exec nginx -g 'daemon off;'