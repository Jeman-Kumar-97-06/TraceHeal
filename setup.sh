#!/bin/bash
set -e

echo "🚀 Installing SigNoz Foundry CLI..."
if ! command -v foundryctl &> /dev/null; then
    curl -fsSL https://signoz.io/foundry.sh | bash
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "📦 Casting SigNoz stack..."
foundryctl cast -f casting.yaml

echo "✅ SigNoz is booting up at http://localhost:8080"