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

    Args:
        io: File path, file-like object, or bytes to read from.
        sheet_name: Name or index of the sheet to read (default: 0, which means the first sheet).
        usecols: Optional list of columns to read (e.g., ["A", "C:E"] or [0, 2, 4]).
        orient: Orientation of the resulting list of dictionaries (default: "records"). See pandas.DataFrame.to_dict()
            for options.
        **kwargs: Additional keyword arguments to pass to pandas.read_excel().

    Returns:
        A list of dictionaries representing the rows of the Excel sheet, with keys as column names and values as cell
        values, formatted according to the specified orientation.

    Raises:
        ValueError: If the file extension is not recognized or if no suitable engine can read the file.
        ImportError: If required engines for .xlsb files are not installed.
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
