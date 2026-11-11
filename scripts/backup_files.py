"""Pack/restore only ordinary files; reject path traversal and links."""
import os
from pathlib import Path, PurePosixPath
import sys
import tarfile

root = Path('/app/media')
if sys.argv[1] == 'pack':
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as archive:
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
            for name in sorted(files):
                path = Path(directory) / name
                if path.is_file() and not path.is_symlink():
                    archive.add(path, arcname=str(path.relative_to(root)), recursive=False)
else:
    count = size = 0
    with tarfile.open(fileobj=sys.stdin.buffer, mode='r|') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            count, size = count + 1, size + member.size
            if not member.isfile() or path.is_absolute() or '..' in path.parts or count > 100000 or size > 20 * 1024**3:
                raise SystemExit('Unsafe or excessive backup member.')
            destination = root.joinpath(*path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, destination.open('xb') as target:
                while chunk := source.read(65536):
                    target.write(chunk)
