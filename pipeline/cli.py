"""CLI entry point for the pipeline tool."""

import argparse
import json
import sys
from pathlib import Path

import yaml

from pipeline.config import load_config, ConfigError
from pipeline.pipeline import PipelineOrchestrator


def cmd_run(args):
    config = load_config(args.config, project_root=Path.cwd())
    if args.preset:
        config.preset = args.preset

    orch = PipelineOrchestrator()
    orch.run_preset(config, force=args.force)


def cmd_stage(args):
    config = load_config(args.config, project_root=Path.cwd())

    orch = PipelineOrchestrator()
    orch.run_stage(config, args.stage_name, force=args.force)


def cmd_status(args):
    config = load_config(args.config, project_root=Path.cwd())

    orch = PipelineOrchestrator()
    orch.status(config)


def cmd_setup(args):
    task_name = args.task
    project_root = Path(args.project_root).resolve()
    task_dir = project_root / "tasks" / task_name

    if not task_dir.is_dir():
        print(f"Error: Task directory not found: {task_dir}", file=sys.stderr)
        sys.exit(1)

    info_path = task_dir / "dataset_info.json"
    info = {}
    if info_path.exists():
        with open(info_path) as f:
            info = json.load(f)

    existing_path = task_dir / "task.yaml"
    existing = {}
    if existing_path.exists():
        existing = yaml.safe_load(existing_path.read_text(encoding="utf-8")) or {}

    sam2_data = info.get("sam2_points", {})
    data = {
        **existing,
        "task_id": task_name,
        "pipeline": existing.get("pipeline", args.pipeline),
        "runtime": existing.get("runtime", args.runtime),
        "class_id": int(existing.get("class_id", args.class_id)),
        "input": {
            **existing.get("input", {}),
            "source": f"./tasks/{task_name}/",
            "first_frame": int(existing.get("input", {}).get("first_frame", 0)),
        },
        "sam2": {
            **existing.get("sam2", {}),
            "points": sam2_data.get("points", existing.get("sam2", {}).get("points", [])),
            "labels": sam2_data.get("labels", existing.get("sam2", {}).get("labels", [])),
        },
        "output_dir": existing.get("output_dir", "output/"),
    }

    existing_path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    print(f"Task config written: {existing_path}")
    print(f"  source     -> ./tasks/{task_name}/")
    print(f"  pipeline   -> {data['pipeline']}")


def main():
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="Perception platform pipeline orchestration CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  pipeline setup --task mouse_001
  pipeline run --config tasks/mouse_001/task.yaml --force
  pipeline run annotation_to_unitrain --config tasks/mouse_001/task.yaml
  pipeline stage detection_dataset_export --config tasks/mouse_001/task.yaml --force
  pipeline status --config tasks/mouse_001/task.yaml
""",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>", help="Available commands")

    # pipeline run <preset> --config <path> [--force]
    run_parser = subparsers.add_parser(
        "run",
        help="Run all stages for a task config",
        description="Run a configured pipeline, such as annotation_dataset or annotation_to_unitrain.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  pipeline run --config tasks/mouse_001/task.yaml --force
  pipeline run annotation_dataset --config tasks/mouse_001/task.yaml
  pipeline run annotation_to_unitrain --config tasks/mouse_001/task.yaml
""",
    )
    run_parser.add_argument(
        "preset",
        nargs="?",
        help="Optional pipeline preset name; overrides the preset resolved from the YAML config",
    )
    run_parser.add_argument(
        "--config",
        required=True,
        help="Path to a task YAML config, usually tasks/<task>/task.yaml",
    )
    run_parser.add_argument("--force", action="store_true", help="Re-run stages even if outputs already exist")
    run_parser.set_defaults(func=cmd_run)

    # pipeline stage <name> --config <path> [--force]
    stage_parser = subparsers.add_parser(
        "stage",
        help="Run one named pipeline stage",
        description="Run a single stage from a task config.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Common stages:
  prompt_mask
  sam2_video_propagation
  mask_qa
  review_pack
  detection_dataset_export
  dataset_prepare
  model_train

Examples:
  pipeline stage detection_dataset_export --config tasks/mouse_001/task.yaml --force
  pipeline stage model_train --config tasks/mouse_001/task.yaml
""",
    )
    stage_parser.add_argument("stage_name", help="Stage name to run, for example detection_dataset_export")
    stage_parser.add_argument(
        "--config",
        required=True,
        help="Path to a task YAML config, usually tasks/<task>/task.yaml",
    )
    stage_parser.add_argument("--force", action="store_true", help="Re-run the stage even if output exists")
    stage_parser.set_defaults(func=cmd_stage)

    # pipeline status --config <path>
    status_parser = subparsers.add_parser(
        "status",
        help="Show stage status for a task config",
        description="Read the pipeline manifest and show status for the selected task config.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Example:
  pipeline status --config tasks/mouse_001/task.yaml
""",
    )
    status_parser.add_argument(
        "--config",
        required=True,
        help="Path to a task YAML config, usually tasks/<task>/task.yaml",
    )
    status_parser.set_defaults(func=cmd_status)

    # pipeline setup --task <name>
    setup_parser = subparsers.add_parser(
        "setup",
        help="Create or update tasks/<task>/task.yaml",
        description="Create or update a task YAML file under tasks/<task>/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  pipeline setup --task mouse_001
  pipeline setup --task mouse_001 --pipeline annotation_to_unitrain --class-id 0
""",
    )
    setup_parser.add_argument("--task", required=True, help="Task name; writes tasks/<task>/task.yaml")
    setup_parser.add_argument("--pipeline", default="annotation_dataset", help="Pipeline id to store in task.yaml")
    setup_parser.add_argument("--runtime", default="server", help="Runtime config id from configs/runtime/")
    setup_parser.add_argument("--class-id", type=int, default=0, help="Target class id from registry/classes.json")
    setup_parser.add_argument("--project-root", default=".", help="Project root that contains tasks/ and configs/")
    setup_parser.set_defaults(func=cmd_setup)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
