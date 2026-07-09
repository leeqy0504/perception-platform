# CLI Documentation and Help Design

## Context

The perception platform is now a single CLI-driven project with two public command families:

- Pipeline orchestration commands exposed through `perception-platform`, `pipeline`, `annotation-dataset`, and `python -m pipeline.cli`.
- UniTrain commands exposed through `unitrain-train`, `unitrain-predict`, `unitrain-export`, `unitrain-eval`, plus the helper script `run_unitrain.sh`.

The repository already contains reusable task examples in `examples/` and layered config presets under `configs/`. The current README explains the main annotation and end-to-end flows, but it does not give a complete command reference or show how each example YAML should be invoked. Some CLI help text is terse, and `run_unitrain.sh --help` currently fails when executed by the system `/bin/bash` on this machine because the script uses Bash associative arrays.

## Goal

Make command-line usage discoverable from both README and `--help` output.

The update should answer these common questions without requiring code reading:

- Which command should I run for dataset-only, end-to-end, training-only, predict, export, and eval workflows?
- What do the public command-line parameters mean?
- How do I run each `examples/*.yaml` file?
- Which YAML files are task pipeline configs, and which are direct UniTrain configs?
- What outputs should I expect after each main workflow?

## Scope

This is a documentation and CLI-help cleanup. It should not change pipeline behavior, training behavior, config loading, stage execution, or runner internals.

In scope:

- Update `README.md` with a concise command reference and example invocation table.
- Improve public CLI `argparse` descriptions, argument help, and examples.
- Update `run_annotation_dataset.sh --help` text if needed to align with README.
- Update `run_unitrain.sh --help` examples and make help executable in the current environment.

Out of scope:

- Changing YAML schema.
- Adding new CLI commands.
- Editing internal runner scripts under `unitrain/runners/_scripts` except for verification if needed.
- Running real SAM2 or model training.

## Recommended Approach

Use README as the complete reference and `--help` as the quick reference.

README should include:

- A "CLI Quick Reference" section near the existing run instructions.
- A table of public commands with purpose and examples.
- A table for `examples/*.yaml`:
  - `examples/dataset_only.yaml`: copy or adapt into a task config, then run `perception-platform run --config <task.yaml> --force`.
  - `examples/mixed_images_and_video.yaml`: same as dataset-only, with `input.video_path`.
  - `examples/end_to_end_rfdetr.yaml`: task pipeline config for annotation plus RF-DETR training.
  - `examples/end_to_end_yolo.yaml`: task pipeline config for annotation plus YOLO training.
  - `examples/train_yolo.yaml`: direct UniTrain config, run with `unitrain-train --config examples/train_yolo.yaml` or `./run_unitrain.sh train --config examples/train_yolo.yaml`.
- Parameter notes for pipeline commands and UniTrain commands.

CLI help should include:

- `pipeline --help`: command overview and examples.
- `pipeline run --help`: explain `preset`, `--config`, and `--force`.
- `pipeline stage --help`: explain stage names such as `prompt_mask`, `detection_dataset_export`, `dataset_prepare`, and `model_train`.
- `pipeline status --help`: explain that it reads status for the config run.
- `pipeline setup --help`: explain generated `tasks/<task>/task.yaml`.
- `unitrain-* --help`: keep concise, but make config override behavior clear where arguments override YAML.
- `run_unitrain.sh --help`: update examples to existing files and ensure it can be called directly.

## Implementation Notes

The `run_unitrain.sh` helper should use a Bash version that supports associative arrays. Since macOS `/bin/bash` is often Bash 3, the portable fix is to change the shebang to use `env bash` and make the script fail early with a clear message if the resolved Bash is still too old.

The README should not imply that `examples/dataset_only.yaml` can always be run directly unchanged. It contains sample task IDs and paths, so documentation should say "copy/adapt" for task examples. `examples/train_yolo.yaml` can be run directly once its `data.path` points to an existing COCO dataset.

## Testing

Verification should avoid real training. Run help commands only:

```bash
python -m pipeline.cli --help
python -m pipeline.cli run --help
python -m pipeline.cli stage --help
python -m pipeline.cli status --help
python -m pipeline.cli setup --help
python -m cli.train --help
python -m cli.predict --help
python -m cli.export --help
python -m cli.eval --help
./run_annotation_dataset.sh --help
./run_unitrain.sh --help
```

Also run the existing lightweight tests if the changes touch Python CLI code:

```bash
pytest tests/test_standalone_layout.py -v
```

## Success Criteria

- README tells users which command to run for every example YAML.
- Public help output includes parameter meanings and runnable examples.
- `./run_unitrain.sh --help` exits successfully in the current workspace.
- No behavior changes are introduced outside documentation/help text.
