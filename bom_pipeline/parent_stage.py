"""
Base class for Serial and Parallel classes.  Implements common functionality between the two.
"""
import inspect
from typing import Callable, Dict, List

from bom_pipeline.decorators import STAGE_MAP
from bom_pipeline.initializer import Initializer
from bom_pipeline.models.time import Time
from bom_pipeline.stage import Stage


class ParentStage(Stage):
    """
    Base class for Serial and Parallel classes.  Implements common functionality between the two.
    """

    static_stages = []

    def __init__(
        self, name: str, runtime_config: Dict[str, any], *stage_types: List[Callable]
    ):
        Stage.__init__(self)

        if runtime_config is None:
            runtime_config = {}

        self.name = name
        self.stages: List[Stage] = []
        for stage_type in stage_types:
            parameters_dict = {}

            if hasattr(stage_type, "last_stage"):
                for parameter in stage_type.last_stage:
                    parameters_dict[parameter] = self.stages[-1]

            if stage_type in STAGE_MAP:
                for stage, is_property in STAGE_MAP[stage_type]:
                    if is_property:
                        continue

                    signature = inspect.signature(stage_type)
                    depen_type = signature.parameters[stage].annotation

                    most_recent_mixin = [
                        s
                        for s in reversed(self.static_stages)
                        if isinstance(s, depen_type)
                    ][0]

                    parameters_dict[stage] = most_recent_mixin

            if hasattr(stage_type, "runtime_configuration"):
                for parameter, is_property in stage_type.runtime_configuration:
                    if is_property:
                        continue

                    parameters_dict[parameter] = runtime_config

            stage: Stage = Initializer.instance(
                stage_type,
                parameters_dict,
                runtime_config,
                self.static_stages,
            )

            stage.before_init()

            self.stages.append(stage)
            self.static_stages.append(stage)

    def get_time(self) -> Time:
        """
        Calculates the average time per execution of this stage.
        """

        time = Stage.get_time(self)
        time.children = [s.get_time() for s in self.stages]

        return time

    def on_init(self) -> None:
        for stage in self.stages:
            stage.on_init()

    def on_destroy(self) -> None:
        for stage in self.stages:
            stage.on_destroy()
