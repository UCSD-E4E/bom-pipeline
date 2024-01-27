"""
Implements a base pipeline.
"""

import datetime
import inspect
import os
import platform
from abc import ABC
from typing import Callable, List

from wakepy import set_keepawake, unset_keepawake

from bom_pipeline.initializer import Initializer
from bom_pipeline.parallel import Parallel
from bom_pipeline.parent_stage import ParentStage
from bom_pipeline.progress import Progress
from bom_pipeline.serial import Serial
from bom_pipeline.stage import Stage
from bom_pipeline.stage_result import StageResult


class Pipeline(ABC):
    """
    Implements a base pipeline.
    """

    iterations = 0

    def __init__(
        self,
        name: str,
        initializer: Initializer,
        *stage_types: List[Stage],
        progress: Progress = None,
        parallel=False,
        runtime_config=None,
    ):
        ParentStage.static_stages = []
        Pipeline.instance = self

        self.name = name
        self._runtime_config = runtime_config
        self._progress = progress
        self._pdtTimeZone = datetime.timezone(datetime.timedelta(hours=-7))
        self._last_print_time: datetime = datetime.datetime.utcnow().astimezone(
            self._pdtTimeZone
        )

        with open("./output/update", "w", encoding="utf8") as f:
            f.write(f"{self._last_print_time}\n")

        if parallel:
            self.stage = Parallel(name, runtime_config, initializer, *stage_types)
        else:
            self.stage = Serial(name, runtime_config, initializer, *stage_types)

        for result in ParentStage.static_stages:
            function = type(result)

            if hasattr(function, "stages_from_prev_iter"):
                for stage, is_property in function.stages_from_prev_iter:
                    if not is_property:
                        continue

                    func = getattr(function, stage)

                    signature = inspect.signature(func)
                    depen_type = [
                        signature.parameters[p]
                        for i, p in enumerate(signature.parameters)
                        if i == 1
                    ][0].annotation

                    most_recent_mixin = [
                        s
                        for s in reversed(ParentStage.static_stages)
                        if isinstance(s, depen_type)
                    ][0]

                    func(result, most_recent_mixin)
        self.stage.on_init()

    # def flowchart_image(self):
    #     """
    #     Generates a chart representing the algorithm.
    #     """

    #     (
    #         img,
    #         _,
    #         _,
    #     ) = self.stage.flowchart_image()
    #     return img

    def step(self) -> StageResult:
        """
        Runs one step of the algorithm.
        """
        self.stage.before_execute()
        result = self.stage.execute()
        self.stage.after_execute()

        return result

    def run(self, iterations: int = None):
        """
        Runs the algorithm until it finishes.
        """

        if iterations:
            Pipeline.iterations = iterations

        keep_awake = platform.system() != "Linux" or (
            "XDG_SESSION_TYPE" in os.environ and os.environ["XDG_SESSION_TYPE"] != "tty"
        )
        if keep_awake:
            set_keepawake()

        curr = 1
        try:
            while True:
                result = self.step()
                self.progress()

                curr += 1

                if not result.continue_pipeline or (
                    iterations and curr >= iterations + 1
                ):
                    if self._progress:
                        self._progress.close()

                    if (
                        "timings" in self._runtime_config
                        and self._runtime_config["timings"]
                    ):
                        print("Average Runtime per stage:")
                        self.stage.get_time().print_to_console()

                    self.stage.on_destroy()
                    if keep_awake:
                        unset_keepawake()

                    return
        except KeyboardInterrupt as exc:
            if "timings" in self._runtime_config and self._runtime_config["timings"]:
                print("Average Runtime per stage:")
                self.stage.get_time().print_to_console()

            self.stage.on_destroy()
            if keep_awake:
                unset_keepawake()

            raise exc

    def get(self, stage_type: Callable):
        """
        Get a type from the pipeline.
        """
        candidate_stages = [
            s for s in ParentStage.static_stages if isinstance(s, stage_type)
        ]

        return candidate_stages[-1]

    def progress(self):
        """
        Increments the progress bar by 1.
        """

        if (
            "progress" not in self._runtime_config
            or not self._runtime_config["progress"]
        ):
            return

        now = datetime.datetime.utcnow().astimezone(self._pdtTimeZone)

        if self._progress:
            self._progress.total = int(Pipeline.iterations)

        if (now - self._last_print_time).seconds >= 5 * 60:
            self._progress.write(str(now))

            with open("./output/update", "w", encoding="utf8") as f:
                f.write(f"{now}\n")

            self._last_print_time = now

        self._progress.increment()
