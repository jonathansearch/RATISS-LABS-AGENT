# 🧾 REVUE PR #1 — vérification et mise au point

Document de traçabilité de la vérification indépendante des contrats, et des
décisions prises le **02/10/2026**.

## 1. Traçabilité des commits sur `main`

Les commits `51a88c3`, `61e981b` et `d56632f` sur `main` viennent de
**l'agent Arena**, sur demande explicite du propriétaire (Jonathan).

- Ce **n'est pas un écart de conduite**.
- La consigne « ne pas pousser, laisser la PR #1 ouverte » s'adressait à
  **OpenHands uniquement**.
- Les documents `CATALOGUE.md`, `MONTAGE.md`, `COMPATIBILITE.md`, `LICENCES.md`,
  `VERSIONS.md`, `SOURCES.md`, `LIENS.csv` sont de **l'agent Arena**.

## 2. État du distant

| Réf | Commit |
|---|---|
| `origin/main` | `d56632f` (2ᵉ passe : `VERSIONS.md`, jonctions documentées) |
| `origin/openhands/phase-0-contrats` | `fa5a5c4` |
| PR #1 | `openhands/phase-0-contrats` → `main`, **ouverte**, non mergée |

`61e981b` est un **ancêtre** de `d56632f`.

## 3. Base canonique : **6 schémas**

Tool, Skill, Task, Event, Run, Policy. Le brief et `MONTAGE.md` étape 0 disent
**6**. Il n'existe pas de version « 10 schémas ».

## 4. Problème de contrat identifié puis corrigé

`contrats/skill.schema.json` **rejetait** un vrai skill Agent Skills. Preuve sur
un `SKILL.md` réel de K-Dense (`literature-review`) :

```
Additional properties are not allowed
('allowed-tools', 'compatibility', 'license', 'metadata', 'name' were unexpected)
```

Puis, après une première correction incomplète, le même skill brut était encore
refusé car `nom` restait **requis** :

```
'nom' is a required property
```

C'est ce second point qui garantissait l'échec des skills de K-Dense,
Cybersecurity-Skills et diagram-design.

## 5. Règle de nommage appliquée (décision du propriétaire)

- champs **standards en anglais**, exactement comme la spécification de référence ;
- extensions RATISS regroupées dans un **bloc unique `x-ratiss`** ;
- `additionalProperties: false` à la racine ;
- **aucun doublon** (règle n° 3) : `name` seul (`nom` supprimé), `license` seule
  (`licence` supprimé), `allowed-tools` seul (alias `allowed_tools` supprimé) ;
- **aucune rétrocompatibilité** : rien n'est en production, la PR #1 n'est pas
  fusionnée. Les tolérances iront dans le **chargeur**, au montage, et seulement
  si un test le montre nécessaire ;
- **exception `Event`** : CloudEvents autorise les attributs d'extension
  (minuscules et chiffres), acceptés par `patternProperties` ;
- `Task`, `Run`, `Policy` : pas de standard externe, champs conservés mais en anglais.

### Corrélation OpenTelemetry

L'enveloppe suit **CloudEvents** ; la corrélation **OpenTelemetry** passe par
l'**extension CloudEvents de traçage distribué** : `traceparent` (requis non
vide) et `tracestate` (optionnel). `trace_id`/`span_id` ont été supprimés
(doublon). Les deux exigences du brief et de `MONTAGE.md` sont satisfaites.

## 6. Contenu de la PR

| Élément | État |
|---|---|
| `skill.schema.json` | aligné Agent Skills + `x-ratiss` |
| `tool.schema.json` | aligné MCP (`name`, `description`, `inputSchema`, `outputSchema`, `annotations`) + `x-ratiss` |
| `event.schema.json` | aligné CloudEvents + attributs d'extension + `traceparent`/`tracestate` + `x-ratiss` |
| `task`, `run`, `policy` | champs renommés en anglais |
| 6 exemples | mis à jour |
| `docker-compose.yml` | `127.0.0.1:${POSTGRES_PORT:-5432}:5432` |
| `docs/architecture/LICENCES-VERIFICATION.md` | décision MPL-2.0 consignée |
| `docs/architecture/NOTES-MONTAGE.md` | `allowed-tools` strict ; tolérance dans le chargeur |

## 7. Tests (4 demandés + garde-fous)

1. ✅ un vrai SKILL.md K-Dense accepté ;
2. ✅ un vrai événement CloudEvents accepté (exemple officiel de la spec) ;
3. ✅ une vraie définition d'outil MCP (`tools/list`) acceptée ;
4. ✅ un champ inconnu refusé ;
5. ✅ un **doublon** refusé (`nom`, `licence`, `allowed_tools`, `trace_id`) ;
6. ✅ les limites de taille testées (`name` ≤ 64, `description` ≤ 1024,
   `compatibility` ≤ 500).

## 8. Limites assumées

- **Rien n'a été fusionné.** PR #1 laissée ouverte comme référence.
- Aucune archive `RATISS-PHASE-0-1-REVIEW.zip` n'existe.
- Les tests valident la **conformité aux spécifications**, pas l'exécution réelle
  des briques (aucun service lancé).
- Lecture technique, **pas un avis juridique**.
