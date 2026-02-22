import logging

from structlog.typing import EventDict


class SemanticSorter:
    """
    Semantic sorter sorts parameters in JSON in given order.
    """

    def __init__(self, order: list[str]) -> None:
        self._order = order

    def __call__(self, _logger: logging.Logger, _method_name: str, event_dict: EventDict) -> EventDict:
        ordered_dict = {k: v for k in self._order if (v := event_dict.pop(k, None))}
        # This can be faster if the json dumper supports the typing.Mapping protocol
        # return ChainMap(event_dict, ordered_dict)
        # ChainMap iterates its maps from the last map
        ordered_dict |= event_dict
        return ordered_dict
