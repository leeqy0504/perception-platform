"""Training-related pipeline stages."""

from pathlib import Path

from datasets import DatasetValidationError, prepare_dataset_manifest
from pipeline.config import PipelineConfig
from pipeline.manifest import load_manifest_for_config
from pipeline.stages import register_stage
from pipeline.stages.base import BaseStage, StageError
from pipeline.stages.context import StageContext


def _stage_input(config: PipelineConfig, context: StageContext | None, stage_name: str) -> Path:
    if context and context.data and context.data.get_input(stage_name):
        return context.input(stage_name)
    manifest = load_manifest_for_config(config)
    output = manifest.get_output_dir(stage_name)
    if output:
        return Path(output)
    raise StageError(f"Required stage input not found: {stage_name}")


@register_stage("dataset_prepare")
class DatasetPrepareStage(BaseStage):
    @property
    def name(self) -> str:
        return "dataset_prepare"

    def run(
        self,
        config: PipelineConfig,
        output_dir: Path,
        context: StageContext | None = None,
    ) -> Path:
        dataset_root = _stage_input(config, context, "detection_dataset_export")
        run_id = context.run.run_id if context and context.run else config.run_id
        try:
            prepare_dataset_manifest(
                dataset_root=dataset_root,
                output_dir=output_dir,
                task_name=config.task,
                run_id=run_id,
                source_stage="detection_dataset_export",
            )
        except DatasetValidationError as exc:
            raise StageError(str(exc)) from exc
        return output_dir
