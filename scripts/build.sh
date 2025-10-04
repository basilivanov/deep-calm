#!/bin/bash
set -e

ENV=${1:-dev}

echo "🚀 Building DeepCalm images for $ENV environment"

case $ENV in
  "test")
    echo "📦 Building test images..."
    docker build -f Dockerfile.api -t deep-calm-api:test .
    docker build -f Dockerfile.frontend -t deep-calm-frontend:test .
    ;;
  "prod")
    echo "📦 Building production images..."
    docker build -f Dockerfile.api -t deep-calm-api:prod .
    docker build -f Dockerfile.frontend -t deep-calm-frontend:prod .
    ;;
  "dev")
    echo "ℹ️  Dev uses bind-mounts, no build needed"
    echo "ℹ️  Just run: docker compose -f dev/docker-compose.yml up"
    ;;
  *)
    echo "❌ Unknown environment: $ENV"
    echo "Usage: $0 [dev|test|prod]"
    exit 1
    ;;
esac

echo "✅ Build complete for $ENV"