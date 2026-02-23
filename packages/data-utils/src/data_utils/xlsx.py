from pathlib import Path
from typing import Any

import pandas as pd


def excel_to_dict(
    io: Any,
    sheet_name: int | str = 0,
    usecols: list | None = None,
    orient="records",
    **kwargs,
) -> list[dict]:
    """Reads an Excel file or files and returns the data as a list of dictionaries.

    Automatically selects the appropriate engine based on file extension:
    - .xlsb files: tries multiple engines (openpyxl, pyxlsb) for compatibility
    - Other Excel files (.xlsx, .xls): uses calamine engine for better performance
    """
    # Determine file extension to choose appropriate engine
    file_path = Path(str(io))
    file_extension = file_path.suffix.lower()

    # Select engine based on file type
    if file_extension == ".xlsb":
        # Try engines in order until one works; None lets pandas auto-select.
        last_error: Exception | None = None
        for engine in (None, "openpyxl", "pyxlsb"):
            try:
                engine_kwarg = {} if engine is None else {"engine": engine}
                df = pd.read_excel(io=io, sheet_name=sheet_name, usecols=usecols, **engine_kwarg, **kwargs)
                break
            except (ImportError, Exception) as e:
                last_error = e
        else:
            raise last_error or RuntimeError(f"Could not read XLSB file {io} with any available engine")
    else:
        # For other Excel files, use calamine for better performance
        df = pd.read_excel(io=io, sheet_name=sheet_name, usecols=usecols, engine="calamine", **kwargs)

    return df.to_dict(orient=orient)  # type: ignore[call-arg]
