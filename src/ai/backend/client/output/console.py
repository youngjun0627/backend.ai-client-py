from __future__ import annotations

import sys
from typing import (
    Any,
    Callable,
    Mapping,
    Sequence,
)

from tabulate import tabulate

from ai.backend.client.cli.pretty import print_error, print_fail
from ai.backend.client.cli.pagination import (
    echo_via_pager,
    get_preferred_page_size,
    tabulate_items,
)
from .types import FieldSpec, PaginatedResult, BaseOutputHandler


class NoItems(Exception):
    pass


class ConsoleOutputHandler(BaseOutputHandler):

    def print_item(
        self,
        item: Mapping[str, Any] | None,
        fields: Sequence[FieldSpec],
    ) -> None:
        if item is None:
            print_fail("No matching entry found.")
            return
        field_map = {f.field_name: f for f in fields}
        print(tabulate(
            [
                (
                    field_map[k].humanized_name,
                    field_map[k].formatter.format_console(v, field_map[k]),
                )
                for k, v in item.items()
            ],
            headers=('Field', 'Value'),
        ))

    def print_items(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[FieldSpec],
    ) -> None:
        field_map = {f.field_name: f for f in fields}
        for idx, item in enumerate(items):
            if idx > 0:
                print("-" * 20)
            print(tabulate(
                [
                    (
                        field_map[k].humanized_name,
                        field_map[k].formatter.format_console(v, field_map[k]),
                    )
                    for k, v in item.items()
                ],
                headers=('Field', 'Value'),
            ))

    def print_list(
        self,
        items: Sequence[Mapping[str, Any]],
        fields: Sequence[FieldSpec],
        *,
        is_scalar: bool = False,
    ) -> None:
        if is_scalar:
            assert len(fields) == 1
        if sys.stdout.isatty():

            def infinite_fetch():
                current_offset = 0
                page_size = get_preferred_page_size()
                while True:
                    if len(items) == 0:
                        raise NoItems
                    if is_scalar:
                        yield from map(
                            lambda v: {fields[0].field_name: v},
                            items[current_offset:current_offset + page_size],
                        )
                    else:
                        yield from items[current_offset:current_offset + page_size]
                    current_offset += page_size
                    if current_offset >= len(items):
                        break

            try:
                echo_via_pager(
                    tabulate_items(
                        infinite_fetch(),
                        fields,
                    )
                )
            except NoItems:
                print("No matching items.")
        else:
            if is_scalar:
                for line in tabulate_items(
                    map(lambda v: {fields[0].field_name: v}, items),  # type: ignore
                    fields,
                ):
                    print(line, end="")
            else:
                for line in tabulate_items(
                    items,  # type: ignore
                    fields,
                ):
                    print(line, end="")

    def print_paginated_list(
        self,
        fetch_func: Callable[[int, int], PaginatedResult],
        initial_page_offset: int,
        page_size: int = None,
    ) -> None:
        if sys.stdout.isatty() and page_size is None:
            page_size = get_preferred_page_size()
            fields: Sequence[FieldSpec] = []

            def infinite_fetch():
                nonlocal fields
                current_offset = initial_page_offset
                while True:
                    result = fetch_func(current_offset, page_size)
                    if result.total_count == 0:
                        raise NoItems
                    current_offset += len(result.items)
                    if not fields:
                        fields.extend(result.fields)
                    yield from result.items
                    if current_offset >= result.total_count:
                        break

            try:
                echo_via_pager(
                    tabulate_items(
                        infinite_fetch(),
                        fields,
                    )
                )
            except NoItems:
                print("No matching items.")
        else:
            page_size = page_size or 20
            result = fetch_func(initial_page_offset, page_size)
            for line in tabulate_items(
                result.items,  # type: ignore
                result.fields,
            ):
                print(line, end="")

    def print_error(
        self,
        error: Exception,
    ) -> None:
        print_error(error)

    def print_fail(
        self,
        message: str,
    ) -> None:
        print_fail(message)
