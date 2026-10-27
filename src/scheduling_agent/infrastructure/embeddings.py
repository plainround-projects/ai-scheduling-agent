"""Embedding adapters: an OpenAI-compatible server, a recording of its answers, and the replay of that recording."""

from __future__ import annotations

import base64
import hashlib
import json
import struct
import threading
from collections.abc import Sequence
from pathlib import Path

import httpx

from scheduling_agent.application.ports import Embedder
from scheduling_agent.domain.errors import PermanentModelError, RecordingMissing, TransientModelError


def text_key(text: str) -> str:
    """The recording key of a text: its SHA-256. The model name is not part of it."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pack(vector: Sequence[float]) -> str:
    return base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode("ascii")


def _unpack(blob: str) -> list[float]:
    raw = base64.b64decode(blob)
    return list(struct.unpack(f"<{len(raw) // 4}f", raw))


class OpenAICompatibleEmbedder:
    """Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide."""

    def __init__(self, http: httpx.Client, base_url: str, model: str, api_key: str | None = None) -> None:
        self._http = http
        self._url = f"{base_url.rstrip('/')}/embeddings"
        self._model = model
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    @property
    def name(self) -> str:
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            reply = self._http.post(self._url, json={"model": self._model, "input": list(texts)}, headers=self._headers)
        except httpx.TransportError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        if reply.status_code == 429 or reply.status_code >= 500:
            raise TransientModelError(f"HTTP {reply.status_code}")
        if reply.status_code >= 400:
            raise PermanentModelError(f"HTTP {reply.status_code}: {reply.text[:200]}")
        try:
            data = sorted(reply.json()["data"], key=lambda item: item["index"])
            vectors = [[float(x) for x in item["embedding"]] for item in data]
        except (KeyError, TypeError, ValueError) as error:
            raise PermanentModelError(f"unexpected embeddings response: {error!r}") from error
        if len(vectors) != len(texts):
            raise PermanentModelError(f"asked for {len(texts)} embeddings, got {len(vectors)}")
        return vectors


class EmbeddingStore:
    """A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._vectors: dict[str, list[float]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
        for file in files:
            with file.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        entry = json.loads(line)
                        self._vectors[entry["key"]] = _unpack(entry["vector"])
        self._append_to = path / "embeddings.jsonl" if path.is_dir() else path

    def __len__(self) -> int:
        return len(self._vectors)

    def get(self, key: str) -> list[float] | None:
        return self._vectors.get(key)

    def put(self, key: str, vector: Sequence[float], model: str) -> None:
        with self._lock:
            self._vectors[key] = list(vector)
            self._append_to.parent.mkdir(parents=True, exist_ok=True)
            with self._append_to.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"key": key, "model": model, "vector": _pack(vector)}) + "\n")
                handle.flush()


class RecordedEmbedder:
    """Replays recorded vectors. A text nobody embedded raises `RecordingMissing`."""

    def __init__(self, store: EmbeddingStore, name: str = "recorded") -> None:
        self._store = store
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vector = self._store.get(text_key(text))
            if vector is None:
                raise RecordingMissing(
                    f"no recorded embedding for a text of {len(text)} characters starting {text[:40]!r}; "
                    "run `make record` against the embedding model to refresh the fixtures"
                )
            out.append(vector)
        return out


class RecordingEmbedder:
    """Wraps a live embedder and writes each new vector into the recording; known texts are replayed."""

    def __init__(self, inner: Embedder, store: EmbeddingStore) -> None:
        self._inner = inner
        self._store = store

    @property
    def name(self) -> str:
        return self._inner.name

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        unknown = [t for t in dict.fromkeys(texts) if self._store.get(text_key(t)) is None]
        if unknown:
            for text, vector in zip(unknown, self._inner.embed(unknown), strict=True):
                self._store.put(text_key(text), vector, self._inner.name)
        return [self._store.get(text_key(t)) or [] for t in texts]
