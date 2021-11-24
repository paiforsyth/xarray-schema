from typing import Any, Dict, List, Union

import numpy as np

from .base import BaseSchema, SchemaError
from .types import ChunksT, DimsT, ShapeT


class DTypeSchema(BaseSchema):

    _json_schema = {'type': 'string'}

    def __init__(self, dtype: np.typing.DTypeLike) -> None:
        if dtype in [np.floating, np.integer, np.signedinteger, np.unsignedinteger, np.generic]:
            self.dtype = dtype
        else:
            self.dtype = np.dtype(dtype)

    def validate(self, dtype: np.typing.DTypeLike) -> None:
        '''Validate dtype

        Parameters
        ----------
        dtype : Any
            Dtype of the DataArray.
        '''
        if not np.issubdtype(dtype, self.dtype):
            raise SchemaError(f'dtype {dtype} != {self.dtype}')

    @property
    def json(self) -> str:
        try:
            return self.dtype.str
        except AttributeError:
            # this handles generic dtypes
            return self.dtype.__name__


class DimsSchema(BaseSchema):

    _json_schema = {'type': 'array', 'items': {'type': ['string', 'null']}}

    def __init__(self, dims: DimsT) -> None:
        self.dims = dims

    def validate(self, dims: DimsT) -> None:
        '''Validate dimensions

        Parameters
        ----------
        dims : Tuple[Union[str, None]]
            Dimensions of the DataArray. `None` may be used as a wildcard value.
        '''
        if len(self.dims) != len(dims):
            raise SchemaError(f'length of dims does not match: {len(dims)} != {len(self.dims)}')

        for i, (actual, expected) in enumerate(zip(dims, self.dims)):
            if expected is not None and actual != expected:
                raise SchemaError(f'dim mismatch in axis {i}: {actual} != {expected}')

    @property
    def json(self) -> list:
        return list(self.dims)


class ShapeSchema(BaseSchema):

    _json_schema = {'type': 'array', 'items': {'type': ['int', 'null']}}

    def __init__(self, shape: ShapeT) -> None:
        self.shape = shape

    def validate(self, shape: ShapeT) -> None:
        '''Validate shape

        Parameters
        ----------
        shape : ShapeT
            Shape of the DataArray. `None` may be used as a wildcard value.
        '''
        if len(self.shape) != len(shape):
            raise SchemaError(
                f'number of dimensions in shape ({len(shape)}) != da.ndim ({len(self.shape)})'
            )

        for i, (actual, expected) in enumerate(zip(shape, self.shape)):
            if expected is not None and actual != expected:
                raise SchemaError(f'shape mismatch in axis {i}: {actual} != {expected}')

    @property
    def json(self) -> list:
        return list(self.shape)


class NameSchema(BaseSchema):

    _json_schema = {'type': 'string'}

    def __init__(self, name: str) -> None:
        self.name = name

    def validate(self, name: str) -> None:
        '''Validate name

        Parameters
        ----------
        name : str, optional
            Name of the DataArray. Currently requires an exact string match.
        '''
        # TODO: support regular expressions
        # - http://json-schema.org/understanding-json-schema/reference/regular_expressions.html
        # - https://docs.python.org/3.9/library/re.html
        if self.name != name:
            raise SchemaError(f'name {name} != {self.name}')

    @property
    def json(self) -> str:
        return self.name


class ChunksSchema(BaseSchema):

    _json_schema = {'type': 'object'}  # TODO: fill this in with patternProperties

    def __init__(self, chunks: ChunksT) -> None:
        self.chunks = chunks

    def validate(self, chunks: ChunksT, dims: tuple, shape: tuple) -> None:
        '''Validate chunks

        Parameters
        ----------
        chunks : bool or dict
            Chunks of the DataArray.
        dims : tuple of str
            Dimension keys from array.
        shape : tuple of int
            Shape of array.
        '''
        if self.chunks is True:
            if chunks is None:
                raise SchemaError('expected array to be chunked but it is not')
        elif self.chunks is False:
            if chunks is not None:
                raise SchemaError('expected unchunked array but it is chunked')
        else:  # chunks is dict-like
            dim_chunks = dict(zip(dims, chunks))
            dim_sizes = dict(zip(dims, shape))
            # check whether chunk sizes are regular because we assume the first chunk to be representative below
            for key, ec in self.chunks.items():
                if isinstance(ec, int):
                    # handles case of expected chunksize is shorthand of -1 which translates to the full length of dimension
                    if ec < 0:
                        ec = dim_sizes[key]
                        # grab the first entry in da's tuple of chunks to be representative (since we've checked above that they're regular)
                    ac = dim_chunks[key][0]
                    if ac != ec:
                        raise SchemaError(f'{key} chunks did not match: {ac} != {ec}')

                else:  # assumes ec is an iterable
                    ac = dim_chunks[key]
                    if tuple(ac) != tuple(ec):
                        raise SchemaError(f'{key} chunks did not match: {ac} != {ec}')

    @property
    def json(self) -> Union[str, Dict[str, Union[bool, int, List[int]]]]:
        if isinstance(self.chunks, bool):
            return self.chunks
        else:
            obj = {}
            for key, val in self.chunks.items():
                if isinstance(val, tuple):
                    obj[key] = list(val)
                else:
                    obj[key] = val
            return obj


class ArrayTypeSchema(BaseSchema):

    _json_schema = {'type': 'string'}

    def __init__(self, array_type: Any) -> None:
        self.array_type = array_type

    def validate(self, array: Any) -> None:
        '''Validate array_type

        Parameters
        ----------
        array : array_like
            array_type of the DataArray. `None` may be used as a wildcard value.
        '''
        if not isinstance(array, self.array_type):
            raise SchemaError(f'array_type {type(array)} != {self.array_type}')

    @property
    def json(self) -> str:
        return str(self.array_type)
