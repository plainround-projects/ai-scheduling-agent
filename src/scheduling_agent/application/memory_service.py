"""Long-term memory with a write policy: only what a person states about themselves, one fact per topic."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from scheduling_agent.application.ports import Clock, Embedder, MemoryStore
from scheduling_agent.domain.memory import Fact, compact, parse_statement, rank_facts
from scheduling_agent.domain.retrieval import cosine

_log = logging.getLogger(__name__)


class MemoryService:
    """Remember what people say, recall the three most relevant facts for a task, forget on request."""

    def __init__(
        self, store: MemoryStore, embedder: Embedder, clock: Clock, people: Sequence[str], top: int = 3
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._clock = clock
        self._people = tuple(people)
        self._top = top

    def remember(self, person: str, statement: str, session: str) -> Fact | None:
        """Store a statement a person made about themselves. A sentence that states no usable fact is not kept.

        A fact about the same person and topic replaces the old one, so a changed preference leaves no trace of the
        old value in recall or in storage.
        """
        today = self._clock.today()
        fact = parse_statement(person, statement, session, today)
        if fact is None:
            _log.info("statement not kept", extra={"fields": {"person": person, "session": session}})
            return None
        existing = [f for f in self._store.facts() if f.person == person]
        others = [f for f in self._store.facts() if f.person != person]
        self._store.replace([*others, *compact(existing, fact, today)])
        _log.info("fact stored", extra={"fields": {"person": person, "kind": fact.kind.value, "session": session}})
        return fact

    def recall(self, task: str) -> list[Fact]:
        """The most relevant live facts for a task: those of the people it names, ranked by similarity and recency."""
        today = self._clock.today()
        named = [p for p in self._people if p in task.lower()]
        candidates = [f for f in self._store.facts() if f.alive(today) and (not named or f.person in named)]
        if not candidates:
            return []
        vectors = self._embedder.embed([task, *[f.text for f in candidates]])
        scored = [(fact, cosine(vectors[0], vector)) for fact, vector in zip(candidates, vectors[1:], strict=True)]
        return rank_facts(scored, today, self._top)

    def facts(self) -> list[Fact]:
        """Everything remembered, for a person to inspect."""
        return self._store.facts()

    def forget(self, person: str) -> int:
        """Delete every fact about a person from storage; returns how many were removed."""
        facts = self._store.facts()
        kept = [f for f in facts if f.person != person]
        self._store.replace(kept)
        return len(facts) - len(kept)
