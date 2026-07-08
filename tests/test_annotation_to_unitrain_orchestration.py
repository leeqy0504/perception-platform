from pathlib import Path

from pipeline.config import InputConfig, PipelineConfig, Sam2Config
from pipeline.manifest import Manifest
from pipeline.pipeline import PipelineOrchestrator


class FakeStage:
    def __init__(self, name: str):
        self.name = name

    def run(self, config, output_dir, context=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        if self.name == "model_train":
            context.metadata["model_train"] = {
                "framework": "rfdetr",
                "model": "seg-nano",
                "task": "segment",
                "train_output_dir": str(output_dir / "train"),
                "best_weights": str(output_dir / "train" / "checkpoint_best_ema.pth"),
                "resolved_config": str(output_dir / "resolved_unitrain_config.yaml"),
            }
        return output_dir


def test_orchestrator_persists_model_train_metadata(tmp_path, monkeypatch):
    config = PipelineConfig(
        task="mouse_001",
        preset="annotation_to_unitrain",
        input=InputConfig(rgbd_dir=str(tmp_path / "tasks" / "mouse_001")),
        sam2=Sam2Config(container="sam2-backend-1", points=[[1, 1]], labels=[1]),
        output_dir=str(tmp_path / "output"),
        pipeline_stages=["dataset_prepare", "model_train"],
    )
    monkeypatch.setattr("pipeline.pipeline.get_stage", lambda name: FakeStage(name))

    PipelineOrchestrator().run_preset(config, force=True)

    manifest = Manifest.load(str(tmp_path / "output" / "mouse_001" / "manifest.json"))
    assert manifest.stages["model_train"]["metadata"]["best_weights"].endswith(
        "checkpoint_best_ema.pth"
    )
    assert manifest.metadata["model_train"]["best_weights"].endswith(
        "checkpoint_best_ema.pth"
    )
