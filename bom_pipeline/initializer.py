"""
Intializes classes, satisfying configuration and supplied parameters.
"""
import inspect
from typing import Callable, Dict, List

from bom_pipeline.decorators import STAGE_MAP
from bom_pipeline.stage import Stage


class Initializer:
    """
    Intializes classes, satisfying configuration and supplied parameters.
    """

    def __init__(self):
        pass

    def __call__(
        self,
        function: Callable,
        parameters_dict: Dict[str, any],
        runtime_config: Dict[str, any],
        static_stages: List[Stage],
    ):
        if hasattr(function, "config"):
            for key in function.config.keys():
                parameters_dict[key] = get_config_part(function.config[key])

        signature = inspect.signature(function.__init__)

        result = function(
            *[
                _get_value_or_none(parameters_dict, k)
                for k in signature.parameters.keys()
                if k not in ("self", "args", "kwargs")
            ]
        )

        if function in STAGE_MAP:
            for stage, is_property in STAGE_MAP[function]:
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
                    s for s in reversed(static_stages) if isinstance(s, depen_type)
                ][0]

                func(result, most_recent_mixin)

        if hasattr(function, "runtime_configuration"):
            for parameter, is_property in function.runtime_configuration:
                if not is_property:
                    continue

                getattr(function, parameter)(result, runtime_config)

        return result


def _get_value_or_none(parameters, key):
    if key in parameters:
        return parameters[key]

    return None
