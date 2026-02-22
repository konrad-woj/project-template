# Logger

Logger package exposes `configure_logger` which configures structured logging to JSON. Set `is_dev` flag to enable developer mode. Developer mode demands either `rich` or `batter-exceptions` packages installed.

## Usage

### Initial configuration

`main.py`
```python
from logger import configure_logger

if __file__ == "__main__":
    configure_logger(is_dev=True)
```


**NOTE:** The configuration should be done once per application

### Direct usage

`some_part_of_app.py`

```python
import structlog

logger: structlog.stdlib.BoundLogger = structlog.get_logger()
logger.info("xxxx", baz=5, bar="foo")
```
