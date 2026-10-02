# Notes de montage — points à vérifier au moment de l'assemblage

Ces points ne bloquent pas la Phase 0 (contrats). Ils sont à confirmer **au
montage**, quand les briques seront réellement installées.

## 1. `allowed-tools` : le contrat est strict, la tolérance ira dans le chargeur

Décision actée : le contrat `skill.schema.json` n'accepte que **`allowed-tools`**
(orthographe de la spécification Agent Skills). L'alias `allowed_tools` a été
**retiré** : accepter les deux orthographes permettrait à un même skill d'avoir
deux noms différents pour le même champ.

Arena a corrigé ses documents sur `main` (`71d2722`) : `COMPATIBILITE.md` et
`MONTAGE.md` écrivent désormais `allowed-tools`.

→ **À vérifier au montage** : quel nom exact deepagents lit-il dans le
frontmatter d'un `SKILL.md` ? **Si** il lit `allowed_tools`, la tolérance sera
ajoutée **dans le chargeur**, pas dans le contrat — et seulement si un test le
montre nécessaire.

## 2. Corrélation OpenTelemetry : `traceparent` / `tracestate`

Décision actée : l'enveloppe des événements suit **CloudEvents**, et la
corrélation **OpenTelemetry** passe par l'**extension CloudEvents de traçage
distribué** (`traceparent`, `tracestate`), qui embarque le contexte W3C
Trace Context. Les deux exigences du brief et de `MONTAGE.md` sont donc
satisfaites sans contradiction.

Le contrat expose `traceparent` (chaîne non vide) et `tracestate` (optionnel) à
la racine de l'événement. Les anciens champs `trace_id` et `span_id` ont été
**retirés** : ils faisaient doublon avec `traceparent`.

## 3. Attributs d'extension CloudEvents

Le contrat `event.schema.json` accepte tout attribut dont le nom est en
**minuscules et chiffres** (`patternProperties`), conformément à CloudEvents.
Conséquence assumée : un ancien champ comme `horodatage` est **accepté** (il est
traité comme un attribut d'extension). La protection vient du fait que les
consommateurs lisent `time`, pas `horodatage`.

## 4. `inputSchema` MCP

Le contrat `tool.schema.json` reprend `name`, `description`, `inputSchema`,
`outputSchema` et `annotations` de la spécification MCP. `outputSchema` et
`annotations` sont **optionnels** (la spec les prévoit mais tous les serveurs ne
les exposent pas).
