from rapid.ocr import RapidOCRWrapper
from rapid.layout import RapidLayoutWrapper
from rapid.table import RapidTableWrapper

if __name__ == "__main__":
    img_url = "samples/report_original.png"

    ocr = RapidOCRWrapper(is_init=True)
    ocr_result = ocr.run(img_url)
    print("---JSON---")
    print(ocr_result.to_json())
    print("---MARKDOWN---")
    print(ocr_result.to_markdown())
    ocr_result.vis("results/ocr_result.png")

    layout = RapidLayoutWrapper(is_init=True)
    layout_result = layout.run(img_url)
    print(layout_result)
    layout_result.vis("results/layout_result.png")

    table = RapidTableWrapper(is_init=True, ocr=ocr)
    table_result = table.run(img_url, ocr_results=ocr_result)
    print(table_result)
    table_result.vis("results", "table_result.png")