"""DownGrab - nucleo de download (Fase 1).

Uso:
    python src/downloader.py URL [-n LIGACOES] [-o PASTA]
"""

import argparse
import asyncio
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

CHUNK = 64 * 1024  # tamanho de cada bloco lido da rede (64 KB)


def split_ranges(size: int, parts: int) -> list[tuple[int, int]]:
    """Divide `size` bytes em `parts` intervalos (inicio, fim), com fim inclusivo.

    Ex: split_ranges(10, 3) -> [(0, 3), (4, 6), (7, 9)]
    """
    if size <= 0:
        raise ValueError("size tem de ser > 0")
    if parts <= 0:
        raise ValueError("parts tem de ser > 0")
    parts = min(parts, size)  # nao faz sentido ter mais partes do que bytes
    base, extra = divmod(size, parts)
    ranges = []
    start = 0
    for i in range(parts):
        length = base + (1 if i < extra else 0)  # as primeiras levam o resto
        ranges.append((start, start + length - 1))
        start += length
    return ranges


def filename_from_url(url: str) -> str:
    """Tira o nome do ficheiro do URL (ultima parte do caminho)."""
    name = unquote(Path(urlparse(url).path).name)
    return name or "download"


def unique_path(path: Path) -> Path:
    """Devolve um caminho que ainda nao existe, para nunca sobrescrever ficheiros.

    Ex: video.mp4 -> video (1).mp4 -> video (2).mp4 ...
    """
    if not path.exists():
        return path
    i = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({i}){path.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


async def get_info(client: httpx.AsyncClient, url: str) -> tuple[int | None, bool]:
    """Faz HEAD ao URL. Devolve (tamanho, aceita_ranges)."""
    r = await client.head(url)
    r.raise_for_status()
    length = r.headers.get("Content-Length")
    size = int(length) if length and length.isdigit() else None
    accepts_ranges = r.headers.get("Accept-Ranges", "").lower() == "bytes"
    return size, accepts_ranges


async def download_single(client: httpx.AsyncClient, url: str, dest: Path) -> None:
    """Descarrega o URL inteiro numa so ligacao."""
    async with client.stream("GET", url) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            async for chunk in r.aiter_bytes(CHUNK):
                f.write(chunk)


async def download_part(
    client: httpx.AsyncClient, url: str, start: int, end: int, part_path: Path
) -> None:
    """Descarrega os bytes [start, end] para um ficheiro temporario."""
    headers = {"Range": f"bytes={start}-{end}"}
    async with client.stream("GET", url, headers=headers) as r:
        r.raise_for_status()
        # 206 = Partial Content. Se vier 200, o servidor ignorou o Range.
        if r.status_code != 206:
            raise RuntimeError(f"Servidor nao respeitou o Range (status {r.status_code})")
        with open(part_path, "wb") as f:
            async for chunk in r.aiter_bytes(CHUNK):
                f.write(chunk)

    # Confirma que recebemos o tamanho certo
    expected = end - start + 1
    got = part_path.stat().st_size
    if got != expected:
        raise RuntimeError(f"Parte {part_path.name}: esperava {expected} bytes, recebi {got}")


def join_parts(part_paths: list[Path], dest: Path) -> None:
    """Junta as partes por ordem num unico ficheiro e apaga as partes."""
    with open(dest, "wb") as out:
        for part in part_paths:
            with open(part, "rb") as f:
                while chunk := f.read(CHUNK):
                    out.write(chunk)
    for part in part_paths:
        part.unlink()


async def download(
    url: str,
    dest_dir: str | Path = ".",
    connections: int = 4,
    client: httpx.AsyncClient | None = None,
) -> Path:
    """Descarrega `url` para `dest_dir` com N ligacoes. Devolve o caminho final."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = unique_path(dest_dir / filename_from_url(url))

    # Permite passar um client (util nos testes); senao cria um
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(follow_redirects=True, timeout=30)

    try:
        size, accepts_ranges = await get_info(client, url)

        # Sem tamanho conhecido ou sem suporte a Range -> uma so ligacao
        if not size or not accepts_ranges or connections <= 1:
            await download_single(client, url, dest)
            return dest

        ranges = split_ranges(size, connections)
        part_paths = [dest.with_name(f"{dest.name}.part{i}") for i in range(len(ranges))]

        try:
            # Todas as partes ao mesmo tempo
            await asyncio.gather(
                *(
                    download_part(client, url, start, end, path)
                    for (start, end), path in zip(ranges, part_paths)
                )
            )
        except Exception:
            # Em caso de erro, limpa os temporarios (so os nossos .partN)
            for p in part_paths:
                p.unlink(missing_ok=True)
            raise

        join_parts(part_paths, dest)
        return dest
    finally:
        if own_client:
            await client.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description="DownGrab - gestor de downloads")
    parser.add_argument("url", help="URL do ficheiro a descarregar")
    parser.add_argument("-n", "--connections", type=int, default=4, help="numero de ligacoes (default 4)")
    parser.add_argument("-o", "--output", default=".", help="pasta de destino (default: pasta atual)")
    args = parser.parse_args()

    path = asyncio.run(download(args.url, args.output, args.connections))
    print(f"Concluido: {path}")


if __name__ == "__main__":
    main()
