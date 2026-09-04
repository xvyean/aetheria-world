#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
blender --background --factory-startup --python "$ROOT/blender/build_academy.py"
echo "ok: $ROOT/models/academy.glb"
