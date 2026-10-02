# Notes de montage — points à vérifier au moment de l'assemblage

Ces points ne bloquent pas la Phase 0 (contrats). Ils sont à confirmer **au
montage**, quand les briques seront réellement installées.

## 1. `allowed-tools` (spécification) vs `allowed_tools` (documentation deepagents)

La spécification Agent Skills écrit **`allowed-tools`** (tiret). La
documentation et `MONTAGE.md` écrivent **`allowed_tools`** (underscore).

→ **À vérifier** : quel nom exact deepagents lit-il dans le frontmatter d'un
`SKILL.md` ?

En attendant, le contrat `skill.schema.json` **accepte les deux** :

- `allowed-tools` — champ de premier niveau (spec) ;
- `x-ratiss.allowed_tools` — alias (orthographe de `MONTAGE.md`).

Le test `test_skill_allowed_tools_deux_orthographes` couvre les deux cas. Quand
la réponse sera connue, on pourra retirer l'alias s'il est inutile.

## 2. Attributs d'extension CloudEvents

Le contrat `event.schema.json` accepte tout attribut dont le nom est en
**minuscules et chiffres** (`patternProperties`), conformément à CloudEvents.
Conséquence assumée : un ancien champ comme `horodatage` est **accepté** (il est
traité comme un attribut d'extension). La protection vient du fait que les
consommateurs lisent `time`, pas `horodatage`.

## 3. `inputSchema` MCP

Le contrat `tool.schema.json` reprend `name`, `description`, `inputSchema`,
`outputSchema` et `annotations` de la spécification MCP. `outputSchema` et
`annotations` sont **optionnels** (la spec les prévoit mais tous les serveurs ne
les exposent pas).
