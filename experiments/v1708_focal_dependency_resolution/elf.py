"""Read ELF64 x86-64 dynamic dependencies as data; never load the object."""
import hashlib
import struct
from pathlib import Path


def dynamic_metadata(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), "REGULAR_ELF_REQUIRED"
    data = path.read_bytes()
    assert 64 <= len(data) <= 32 * 1024**2, "ELF_FILE_SIZE"
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", data)
    ident = header[0]
    assert ident[:4] == b"\x7fELF" and ident[4:7] == b"\x02\x01\x01", "ELF64_LE_ONLY"
    assert header[1] in (2, 3) and header[2] == 62 and header[3] == 1, "X86_64_ONLY"
    offset, stride, count = header[5], header[9], header[10]
    assert stride == 56 and 0 < count <= 128 and offset + stride * count <= len(data), "PROGRAM_HEADERS"
    loads, dynamics = [], []
    for index in range(count):
        segment = struct.unpack_from("<IIQQQQQQ", data, offset + stride * index)
        kind, _, file_offset, address, _, file_size, memory_size, _ = segment
        assert file_offset + file_size <= len(data) and file_size <= memory_size, "SEGMENT_BOUNDS"
        if kind == 1:
            loads.append((address, file_offset, file_size))
        elif kind == 2:
            dynamics.append((file_offset, file_size))
    assert len(dynamics) == 1, "ONE_DYNAMIC_SEGMENT_REQUIRED"
    offset, size = dynamics[0]
    assert size % 16 == 0 and size <= 1024**2, "DYNAMIC_SEGMENT_SIZE"
    tags, terminated = [], False
    for position in range(offset, offset + size, 16):
        tag, value = struct.unpack_from("<qQ", data, position)
        if tag == 0:
            terminated = True
            break
        tags.append((tag, value))
    assert terminated, "DYNAMIC_NULL_TERMINATOR"
    table = [value for tag, value in tags if tag == 5]
    sizes = [value for tag, value in tags if tag == 10]
    assert len(table) == len(sizes) == 1 and 0 < sizes[0] <= 2 * 1024**2, "DYNAMIC_STRING_TABLE"
    address, length = table[0], sizes[0]
    mappings = [file_offset + address - virtual for virtual, file_offset, file_size in loads
                if virtual <= address and address + length <= virtual + file_size]
    assert len(mappings) == 1, "STRING_TABLE_FILE_MAPPING"
    strings = data[mappings[0]:mappings[0] + length]

    def text(at):
        assert 0 <= at < len(strings), "STRING_OFFSET"
        end = strings.find(b"\0", at)
        assert end != -1 and end - at <= 4096, "STRING_TERMINATOR"
        return strings[at:end].decode("utf-8", errors="strict")

    needed = [text(value) for tag, value in tags if tag == 1]
    assert len(needed) <= 256 and all(name and "/" not in name for name in needed), "NEEDED_LIBRARY_NAME"
    sonames = [text(value) for tag, value in tags if tag == 14]
    assert len(sonames) <= 1, "ONE_SONAME"
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                ELF_class=64, architecture="x86_64", needed=needed,
                soname=sonames[0] if sonames else None,
                rpath=[text(value) for tag, value in tags if tag == 15],
                runpath=[text(value) for tag, value in tags if tag == 29],
                library_loaded=False, library_code_executed=False, models=0)
