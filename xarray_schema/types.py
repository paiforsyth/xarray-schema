from typing import Dict, Iterable, Union

DimsT = Iterable[Union[str, None]]
ShapeT = Iterable[Union[int, None]]
ChunksT = Union[bool, Dict[str, Union[int, None]]]
