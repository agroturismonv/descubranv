#!/bin/bash
set -e

if [ -n "$GIT_TOKEN" ] && [ -n "$GIT_REPO" ]; then
    git config user.name  "${GIT_USER_NAME:-Deploy Bot}"
    git config user.email "${GIT_USER_EMAIL:-bot@descubranv.com}"
    git remote set-url origin "https://${GIT_TOKEN}@github.com/${GIT_REPO}.git"

    echo "⬇️  Puxando dados mais recentes..."
    git pull origin "${GIT_BRANCH:-main}" --rebase --autostash || true
fi

exec gunicorn server:app \
    --bind "0.0.0.0:${PORT:-5000}" \
    --workers 2 --timeout 120 \
    --access-logfile - --error-logfile -
