"""A wrapper around the RapidOCR library to provide a simplified interface for OCR processing with error handling
and configuration management.

Example:
    ocr_wrapper = RapidOCRWrapper(is_init=True)
    img_url = "https://example.com/image.jpg"

    result = ocr_wrapper.run_ocr(img_url)
    print(result.boxes)
    print(result.txts)

    result = ocr_wrapper.run_ocr(img_url, params={"Global.return_word_box": True, "Global.return_single_char_box": True})
    print(result.to_json())
    print(result.to_markdown())
    result.vis("ocr_result.png")
"""
from pathlib import Path

from rapidocr import RapidOCR, LangDet, LangRec, ModelType, EngineType, OCRVersion
from rapidocr.utils.output import RapidOCROutput


class RapiOCRWrapperInitError(Exception):
    pass


class RapidOCRWrapperRunError(Exception):
    pass


class RapidOCRWrapper:
    def __init__(self, is_init: bool = True, params: dict | None = None):
        self.engine = None
        self.default_params = {
            "Global.log_level": "INFO",
            "Global.text_score": 0.3,
            # "Global.return_word_box": True,
            # "Global.return_single_char_box": True,
            # Detection parameters
            "Det.model_path": None,  # Use default model or replace with your own.
            "Det.engine_type": EngineType.ONNXRUNTIME,
            "Det.lang_type": LangDet.CH,
            "Det.model_type": ModelType.MOBILE,
            "Det.ocr_version": OCRVersion.PPOCRV5,
            "Det.thresh": 0.3,
            "Det.box_thresh": 0.5,
            "Det.unclip_score": 1.6,
            "Det.score_mode": "fast",
            # Recognition parameters
            "Rec.model_path": None,  # Use default model or replace with your own.
            "Rec.engine_type": EngineType.ONNXRUNTIME,
            "Rec.lang_type": LangRec.EN,
            "Rec.model_type": ModelType.MOBILE,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Rec.batch_num": 2,
        }
        if is_init:
            self.init(params={**self.default_params, **(params or {})})

    def init(self, config_path: str = "ocr_cfg.yaml", params: dict | None = None) -> None:
        """Initialize the RapidOCR engine with optional configuration path and parameters.

        Args:
            config_path: Path to the configuration file. If None, default configuration will be used.
            params: A dictionary of parameters to override the default configuration. If None, default parameters
                will be used.

        Raises:
            RapidOCRWrapperInitError: If there is an error during initialization of the RapidOCR engine
        """
        try:
            if config_path:
                config_path = (Path(__file__).parent / config_path).resolve()

            self.engine = RapidOCR(
                config_path=config_path,  # Use default config or replace with your own or override with params.
                params=params,  # Override default params with provided params if any.
            )
        except Exception as e:
            raise RapiOCRWrapperInitError(f"Failed to initialize RapidOCR engine: {e}") from e


    def run(self, img, params: dict | None = None) -> RapidOCROutput:
        """Run OCR on the given image URL with optional parameters.

        Args:
            img: The image to process. This can be a URL, a local file path, or an image array.
            params: A dictionary of parameters to override the current engine configuration for this run. If None
                the current engine configuration will be used.

        Returns:
            A RapidOCROutput object containing the OCR results.

        Raises:
            RapidOCRWrapperRunError: If there is an error during OCR processing.
        """
        if params:
            current_params = self.engine.params
            if any(current_params.get(k) != v for k, v in params.items()):
                self.init(params={**current_params, **params})

        if not self.engine:
            self.init()

        try:
            result: RapidOCROutput = self.engine(img, use_det=True, use_cls=False, use_rec=True)
            return result
        except Exception as e:
            raise RapidOCRWrapperRunError(f"Failed to run OCR: {e}") from e
