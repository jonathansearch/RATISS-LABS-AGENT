"""Événements séquencés du run (conformes à `contrats/event.schema.json`).

Chaque étape du graphe émet un événement **CloudEvents**. Le séquenceur garantit
un `seq` monotone, ce qui rend le journal replayable et détectable en cas
d'altération.

Mapping vers le contrat (CloudEvents) :

- `horodatage` → `time` ;
- `donnees`    → `data` ;
- `run_id`, `acteur` (`actor`), `task_id`, `seq` → bloc `x-ratiss` ;
- `subject`    → `task_id` (sujet de l'événement) ;
- `traceparent` → extension CloudEvents de traçage distribué (corrélation
  OpenTelemetry, contexte W3C Trace Context).

La corrélation OTel est **déterministe** : le `trace_id` dérive du `run_id` et le
`span_id` du numéro d'événement. Deux exécutions du même run produisent donc la
même trace, ce qui reste testable hors ligne.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .hashes import sha256_hex

# Types autorisés par contrats/event.schema.json
TYPES_AUTORISES = {
    "run_demarre",
    "run_termine",
    "task_demarree",
    "task_terminee",
    "outil_appele",
    "outil_resultat",
    "modele_appele",
    "approbation_demandee",
    "approbation_accordee",
    "approbation_refusee",
    "politique_appliquee",
    "erreur",
    "souvenir_lu",
    "souvenir_ecrit",
}

# Producteur des événements (CloudEvents `source`).
SOURCE = "/ratiss/runtime"

ACTEURS_AUTORISES = {"control_plane", "execution_plane", "humain", "systeme"}


@dataclass
class Evenement:
    id: str
    seq: int
    type: str
    horodatage: str
    run_id: str
    acteur: str
    task_id: str | None = None
    donnees: dict[str, Any] = field(default_factory=dict)
    traceparent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Forme conforme à `contrats/event.schema.json` (CloudEvents).

        Les attributs d'enveloppe suivent CloudEvents ; les champs propres à
        RATISS (`run_id`, `task_id`, `actor`, `seq`) sont regroupés dans
        `x-ratiss`. `subject` reprend `task_id` pour respecter la sémantique
        CloudEvents.
        """
        evt: dict[str, Any] = {
            "specversion": "1.0",
            "id": self.id,
            "source": SOURCE,
            "type": self.type,
            "time": self.horodatage,
            "data": self.donnees,
            "x-ratiss": {
                "run_id": self.run_id,
                "task_id": self.task_id,
                "actor": self.acteur,
                "seq": self.seq,
            },
        }
        if self.task_id is not None:
            evt["subject"] = self.task_id
        if self.traceparent is not None:
            evt["traceparent"] = self.traceparent
        return evt


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat()


class SequenceurEvenements:
    """Émet des événements séquencés (CloudEvents) pour un run donné."""

    def __init__(self, run_id: str, depart: int = 0) -> None:
        self.run_id = run_id
        self._seq = depart
        # Trace OTel déterministe : dérivée du run_id (32 hexadécimaux).
        self.trace_id = sha256_hex(run_id)[:32]
        self.evenements: list[Evenement] = []

    def _span_id(self, seq: int) -> str:
        return sha256_hex(f"{self.run_id}-e{seq:03d}")[:16]

    def _traceparent(self, seq: int) -> str:
        """`version-traceid-spanid-flags` (W3C Trace Context, flags=01 échantillonné)."""
        return f"00-{self.trace_id}-{self._span_id(seq)}-01"

    @classmethod
    def depuis_journal(cls, run_id: str, journal: list[dict[str, Any]]) -> "SequenceurEvenements":
        """Reconstruit un séquenceur à partir d'un journal déjà émis.

        Utilisé à la reprise : la numérotation continue, sans dupliquer les
        identifiants déjà présents.
        """
        seq = cls(run_id)
        for i, d in enumerate(journal, start=1):
            xr = d.get("x-ratiss") or {}
            seq.evenements.append(
                Evenement(
                    id=d["id"],
                    seq=xr.get("seq", i),
                    type=d["type"],
                    horodatage=d["time"],
                    run_id=xr["run_id"],
                    acteur=xr["actor"],
                    task_id=xr.get("task_id"),
                    donnees=d.get("data") or {},
                    traceparent=d.get("traceparent"),
                )
            )
        seq._seq = len(journal)
        return seq

    def emettre(
        self,
        type: str,
        acteur: str,
        task_id: str | None = None,
        donnees: dict[str, Any] | None = None,
    ) -> Evenement:
        if type not in TYPES_AUTORISES:
            raise ValueError(f"Type d'événement non autorisé : {type!r}")
        if acteur not in ACTEURS_AUTORISES:
            raise ValueError(f"Acteur non autorisé : {acteur!r}")
        self._seq += 1
        evt = Evenement(
            id=f"{self.run_id}-e{self._seq:03d}",
            seq=self._seq,
            type=type,
            horodatage=_maintenant(),
            run_id=self.run_id,
            acteur=acteur,
            task_id=task_id,
            donnees=donnees or {},
            traceparent=self._traceparent(self._seq),
        )
        self.evenements.append(evt)
        return evt

    def journal_dict(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.evenements]
