from rapid_layout import EngineType, ModelType, RapidLayout, RapidLayoutInput
from rapid_layout.utils.typings import RapidLayoutOutput


class RapidLayoutWrapperInitError(Exception):
    pass


class RapidLayoutWrapperRunError(Exception):
    pass


class RapidLayoutWrapper:
    def __init__(self, is_init: bool = True, params: dict | None = None):
        self.engine = None
        self.default_params = {
            "model_dir_or_path": None,  # https://rapidai.github.io/RapidLayout/latest/models/
            "model_type": ModelType.PP_LAYOUT_CDLA,
            "engine_type": EngineType.ONNXRUNTIME,
            "conf_thresh": 0.3,
            "iou_thresh": 0.5,
        }
        if is_init:
            self.init(params={**self.default_params, **(params or {})})

    def init(self, params: dict | None = None):
        """Initialize the RapidLayout engine with optional parameters.

        Args:
            params: A dictionary of parameters to override the default configuration. If None, default parameters
                will be used.

        Raises:
            RapidLayoutWrapperInitError: If there is an error during initialization of the RapidLayout engine
        """
        try:
            normalized_params = RapidLayoutInput.normalize_kwargs(params)
            self.engine = RapidLayout(**normalized_params)
        except Exception as e:
            raise RapidLayoutWrapperInitError(f"Failed to initialize RapidLayout: {e}") from e

    def run(self, img_path: str, params: dict | None = None) -> RapidLayoutOutput:
        """Run layout analysis on the given image path with optional parameters.

        Args:
            img_path: Path to the input image for layout analysis.
            params: A dictionary of parameters to override the default configuration for this run. If None,
                default parameters will be used.

        Returns:
            RapidLayoutOutput: The output of the layout analysis.

        Raises:
            RapidLayoutWrapperRunError: If there is an error during the execution of the layout analysis
        """
        if params:
            current_params = self.engine.params
            if any(current_params.get(k) != v for k, v in params.items()):
                self.init(params={**current_params, **params})

        if not self.engine:
            self.init()

        try:
            result = self.engine(img_path)
            return result
        except Exception as e:
            raise RapidLayoutWrapperRunError(f"Failed to run layout analysis: {e}") from e
