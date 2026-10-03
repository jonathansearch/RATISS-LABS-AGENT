#!/usr/bin/env python3
"""RATISS LABS AGENT — ÉTAPE C : enregistrement idempotent des outils MCP.

Lit tools.yaml et enregistre dans ContextForge (MONTAGE étape 3) :
  1. chaque serveur `actif: true` comme GATEWAY (POST /admin/gateways, JSON,
     transport STREAMABLEHTTP) — ContextForge découvre et enregistre
     automatiquement les outils au moment de l'enregistrement ;
  2. le serveur virtuel `ratiss-v1` (POST /admin/servers, formulaire
     associatedTools) regroupant les outils des serveurs actifs ;
  3. il VÉRIFIE : la liste tools/list de l'endpoint virtuel
     /servers/<UUID>/mcp (Streamable HTTP + Bearer) doit correspondre
     exactement aux outils attendus.

Idempotence : relancer ne crée pas de doublon (les serveurs existants sont
repérés par nom ; si l'URL a changé, mise à jour via la route d'édition).
Aucune clé ne s'affiche : les jetons sont lus depuis l'environnement et
jamais imprimés. Aucune invention : si le gateway est injoignable, échec
honnête avec code de sortie != 0.

Usage :
  python scripts/enregistrer_outils.py                     # enregistrer + vérifier
  python scripts/enregistrer_outils.py --verifier-seule    # vérifier seulement
  python scripts/enregistrer_outils.py --url http://127.0.0.1:4444 --tools tools.yaml

Variables d'environnement attendues (fichier .env, jamais dans git) :
  CONTEXTFORGE_ADMIN_EMAIL, CONTEXTFORGE_ADMIN_PASSWORD (admin plateforme),
  GITHUB_TOKEN (optionnel — active le serveur github de tools.yaml).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml

RACINE = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------
# Lecture de tools.yaml (validation stricte, fail-closed)
# --------------------------------------------------------------------------
CHAMPS_REQUIS = {"nom", "transport", "url", "service_docker"}


def charger_tools_yaml(chemin: Path) -> dict[str, Any]:
    """Charge et valide tools.yaml. Lève ValueError sur toute anomalie."""
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    if not isinstance(brut, dict):
        raise ValueError(f"{chemin}: document YAML inattendu")
    if brut.get("version") != 1:
        raise ValueError(f"{chemin}: version != 1 (refusé)")
    virtuel = brut.get("serveur_virtuel") or {}
    if not virtuel.get("nom"):
        raise ValueError(f"{chemin}: serveur_virtuel.nom manquant")
    if virtuel.get("outils_autorises") not in ("tous",):
        raise ValueError(
            f"{chemin}: outils_autorises={virtuel.get('outils_autorises')!r} non supporté "
            "(V1 : 'tous' uniquement, rien d'inventé)"
        )
    serveurs = brut.get("serveurs") or []
    if not serveurs:
        raise ValueError(f"{chemin}: aucun serveur déclaré")
    noms = set()
    for i, srv in enumerate(serveurs):
        manquants = CHAMPS_REQUIS - set(srv or {})
        if manquants:
            raise ValueError(f"{chemin}: serveur #{i} sans champs {sorted(manquants)}")
        if srv["nom"] in noms:
            raise ValueError(f"{chemin}: serveur dupliqué {srv['nom']!r}")
        noms.add(srv["nom"])
    return brut


def serveurs_actifs(inv: dict[str, Any]) -> list[dict[str, Any]]:
    """Les serveurs à enregistrer : actif=true, OU activable si l'env existe."""
    resultats = []
    for srv in inv["serveurs"]:
        if srv.get("actif"):
            resultats.append(srv)
        elif srv.get("activable_si_env"):
            if os.environ.get(srv["activable_si_env"], "").strip():
                resultats.append({**srv, "actif": True})
    return resultats


# --------------------------------------------------------------------------
# Résolution / comparaisons (fonctions pures, testables sans service)
# --------------------------------------------------------------------------
def planifier_gateways(
    desires: list[dict[str, Any]], existants: list[dict[str, Any]]
) -> list[tuple[str, dict[str, Any] | None, str]]:
    """Plan d'actions par serveur : (nom, existant_ou_None, action).

    action ∈ {"creer", "maj", "inchangé"}. Idempotent : aucun doublon créé.
    """
    par_nom = {g.get("name"): g for g in existants}
    plan = []
    for srv in desires:
        existant = par_nom.get(srv["nom"])
        if existant is None:
            plan.append((srv["nom"], None, "creer"))
        else:
            url_ok = (existant.get("url") or "").rstrip("/") == srv["url"].rstrip("/")
            if url_ok:
                plan.append((srv["nom"], existant, "inchangé"))
            else:
                plan.append((srv["nom"], existant, "maj"))
    return plan


def outils_attendus(
    outils_admin: list[dict[str, Any]], gateways_cibles: dict[str, str]
) -> set[str]:
    """Noms d'outils attendus dans ratiss-v1 : les outils dont le gateway_id
    appartient à nos gateways (id -> nom donné par gateways_cibles)."""
    ids_cibles = set(gateways_cibles)
    return {
        (o.get("name") or "")
        for o in outils_admin
        if (o.get("gateway_id") or o.get("gatewayId")) in ids_cibles
    }


def comparer_listes(
    attendus: set[str], observes: set[str]
) -> tuple[bool, set[str], set[str]]:
    """(ok, manquants, en_trop) — le contrôle étape C est exact, sans indulgence."""
    return (attendus == observes, attendus - observes, observes - attendus)


# --------------------------------------------------------------------------
# Client ContextForge minimal (stdlib, jetons jamais imprimés)
# --------------------------------------------------------------------------
class ContextForge:
    def __init__(self, base_url: str, jeton: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.jeton = jeton

    def _requete(
        self,
        methode: str,
        chemin: str,
        *,
        json_body: dict | None = None,
        form: list[tuple[str, str]] | None = None,
    ) -> Any:
        en_tetes = {"Accept": "application/json"}
        if self.jeton:
            en_tetes["Authorization"] = f"Bearer {self.jeton}"
        donnees = None
        if json_body is not None:
            en_tetes["Content-Type"] = "application/json"
            donnees = json.dumps(json_body).encode()
        elif form is not None:
            en_tetes["Content-Type"] = "application/x-www-form-urlencoded"
            donnees = urllib.parse.urlencode(form, doseq=True).encode()
        req = urllib.request.Request(
            self.base_url + chemin, data=donnees, headers=en_tetes, method=methode
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as rep:
                corps = rep.read().decode("utf-8")
                return json.loads(corps) if corps else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"HTTP {e.code} sur {chemin} : {detail}") from e

    def login(self, email: str, mot_de_passe: str) -> None:
        rep = self._requete(
            "POST",
            "/auth/email/login",
            json_body={"email": email, "password": mot_de_passe},
        )
        jeton = (rep or {}).get("access_token")
        if not jeton:
            raise RuntimeError("login échoué : pas d'access_token dans la réponse")
        self.jeton = jeton  # jeton en mémoire uniquement, jamais affiché

    def _lister_pagines(self, chemin: str) -> list[dict[str, Any]]:
        elements: list[dict[str, Any]] = []
        page = 1
        while page <= 50:  # garde-fou anti-boucle
            rep = self._requete(
                "GET", f"{chemin}?page={page}&per_page=100&include_inactive=true"
            )
            lot = (rep or {}).get("items") or []
            elements.extend(lot)
            total_pages = (rep or {}).get("pages")
            if not lot or (isinstance(total_pages, int) and page >= total_pages):
                break
            page += 1
        return elements

    def gateways(self) -> list[dict[str, Any]]:
        return self._lister_pagines("/admin/gateways")

    def creer_gateway(self, srv: dict[str, Any]) -> dict[str, Any]:
        corps: dict[str, Any] = {
            "name": srv["nom"],
            "url": srv["url"],
            "transport": srv["transport"],
            "description": srv.get("description", ""),
        }
        if srv.get("auth_type") and srv.get("auth_token_env"):
            # Jeton depuis l'environnement uniquement (jamais depuis le YAML).
            corps["auth_type"] = srv["auth_type"]
            corps["auth_token"] = os.environ.get(srv["auth_token_env"], "")
        return self._requete("POST", "/admin/gateways", json_body=corps)

    def maj_gateway(self, gateway_id: str, srv: dict[str, Any]) -> None:
        # Route d'édition de l'admin UI : accepte du formulaire urlencodé.
        self._requete(
            "POST",
            f"/admin/gateways/{gateway_id}/edit",
            form=[
                ("name", srv["nom"]),
                ("url", srv["url"]),
                ("description", srv.get("description", "")),
            ],
        )

    def outils(self) -> list[dict[str, Any]]:
        return self._lister_pagines("/admin/tools")

    def serveurs_virtuels(self) -> list[dict[str, Any]]:
        return self._lister_pagines("/admin/servers")

    def creer_serveur_virtuel(
        self, nom: str, description: str, ids_outils: list[str]
    ) -> dict[str, Any]:
        # POST /admin/servers : formulaire (champ associéTools répété).
        form: list[tuple[str, str]] = [
            ("name", nom),
            ("description", description),
            ("visibility", "public"),
        ]
        form.extend(("associatedTools", i) for i in ids_outils)
        return self._requete("POST", "/admin/servers", form=form)

    def resynchroniser_serveur_virtuel(
        self, serveur_id: str, nom: str, description: str, ids_outils: list[str]
    ) -> None:
        form: list[tuple[str, str]] = [
            ("name", nom),
            ("description", description),
        ]
        form.extend(("associatedTools", i) for i in ids_outils)
        self._requete("POST", f"/admin/servers/{serveur_id}/edit", form=form)

    def outils_du_serveur_virtuel(self, chemin_mcp: str) -> set[str]:
        """tools/list sur /servers/<UUID>/mcp (Streamable HTTP + Bearer)."""
        en_tetes = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.jeton}",
        }
        req = urllib.request.Request(
            self.base_url + chemin_mcp,
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(),
            headers=en_tetes,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as rep:
            corps = rep.read().decode("utf-8")
        # Le corps peut être JSON direct ou du SSE (lignes data: ...).
        charge = _extraire_json_rpc(corps)
        resultat = (charge or {}).get("result") or {}
        return {t.get("name", "") for t in (resultat.get("tools") or [])}


def _extraire_json_rpc(corps: str) -> dict[str, Any] | None:
    """Accepte un corps JSON pur OU un flux SSE (data: {...})."""
    corps = corps.strip()
    if corps.startswith("{"):
        return json.loads(corps)
    for ligne in corps.splitlines():
        ligne = ligne.strip()
        if ligne.startswith("data:"):
            brut = ligne[5:].strip()
            if brut and brut != "[DONE]":
                return json.loads(brut)
    return None


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Enregistrement idempotent des outils MCP (étape C).")
    p.add_argument("--url", default=os.environ.get("MCPGATEWAY_URL", "http://127.0.0.1:4444"))
    p.add_argument("--tools", default=str(RACINE / "tools.yaml"))
    p.add_argument("--verifier-seule", action="store_true",
                   help="ne rien créer/modifier : vérifier ratiss-v1 contre tools.yaml")
    args = p.parse_args(argv)

    inv = charger_tools_yaml(Path(args.tools))
    actifs = serveurs_actifs(inv)
    print(f"[tools.yaml] {len(actifs)} serveur(s) actif(s) : {[s['nom'] for s in actifs]}")

    email = os.environ.get("CONTEXTFORGE_ADMIN_EMAIL", "").strip()
    mot_de_passe = os.environ.get("CONTEXTFORGE_ADMIN_PASSWORD", "").strip()
    if not email or not mot_de_passe:
        print("ERREUR : CONTEXTFORGE_ADMIN_EMAIL / CONTEXTFORGE_ADMIN_PASSWORD absents du .env.")
        return 1

    cf = ContextForge(args.url)
    try:
        cf.login(email, mot_de_passe)
        print("[login] admin plateforme authentifié (jeton en mémoire, non affiché).")
    except Exception as e:  # noqa: BLE001 — échec honnête, message complet
        print(f"ERREUR login : {e}")
        return 1

    # 1. Gateways ------------------------------------------------------------
    existants = cf.gateways()
    plan = planifier_gateways(actifs, existants)
    gateways_cibles: dict[str, str] = {}
    for nom, existant, action in plan:
        if action == "creer":
            cf.creer_gateway(next(s for s in actifs if s["nom"] == nom))
            print(f"[gateway] {nom} : créé.")
        elif action == "maj":
            cf.maj_gateway(existant["id"], next(s for s in actifs if s["nom"] == nom))
            print(f"[gateway] {nom} : URL mise à jour.")
        else:
            print(f"[gateway] {nom} : inchangé.")
    for g in cf.gateways():
        if g.get("name") in {s["nom"] for s in actifs}:
            gateways_cibles[g["id"]] = g["name"]

    # 2. Serveur virtuel -----------------------------------------------------
    virtuel_cfg = inv["serveur_virtuel"]
    outils_admin = cf.outils()
    attendus = outils_attendus(outils_admin, gateways_cibles)
    if not attendus:
        print("ERREUR : aucun outil découvert pour les gateways cibles — rien n'est créé.")
        return 1
    ids_outils = [
        o["id"]
        for o in outils_admin
        if (o.get("gateway_id") or o.get("gatewayId")) in gateways_cibles
    ]
    if args.verifier_seule:
        return _verifier(cf, virtuel_cfg, attendus)

    existant_v = next(
        (s for s in cf.serveurs_virtuels() if s.get("name") == virtuel_cfg["nom"]), None
    )
    if existant_v is None:
        rep = cf.creer_serveur_virtuel(
            virtuel_cfg["nom"], virtuel_cfg.get("description", ""), ids_outils
        )
        print(f"[virtuel] {virtuel_cfg['nom']} : créé ({len(ids_outils)} outils associés).")
        serveur = rep or {}
    else:
        # Le champ associé revient tantôt en liste, tantôt en chaîne "a,b"
        # (alias camelCase côté API) : normaliser sans deviner.
        brut = existant_v.get("associatedTools")
        if brut is None:
            brut = existant_v.get("associated_tools") or []
        if isinstance(brut, str):
            brut = [x for x in brut.split(",") if x]
        if set(ids_outils) != set(brut):
            cf.resynchroniser_serveur_virtuel(
                existant_v["id"], virtuel_cfg["nom"],
                virtuel_cfg.get("description", ""), ids_outils,
            )
            print(f"[virtuel] {virtuel_cfg['nom']} : liste d'outils resynchronisée.")
        else:
            print(f"[virtuel] {virtuel_cfg['nom']} : inchangé.")
        serveur = existant_v
    chemin_mcp = f"/servers/{serveur['id']}/mcp"
    print(f"[virtuel] endpoint : {args.url}{chemin_mcp}")
    return _verifier(cf, virtuel_cfg, attendus, chemin_mcp)


def _verifier(
    cf: ContextForge,
    virtuel_cfg: dict[str, Any],
    attendus: set[str],
    chemin_mcp: str | None = None,
) -> int:
    """Contrôle étape C : tools/list du serveur virtuel == outils attendus."""
    if chemin_mcp is None:
        existant_v = next(
            (s for s in cf.serveurs_virtuels() if s.get("name") == virtuel_cfg["nom"]), None
        )
        if existant_v is None:
            print(f"ERREUR : serveur virtuel {virtuel_cfg['nom']!r} introuvable (--verifier-seule).")
            return 1
        chemin_mcp = f"/servers/{existant_v['id']}/mcp"
    observes = cf.outils_du_serveur_virtuel(chemin_mcp)
    ok, manquants, en_trop = comparer_listes(attendus, observes)
    if ok:
        print(f"[VERIFIE] ratiss-v1 == outils attendus ({len(attendus)} outils, correspondance exacte).")
        return 0
    print(f"[ECHEC] ratiss-v1 != attendu : manquants={sorted(manquants)} en_trop={sorted(en_trop)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
