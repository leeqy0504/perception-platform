# CLI Docs Help Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make public CLI commands discoverable from README and `--help`, including example YAML invocation guidance.

**Architecture:** Keep behavior unchanged and improve only documentation, public argparse metadata, helper-script help text, and one lightweight help regression test. README is the complete reference; `--help` output is the quick reference.

**Tech Stack:** Python 3.10+, argparse, Bash helper scripts, Markdown README, pytest.

---

## File Structure

- Modify `pipeline/cli.py`: enrich argparse descriptions, subcommand help, and examples.
- Modify `cli/train.py`, `cli/predict.py`, `cli/export.py`, `cli/eval.py`: add concise argparse epilog examples and clearer override wording.
- Modify `run_annotation_dataset.sh`: align usage with README and explain pass-through args.
- Modify `run_unitrain.sh`: use a portable Bash shebang, add a Bash version guard, and replace stale examples.
- Modify `README.md`: add a command reference and example YAML invocation table.
- Modify `tests/test_standalone_layout.py`: add a regression test for help commands that must not trigger real training or SAM2.

Git commits are omitted in this execution because this workspace's `.git/index` writes are blocked by the current sandbox. Final output must explicitly report that changes are not committed.

### Task 1: Add Help Regression Coverage

**Files:**
- Modify: `tests/test_standalone_layout.py`

- [ ] **Step 1: Add a failing help regression test**

Add this test after `test_runner_invokes_pipeline_from_project_root`:

```python
def test_public_help_commands_are_available():
    commands = [
        [sys.executable, "-m", "pipeline.cli", "--help"],
        [sys.executable, "-m", "pipeline.cli", "run", "--help"],
        [sys.executable, "-m", "pipeline.cli", "stage", "--help"],
        [sys.executable, "-m", "pipeline.cli", "status", "--help"],
        [sys.executable, "-m", "pipeline.cli", "setup", "--help"],
        [sys.executable, "-m", "cli.train", "--help"],
        [sys.executable, "-m", "cli.predict", "--help"],
        [sys.executable, "-m", "cli.export", "--help"],
        [sys.executable, "-m", "cli.eval", "--help"],
        [str(ROOT / "run_annotation_dataset.sh"), "--help"],
        [str(ROOT / "run_unitrain.sh"), "--help"],
    ]

    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result.returncode == 0, result.stderr
        output = result.stdout + result.stderr
        assert "--help" in output or "Usage:" in output or "用法:" in output
```

- [ ] **Step 2: Run the new test and verify current failure**

Run:

```bash
pytest tests/test_standalone_layout.py::test_public_help_commands_are_available -v
```

Expected: FAIL because `./run_unitrain.sh --help` exits nonzero under the current script shebang.

### Task 2: Improve Public CLI Help

**Files:**
- Modify: `pipeline/cli.py`
- Modify: `cli/train.py`
- Modify: `cli/predict.py`
- Modify: `cli/export.py`
- Modify: `cli/eval.py`

- [ ] **Step 1: Update `pipeline/cli.py` argparse help**

Use `argparse.RawDescriptionHelpFormatter` and add examples:

```python
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
```

Update subcommand help strings so `run`, `stage`, `status`, and `setup` explain what their arguments do. Keep command behavior unchanged.

- [ ] **Step 2: Update UniTrain argparse descriptions**

Add `formatter_class=argparse.RawDescriptionHelpFormatter` and examples to each public module:

```python
parser = argparse.ArgumentParser(
    description="Unified DL Training",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""Examples:
  unitrain-train --config examples/train_yolo.yaml
  unitrain-train --config examples/train_yolo.yaml --convert-data
  unitrain-train --config examples/train_yolo.yaml --skip-gpu-check --skip-eval
""",
)
```

Use equivalent examples for predict, export, and eval. Keep all existing option names.

- [ ] **Step 3: Verify Python help commands**

Run:

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
```

Expected: all commands exit 0 and show examples.

### Task 3: Fix Shell Helper Help

**Files:**
- Modify: `run_annotation_dataset.sh`
- Modify: `run_unitrain.sh`

- [ ] **Step 1: Update `run_unitrain.sh` shell compatibility**

Change the shebang:

```bash
#!/usr/bin/env bash
```

After `set -e`, add:

```bash
if [ -z "${BASH_VERSION:-}" ] || [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    echo "Error: run_unitrain.sh requires Bash 4+ for associative arrays." >&2
    echo "Install a newer bash and run: bash ./run_unitrain.sh --help" >&2
    exit 2
fi
```

- [ ] **Step 2: Update shell help examples**

Replace stale `configs/rfdetr.yaml` examples with existing repository examples:

```text
  ./run_unitrain.sh train --config examples/train_yolo.yaml
  ./run_unitrain.sh predict --config examples/train_yolo.yaml --source image.jpg
  ./run_unitrain.sh export --config examples/train_yolo.yaml --format onnx
  ./run_unitrain.sh eval --config examples/train_yolo.yaml --weights outputs/.../best.pt
```

Update `run_annotation_dataset.sh` help to mention:

```text
  ./run_annotation_dataset.sh --config tasks/mouse_001/task.yaml --force
  ./run_annotation_dataset.sh --config tasks/mouse_001/task.yaml -- annotation_to_unitrain
```

- [ ] **Step 3: Verify shell help commands**

Run:

```bash
./run_annotation_dataset.sh --help
./run_unitrain.sh --help
```

Expected: both commands exit 0 and show current examples.

### Task 4: Add README Command Reference

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a "CLI 命令速查" section after the current "运行" section**

Document:

```markdown
## CLI 命令速查

安装后公开入口：

| 命令 | 用途 |
| --- | --- |
| `perception-platform` / `pipeline` | 运行感知 pipeline |
| `annotation-dataset` / `annotation_dataset` | `pipeline` 的兼容别名 |
| `unitrain-train` | 直接运行 UniTrain 训练配置 |
| `unitrain-predict` | 使用 UniTrain 配置推理 |
| `unitrain-export` | 导出模型 |
| `unitrain-eval` | 评估模型 |
```

Then add compact parameter tables for pipeline and UniTrain commands.

- [ ] **Step 2: Add an `examples/` invocation table**

Include exact rows:

```markdown
| 示例文件 | 类型 | 调用方式 |
| --- | --- | --- |
| `examples/dataset_only.yaml` | task pipeline 配置模板 | 复制/改成 `tasks/<task>/task.yaml` 后运行 `perception-platform run --config tasks/<task>/task.yaml --force` |
| `examples/mixed_images_and_video.yaml` | task pipeline 配置模板 | 复制/改成任务配置，保留 `input.video_path` 后运行 pipeline |
| `examples/end_to_end_rfdetr.yaml` | task pipeline 配置模板 | 复制/改成任务配置后运行 `perception-platform run --config tasks/<task>/task.yaml --force` |
| `examples/end_to_end_yolo.yaml` | task pipeline 配置模板 | 复制/改成任务配置后运行 `perception-platform run --config tasks/<task>/task.yaml --force` |
| `examples/train_yolo.yaml` | 直接 UniTrain 配置 | 数据集路径有效后运行 `unitrain-train --config examples/train_yolo.yaml` |
```

- [ ] **Step 3: Verify README mentions all public commands**

Run:

```bash
rg -n "CLI 命令速查|perception-platform|unitrain-train|unitrain-predict|unitrain-export|unitrain-eval|examples/train_yolo.yaml" README.md
```

Expected: all listed phrases are present.

### Task 5: Final Verification

**Files:**
- No file edits.

- [ ] **Step 1: Run the focused help regression test**

Run:

```bash
pytest tests/test_standalone_layout.py::test_public_help_commands_are_available -v
```

Expected: PASS.

- [ ] **Step 2: Run lightweight layout tests**

Run:

```bash
pytest tests/test_standalone_layout.py -v
```

Expected: PASS.

- [ ] **Step 3: Review diff**

Run:

```bash
git diff -- README.md pipeline/cli.py cli/train.py cli/predict.py cli/export.py cli/eval.py run_annotation_dataset.sh run_unitrain.sh tests/test_standalone_layout.py docs/superpowers/specs/2026-07-09-cli-docs-help-design.md docs/superpowers/plans/2026-07-09-cli-docs-help.md
```

Expected: diff is limited to docs/help/test changes and contains no runtime behavior changes except the `run_unitrain.sh` Bash compatibility guard.
