import asyncio

import httpx
import pytest

from downloader import download, split_ranges, unique_path

DATA = bytes(range(256)) * 40  # 10240 bytes de dados de teste


# ---------- divisao em partes ----------

def test_split_exato():
    assert split_ranges(9, 3) == [(0, 2), (3, 5), (6, 8)]


def test_split_com_resto():
    assert split_ranges(10, 3) == [(0, 3), (4, 6), (7, 9)]


def test_split_cobre_tudo_sem_buracos():
    size = 10_007
    ranges = split_ranges(size, 7)
    assert ranges[0][0] == 0
    assert ranges[-1][1] == size - 1
    for (_, end), (start, _) in zip(ranges, ranges[1:]):
        assert start == end + 1
    assert sum(e - s + 1 for s, e in ranges) == size


def test_split_mais_partes_que_bytes():
    assert split_ranges(2, 5) == [(0, 0), (1, 1)]


def test_split_valores_invalidos():
    with pytest.raises(ValueError):
        split_ranges(0, 4)
    with pytest.raises(ValueError):
        split_ranges(10, 0)


# ---------- nunca sobrescrever ----------

def test_unique_path(tmp_path):
    f = tmp_path / "a.txt"
    assert unique_path(f) == f
    f.write_text("x")
    assert unique_path(f) == tmp_path / "a (1).txt"


# ---------- download completo com servidor falso ----------

def fake_server(accept_ranges=True):
    """Cria um transporte httpx que simula um servidor HTTP."""

    def handler(request: httpx.Request) -> httpx.Response:
        headers = {"Content-Length": str(len(DATA))}
        if accept_ranges:
            headers["Accept-Ranges"] = "bytes"
        if request.method == "HEAD":
            return httpx.Response(200, headers=headers)
        rng = request.headers.get("Range")
        if rng and accept_ranges:
            start, end = map(int, rng.removeprefix("bytes=").split("-"))
            return httpx.Response(206, content=DATA[start : end + 1])
        return httpx.Response(200, content=DATA)

    return httpx.MockTransport(handler)


def run_download(tmp_path, accept_ranges=True, connections=4):
    async def go():
        async with httpx.AsyncClient(transport=fake_server(accept_ranges)) as client:
            return await download("http://teste/ficheiro.bin", tmp_path, connections, client)

    return asyncio.run(go())


def test_download_em_partes(tmp_path):
    path = run_download(tmp_path, connections=4)
    assert path.read_bytes() == DATA
    assert list(tmp_path.glob("*.part*")) == []  # temporarios apagados


def test_download_sem_range(tmp_path):
    path = run_download(tmp_path, accept_ranges=False)
    assert path.read_bytes() == DATA


def test_download_nao_sobrescreve(tmp_path):
    existente = tmp_path / "ficheiro.bin"
    existente.write_bytes(b"do utilizador")
    path = run_download(tmp_path)
    assert existente.read_bytes() == b"do utilizador"
    assert path.name == "ficheiro (1).bin"
    assert path.read_bytes() == DATA
