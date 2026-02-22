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
        # For XLSB files, try multiple engines for maximum compatibility
        engines_to_try = [None, "openpyxl", "pyxlsb"]  # None lets pandas choose automatically

        for engine in engines_to_try:
            try:
                if engine is None:
                    df = pd.read_excel(io=io, sheet_name=sheet_name, usecols=usecols, **kwargs)
                else:
                    df = pd.read_excel(io=io, sheet_name=sheet_name, usecols=usecols, engine=engine, **kwargs)
                break  # Success, exit the loop
            except ImportError:
                # Engine not available, try next one
                continue
            except Exception as e:
                # Other error with this engine, try next one
                if engine == engines_to_try[-1]:  # Last engine in list
                    raise e  # Re-raise the error if all engines failed
                continue
        else:
            # All engines failed
            raise RuntimeError(f"Could not read XLSB file {io} with any available engine")
    else:
        # For other Excel files, use calamine for better performance
        df = pd.read_excel(io=io, sheet_name=sheet_name, usecols=usecols, engine="calamine", **kwargs)

    if usecols:
        df = df[usecols]
    return df.to_dict(orient=orient)  # type: ignore[call-arg]
