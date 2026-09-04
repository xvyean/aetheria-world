#!/usr/bin/env bash
# 用 blender/engine 重建学院 GLB（大场景）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
blender --background --factory-startup --python "$ROOT/blender/engine/build_academy.py" -- \
  --look night --cam hero --res 1600x900 --samples 24 \
  --glb "$ROOT/models/academy.glb"
echo "ok: $ROOT/models/academy.glb"
