#!/usr/bin/env python

# Copyright (c) 2018 Florian Léger
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import struct
from argparse import ArgumentParser
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Tuple, BinaryIO, Optional, Iterable


@dataclass
class FileObject:
    """
    FileObject structure

    Contains the offset of the file within the LPACK bundle, its size and file name.
    """
    offset: int
    size: int
    compressed_size: int
    compressed: bool
    filename: str


class LPAKParser:
    """
    Parses an LPAK file.
    """

    def __init__(self, file: BinaryIO) -> None:
        self.file = file
        # Check header to get endianness
        header = struct.unpack_from('<4s', self.file.read(4))
        if header[0] == b"LPAK":
            self.endianness = ">"
        elif header[0] == b"KAPL":
            self.endianness = "<"
        else:
            raise ValueError("Not a LPAK file")
        self.file_objects = []
        self.parse_files()

    def unpack(self, struct_format: str) -> Tuple:
        """
        Unpack data from file.

        :param struct_format: struct format of the data to unpack without endianness notation
        :return: unpacked data
        """
        full_format = self.endianness + struct_format
        size = struct.calcsize(full_format)
        return struct.unpack_from(full_format, self.file.read(size))

    def parse_files(self) -> None:
        """
        Populate file_objects
        """
        self.file.seek(6)
        version = self.unpack("H")[0]
        if version >= 16320:
            # TODO: implement post-Full Throttle format
            raise ValueError("Post-Full Throttle file format no supported")
        self.parse_files_v1()

    def parse_files_v1(self):
        """
        Parse pre-Full Throttle format
        """
        size_of_file_record = 20
        self.file.seek(12)
        start_of_file_entries, start_of_file_names, start_of_data, _, size_of_file_entries, _, _ = self.unpack("I" * 7)
        num_files = size_of_file_entries // size_of_file_record
        self.file.seek(start_of_file_entries)

        current_name_offset = 0
        for i in range(num_files):
            self.file.seek(start_of_file_entries + i * size_of_file_record)
            offset, name_offset, size, compressed_size, compressed = self.unpack("I" * 5)
            self.file.seek(start_of_file_names + current_name_offset)
            file_name = self.unpack("255s")[0].split(b"\0")[0]
            current_name_offset += len(file_name) + 1  # Null-terminated string
            self.file_objects.append(FileObject(offset + start_of_data, size, compressed_size, compressed != 0,
                                                file_name.decode()))


def filter_file_objects(file_objects: Iterable[FileObject], include: Optional[str] = None) -> Iterable[FileObject]:
    """
    Filter file objects according a glob pattern

    :param file_objects: file objects to filter
    :param include: optional glob filtering pattern
    :return: iterable of file objects
    """
    return file_objects if include is None else filter(lambda f: fnmatchcase(f.filename, include), file_objects)


def action_list(file: Path, include: Optional[str] = None, *args) -> None:
    """
    List files contained in a bundle

    :param file: path to the bundle file
    :param include: optional filtering glob pattern
    :return: None
    """
    with file.open('rb') as lpak:
        parser = LPAKParser(lpak)
        for f in filter_file_objects(parser.file_objects, include):
            print(f.filename)


def action_extract(file: Path, include: Optional[str] = None, overwrite: bool = False, *args) -> None:
    """
    Extract bundled files in current directory

    :param file: path to the bundle file
    :param include: optional filtering glob pattern
    :param overwrite: if true will overwrite existing files
    :return: None
    """
    with file.open('rb') as lpak:
        parser = LPAKParser(lpak)
        for f in filter_file_objects(parser.file_objects, include):
            if f.compressed:
                print(f"{f.filename}: compressed file not supported, skipping")
                continue
            output = Path(f.filename)
            output.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            output.touch(mode=0o644, exist_ok=overwrite)
            lpak.seek(f.offset)
            output.write_bytes(lpak.read(f.size))


def cli(*args) -> Optional[int]:
    """
    CLI entry-point

    :param args: command line arguments
    :return: return code
    """
    parser = ArgumentParser(description="This will list or extract files from a DoubleFine LPAK bundle as found in"
                                        " Day of the Tentacle Remastered.")
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--list", "-l", dest="action", action="store_const", const=action_list,
                              help="list bundle content")
    action_group.add_argument("--extract", "-x", dest="action", action="store_const", const=action_extract,
                              help="extract bundle content")
    parser.add_argument("--filter", "-F", metavar="PATTERN", dest="include", type=str, default=None,
                        help="extract only files that match the given pattern")
    parser.add_argument("--overwrite", "-o", dest="overwrite", action="store_true", help="overwrite existing files")
    parser.add_argument("file", help="bundle file", type=Path)
    parsed_args = parser.parse_args(args)
    parsed_args.action(parsed_args.file, parsed_args.include, parsed_args.overwrite)
    return 0


if __name__ == '__main__':
    import sys
    exit(cli(*sys.argv[1:]))
