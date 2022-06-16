from typing import Any, Callable, Iterable, List, Tuple


def extract(
    query: str,
    choices: Iterable[str],
    processor: Callable[..., Any] = ...,
    scorer: Callable[..., Any] = ...,
    limit: int = ...,
) -> List[Tuple[str, int]]: ...
