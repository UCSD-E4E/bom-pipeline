"""
Entry point for the pipeline module.
"""

from bom_pipeline.factory import factory
from bom_pipeline.parallel import Parallel
from bom_pipeline.pipeline import Pipeline
from bom_pipeline.serial import Serial
from bom_pipeline.stage import Stage
from bom_pipeline.stage_result import StageResult
