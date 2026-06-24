#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENRIGLOGIC_DIR="${ROOT_DIR}/third_party/openriglogic"
BUILD_DIR="${ROOT_DIR}/build/openriglogic-blender"
PYTHON_EXECUTABLE="${PYTHON_EXECUTABLE:-/opt/homebrew/opt/python@3.13/bin/python3.13}"
PATCH_FILE="${ROOT_DIR}/patches/openriglogic-blender-python-module.patch"

if [[ ! -d "${OPENRIGLOGIC_DIR}" ]]; then
  echo "Missing ${OPENRIGLOGIC_DIR}. Clone EpicGames/openriglogic first." >&2
  exit 1
fi

if [[ -f "${PATCH_FILE}" ]]; then
  if git -C "${OPENRIGLOGIC_DIR}" apply --check "${PATCH_FILE}" >/dev/null 2>&1; then
    git -C "${OPENRIGLOGIC_DIR}" apply "${PATCH_FILE}"
  elif git -C "${OPENRIGLOGIC_DIR}" apply --reverse --check "${PATCH_FILE}" >/dev/null 2>&1; then
    echo "OpenRigLogic Blender Python patch already applied."
  else
    echo "Could not apply ${PATCH_FILE}; OpenRigLogic source may have changed." >&2
    exit 1
  fi
fi

cmake \
  -S "${OPENRIGLOGIC_DIR}" \
  -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Release \
  -DRL_BUILD_PYTHON_WRAPPER=3.13 \
  -DRL_BUILD_TESTS=OFF \
  -DRL_BUILD_EXAMPLES=OFF \
  -DRL_BUILD_BENCHMARKS=OFF \
  -DPython3_EXECUTABLE="${PYTHON_EXECUTABLE}"

cmake --build "${BUILD_DIR}" --config Release --parallel "${BUILD_PARALLELISM:-8}"

ln -sf _py3dna13_2_5.13.2.5.dylib "${BUILD_DIR}/python/dna/_py3dna13_2_5.so"
ln -sf _py3riglogic13_2_5.13.2.5.dylib "${BUILD_DIR}/python/riglogic/_py3riglogic13_2_5.so"

echo "OpenRigLogic Python bindings are ready at:"
echo "${BUILD_DIR}/python"
