"""Inspect untrusted PDFs in a bounded subprocess. Never rewrite signed bytes."""
import io
import resource
import sys

resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

FORBIDDEN = {'/JS', '/JavaScript', '/OpenAction', '/AA', '/Launch', '/RichMedia', '/EmbeddedFiles', '/EF', '/XFA'}
ACTIONS = {'/JavaScript', '/Launch', '/SubmitForm', '/ImportData', '/GoToR', '/URI'}


def inspect(data):
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted:
        return False
    seen = set()
    visited = 0

    def walk(node, depth=0):
        nonlocal visited
        visited += 1
        if depth > 50 or visited > 20000:
            raise ValueError('structure_limit')
        if isinstance(node, IndirectObject):
            key = (node.idnum, node.generation)
            if key in seen:
                return
            seen.add(key)
            walk(node.get_object(), depth + 1)
        elif isinstance(node, DictionaryObject):
            if FORBIDDEN.intersection(node.keys()) or str(node.get('/S', '')) in ACTIONS:
                raise ValueError('active_content')
            for value in node.values():
                walk(value, depth + 1)
        elif isinstance(node, ArrayObject):
            for value in node:
                walk(value, depth + 1)

    walk(reader.trailer)
    # Inspect also unreachable objects, including compressed object streams.
    refs = {(number, generation) for generation, offsets in reader.xref.items() for number in offsets if number}
    refs.update((number, 0) for number in reader.xref_objStm)
    if len(refs) > 10000:
        return False
    for number, generation in refs:
        walk(IndirectObject(number, generation, reader))
    return len(reader.pages) <= 1000


if __name__ == '__main__':
    try:
        data = sys.stdin.buffer.read(5 * 1024 * 1024 + 1)
        result = len(data) <= 5 * 1024 * 1024 and inspect(data)
    except Exception:
        result = False
    sys.exit(0 if result else 2)
