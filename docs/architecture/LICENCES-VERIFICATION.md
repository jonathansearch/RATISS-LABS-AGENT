# Vérification des licences — source réelle, directes vs transitives

**Méthode** : lecture des **fichiers de licence effectivement embarqués**
(`*.dist-info/licenses/`) dans le venv, plus les métadonnées installées. On ne
se fie pas à un seul champ metadata : le texte du fichier de licence fait foi.

> ⚠️ Aucune modification globale du `CATALOGUE.md` sur la seule base d'un champ
> metadata. La nuance LiteLLM ci-dessous est étayée par le fichier de licence réel.

---

## 1. Dépendances **directes** (choisies explicitement)

| Paquet | Version | Licence (fichier réel) |
|---|---|---|
| langgraph | 1.2.12 | MIT |
| litellm | 1.103.2 | MIT |
| pydantic | 2.13.5 | MIT |
| pytest (dev) | 9.1.1 | MIT |

**Aucune dépendance directe n'est en MPL, ni en copyleft.**

### Nuance LiteLLM (lue dans le fichier, pas dans le champ)

Le fichier `litellm-1.103.2.dist-info/licenses/LICENSE` (réel) déclare :

> *« Portions of this software are licensed as follows: All content that resides
> under the "enterprise/" directory … is licensed under the license defined in
> "enterprise/LICENSE". »*

Le champ `License-Expression: MIT` est donc **exact pour le cœur** mais **ne
résume pas** la présence d'un sous-ensemble `enterprise/` sous licence
distincte. Le `CATALOGUE.md` porte `NOASSERTION` : la note demande déjà de lire
le fichier LICENSE avant usage commercial — c'est ce constat qui est ici
précisé, **sans modifier le catalogue global**.

---

## 2. Paquets **transitifs** en MPL-2.0 (copyleft faible)

Les trois proviennent de la fermeture transitive — **aucun n'est un choix
direct du projet** :

| Paquet | Version | Déclaré | Fichiers de licence réels | Amené par (transitivement) |
|---|---|---|---|---|
| `certifi` | 2026.7.22 | MPL-2.0 | `licenses/LICENSE` (MPL-2.0) | `httpx`, `httpcore`, `requests` |
| `orjson` | 3.12.0 | `MPL-2.0 AND (Apache-2.0 OR MIT)` | `LICENSE-MPL-2.0`, `LICENSE-APACHE`, `LICENSE-MIT` | `litellm` (direct), `langsmith`, `langgraph-sdk` |
| `tqdm` | 4.70.1 | `MPL-2.0 AND MIT` | `licenses/LICENCE` (texte MIT, exceptions listées) | `openai`, `huggingface_hub`, `fsspec` |

### Précisions issues des fichiers

- **`orjson`** distribue **trois** fichiers de licence et son
  `License-Expression` est `MPL-2.0 AND (Apache-2.0 OR MIT)` : il existe un
  chemin **Apache-2.0 ou MIT**.
- **`tqdm`** : le fichier `LICENCE` déclare *« release the work under the MIT
  licence »* avec des exceptions listées. Le champ metadata `MPL-2.0 AND MIT`
  est donc plus restrictif que le texte principal.
- **`certifi`** : MPL-2.0 confirmé par le fichier `LICENSE`.

---

## 3. Décision du propriétaire (02/10/2026)

**Décision n° 3 : MPL-2.0 accepté.**

Motif retenu : ce sont des **dépendances indirectes**, **utilisées sans
modification**. La MPL-2.0 est un **copyleft faible, fichier par fichier** :
elle n'impose d'obligation de publication que sur les fichiers MPL **modifiés**.
Aucun fichier de ces paquets n'est modifié par le projet.

Conséquences pratiques retenues :

1. ✅ **Aucune action requise** tant qu'aucun fichier de `certifi`, `orjson` ou
   `tqdm` n'est modifié.
2. ✅ Si un de ces paquets devait être **modifié**, les fichiers modifiés
   devraient être publiés sous MPL-2.0. **Règle du projet : ne pas les modifier.**
3. ✅ Pour `orjson`, la branche `Apache-2.0 OR MIT` reste préférable si un choix
   explicite est nécessaire un jour.
4. ⏳ Un **SBOM formel** n'est pas encore produit ; la présente vérification ne
   le remplace pas.

> ⚠️ Lecture technique, **pas un avis juridique**. Toute redistribution
> commerciale mérite une revue juridique dédiée.

---

## 4. Portée

- Fermeture transitive : **83 paquets**, **0 licence non déclarée**.
- Inventaire brut : `docs/architecture/LICENCES-PHASE1.md`.
- Lock reproductible : `requirements-phase1.lock.txt` (78 paquets).
- Cette vérification **ne couvre pas** la conformité SBOM complète, qui
  n'existe pas encore.
