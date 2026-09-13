#!/usr/bin/env bash
set -euo pipefail

: "${APP_DIR:?APP_DIR is required}"
: "${DEPLOY_SHA:?DEPLOY_SHA is required}"
: "${DEPLOY_IPV4:?DEPLOY_IPV4 is required}"
: "${OWNER_EMAIL:?OWNER_EMAIL is required}"

cd "$APP_DIR"
umask 077

test -f compose.production.yml
test -f deploy/Caddyfile.tjekatjeka
docker network inspect ithute_ithute >/dev/null

DB_PASSWORD=""
if [ -f .env.production ]; then
  DB_PASSWORD="$(sed -n 's/^TJEKATJEKA_DB_PASSWORD=//p' .env.production | head -n1)"
fi
if [ -z "$DB_PASSWORD" ]; then
  DB_PASSWORD="$(openssl rand -hex 32)"
fi

cat > .env.production <<EOF
TJEKATJEKA_DB_PASSWORD=$DB_PASSWORD
TJEKATJEKA_PUBLIC_URL=https://tjekane.ihute.co.ls
TJEKATJEKA_AUTH_ISSUER=https://auth.ithute.co.ls
TJEKATJEKA_AUTH_AUDIENCE=tjekatjeka
TJEKATJEKA_AUTH_CLIENT_ID=tjekatjeka
TJEKATJEKA_OIDC_REDIRECT_URI=https://tjekane.ihute.co.ls/api/auth/oidc/callback
TJEKATJEKA_COOKIE_SECURE=true
TJEKATJEKA_BOOTSTRAP_ADMIN_EMAIL=$OWNER_EMAIL
TJEKATJEKA_DEV_AUTH_BYPASS=false
EOF
chmod 600 .env.production
printf 'TJEKATJEKA_IMAGE_TAG=%s\n' "$DEPLOY_SHA" > .image.env
chmod 600 .image.env

compose() {
  docker compose --env-file .env.production --env-file .image.env -p tjekatjeka -f compose.production.yml "$@"
}

compose config >/tmp/tjekatjeka-compose-rendered.yml
if grep -Eq '^[[:space:]]*build:' /tmp/tjekatjeka-compose-rendered.yml; then
  echo "Production compose must use immutable images, not server-side builds" >&2
  exit 1
fi
compose pull
compose up -d --remove-orphans

APP_API_CONTAINER="$(docker ps --filter label=com.docker.compose.project=ithute --filter label=com.docker.compose.service=ithute-app-api -q | head -n1)"
CADDY_CONTAINER="$(docker ps --filter label=com.docker.compose.project=ithute --filter label=com.docker.compose.service=caddy -q | head -n1)"
test -n "$APP_API_CONTAINER"
test -n "$CADDY_CONTAINER"

# Publish the product hostname through Ithute's authoritative PowerDNS.
docker exec -i "$APP_API_CONTAINER" python - "$DEPLOY_IPV4" <<'PY'
import sys
from app.services.powerdns import PowerDNSClient
ip = sys.argv[1]
client = PowerDNSClient()
client.replace_rrset("ithute.co.ls", "tjekane.ihute.co.ls", "A", 300, [ip])
print("Tjekatjeka DNS A record reconciled")
PY

# Product routes are deliberately owned by product repositories and persisted
# in the central Caddy data volume.
docker exec "$CADDY_CONTAINER" mkdir -p /data/product-routes
docker cp deploy/Caddyfile.tjekatjeka "$CADDY_CONTAINER:/data/product-routes/tjekatjeka.caddy"
docker exec "$CADDY_CONTAINER" caddy validate --config /etc/caddy/Caddyfile >/dev/null
docker exec "$CADDY_CONTAINER" caddy reload --config /etc/caddy/Caddyfile

# Internal readiness and exact-image checks.
compose exec -T backend python -c "import urllib.request; assert b'\"status\":\"ready\"' in urllib.request.urlopen('http://127.0.0.1:8204/readyz', timeout=5).read()"
compose exec -T frontend sh -c "wget -qO- http://127.0.0.1:3204/ | grep -q 'Sign in to Tjekatjeka'"

verify_image() {
  service="$1"
  expected="$2"
  container_id="$(compose ps -q "$service")"
  test -n "$container_id"
  actual="$(docker inspect --format '{{.Config.Image}}' "$container_id")"
  test "$actual" = "$expected"
}
verify_image backend "ghcr.io/ithute-stak/tjekatjeka-backend:$DEPLOY_SHA"
verify_image frontend "ghcr.io/ithute-stak/tjekatjeka-frontend:$DEPLOY_SHA"

echo "Tjekatjeka production runtime deployed successfully"
