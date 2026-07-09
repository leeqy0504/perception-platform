#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH=""
TASK_NAME=""
FORCE_ARGS=()
PIPELINE_ARGS=()

usage() {
  cat <<'USAGE'
Usage:
  ./run_annotation_dataset.sh --task <task_name> [--force] [-- <extra pipeline args>]
  ./run_annotation_dataset.sh --config <path/to/task.yaml> [--force] [-- <extra pipeline args>]

Examples:
  ./run_annotation_dataset.sh --task mouse_001 --force
  ./run_annotation_dataset.sh --config tasks/mouse_001/task.yaml --force
  ./run_annotation_dataset.sh --config tasks/mouse_001/task.yaml -- annotation_to_unitrain

The runner keeps the layered config layout:
  tasks/<task>/task.yaml -> configs/pipelines + configs/algorithms + configs/runtime + registry

Arguments after "--" are passed to "python -m pipeline.cli run" as extra args.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task)
      TASK_NAME="${2:-}"
      shift 2
      ;;
    --config)
      CONFIG_PATH="${2:-}"
      shift 2
      ;;
    --force)
      FORCE_ARGS+=(--force)
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      PIPELINE_ARGS+=("$@")
      break
      ;;
    *)
      PIPELINE_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -n "$TASK_NAME" && -n "$CONFIG_PATH" ]]; then
  echo "Error: use either --task or --config, not both." >&2
  exit 2
fi

if [[ -n "$TASK_NAME" ]]; then
  CONFIG_PATH="$ROOT_DIR/tasks/$TASK_NAME/task.yaml"
fi

if [[ -z "$CONFIG_PATH" ]]; then
  echo "Error: --task or --config is required." >&2
  usage >&2
  exit 2
fi

if [[ "$CONFIG_PATH" != /* ]]; then
  CONFIG_PATH="$ROOT_DIR/$CONFIG_PATH"
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Error: config file not found: $CONFIG_PATH" >&2
  exit 1
fi

cd "$ROOT_DIR"
CMD=(python -m pipeline.cli run --config "$CONFIG_PATH")
if [[ ${#FORCE_ARGS[@]} -gt 0 ]]; then
  CMD+=("${FORCE_ARGS[@]}")
fi
if [[ ${#PIPELINE_ARGS[@]} -gt 0 ]]; then
  CMD+=("${PIPELINE_ARGS[@]}")
fi
"${CMD[@]}"
