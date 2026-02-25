from rapid_table import ModelType, RapidTable, RapidTableInput, EngineType
from rapid_table.utils import RapidTableOutput
from rapidocr.utils.output import RapidOCROutput
from rapid.ocr import RapidOCRWrapper


class RapidTableWrapperInitError(Exception):
    pass

class RapidTableWrapperRunError(Exception):
    pass

class RapidTableWrapper:
    def __init__(self, is_init: bool = True, ocr: RapidOCRWrapper | None = None, params: dict | None = None):
        self.engine = None
        self.ocr = ocr
        self.default_params = {
            "engine_type": EngineType.ONNXRUNTIME,
            "model_type": ModelType.SLANETPLUS,
            "engine_cfg": {
                "use_dml": False,
                "use_cuda": False,
                "use_trt": False,
            }
        }

        if is_init:
            self.init(params={**self.default_params, **(params or {})})

    def init(self, params: dict | None = None) -> None:
        """Initialize the RapidTable engine with optional parameters.

        Args:
            params: A dictionary of parameters to override the default configuration. If None, default parameters
                will be used.

        Raises:
            RapidTableWrapperInitError: If there is an error during initialization of the RapidTable engine
        """
        try:
            if not self.ocr:
                # If no OCR engine is provided, initialize a default RapidOCRWrapper.
                self.ocr = RapidOCRWrapper(is_init=True)

            input_args = RapidTableInput(**(params or {}))
            self.engine = RapidTable(input_args)
        except Exception as e:
            raise RapidTableWrapperInitError(f"Failed to initialize RapidTable: {e}") from e

    def run(self, img: str, ocr_results: RapidOCROutput, params: dict | None = None) -> RapidTableOutput:
        """Run table recognition on the given image with OCR results and optional parameters.

        Args:
            img: The image to process. This can be a URL, a local file path, or an image array.
            ocr_results: The OCR results to use for table recognition. This should be a Rapid OCROutput object
                containing the OCR results.
            params: A dictionary of parameters to override the current engine configuration for this run. If None,
                the current engine configuration will be used.

        Returns:
            A RapidTableOutput object containing the table recognition results.

        Raises:
            RapidTableWrapperRunError: If there is an error during table recognition processing.
        """
        if params:
            current_params = self.engine.params
            if any(current_params.get(k) != v for k, v in params.items()):
                self.init(params={**current_params, **params})

        if not self.engine:
            raise RapidTableWrapperRunError("RapidTable engine is not initialized.")

        try:
            ocr_results = [(ocr_results.boxes, ocr_results.txts, ocr_results.scores)]
            results = self.engine(img, ocr_results=ocr_results)
            return results
        except Exception as e:
            raise RapidTableWrapperRunError(f"Failed to run RapidTable: {e}") from e
