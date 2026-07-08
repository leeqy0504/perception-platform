import json
from pathlib import Path

from pipeline.config import InputConfig, PipelineConfig, Sam2Config
from pipeline.stages.context import DataContext, RunContext, StageContext
from pipeline.stages.training import DatasetPrepareStage


def _config(task_dir: Path) -> PipelineConfig:
    return PipelineConfig(
        task="mouse_001",
        preset="annotation_to_unitrain",
        input=InputConfig(rgbd_dir=str(task_dir)),
        sam2=Sam2Config(container="sam2-backend-1", points=[[1, 1]], labels=[1]),
    )


def _write_split(root: Path, split: str, image_name: str) -> None:
    split_dir = root / split
    split_dir.mkdir(parents=True)
    (split_dir / image_name).write_bytes(b"fake image")
    (split_dir / "_annotations.coco.json").write_text(
        json.dumps({
            "images": [{"id": 1, "file_name": image_name, "width": 4, "height": 3}],
            "annotations": [{"id": 1, "image_id": 1, "category_id": 0, "bbox": [0, 0, 2, 2], "area": 4, "iscrowd": 0}],
            "categories": [{"id": 0, "name": "object", "supercategory": "object"}],
        }),
        encoding="utf-8",
    )


def test_dataset_prepare_stage_writes_manifest_from_export_output(tmp_path):
    task_dir = tmp_path / "tasks" / "mouse_001"
    export_dir = tmp_path / "run" / "detection_dataset_export"
    output_dir = tmp_path / "run" / "dataset_prepare"
    _write_split(export_dir, "train", "000000.png")
    _write_split(export_dir, "valid", "000001.png")
    context = StageContext(
        run=RunContext(run_id="run42", task_name="mouse_001"),
        data=DataContext(
            task_dir=task_dir,
            run_dir=tmp_path / "run",
            output_dir=output_dir,
            inputs={"detection_dataset_export": export_dir},
        ),
        stage_name="dataset_prepare",
    )

    result = DatasetPrepareStage().run(_config(task_dir), output_dir, context=context)

    assert result == output_dir
    manifest = json.loads((output_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == "mouse_001:run42:detection_dataset_export"
    assert manifest["root"] == str(export_dir)
