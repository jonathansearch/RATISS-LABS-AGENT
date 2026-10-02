# BYOK — Bring Your Own Key (conception, Phase 1)

> **Statut : conception uniquement. Rien n'est exposé, aucun composant n'est actif,
> aucun secret n'est stocké.** Aucune UI/API n'est démarrée.

## 1. Objectif

Permettre au propriétaire de saisir lui-même la clé d'un fournisseur IA
(future rubrique *Paramètres → Fournisseur IA*), sans que cette clé ne
transite jamais par OpenHands, le chat, le dépôt ou les tests.

## 2. Règles non négociables

1. Champ de clé **masqué**. Après sauvegarde, n'afficher que
   `configurée / non configurée`, le `provider`, le `modèle` et les limites —
   **jamais la clé, même partiellement**.
2. **Aucun secret** dans : `localStorage`, `sessionStorage`, URL, état persisté
   du frontend, logs, erreurs, traces OTel, checkpoints LangGraph, base
   conversationnelle, fichiers versionnés, artefacts.
3. La saisie passe **uniquement** par une UI authentifiée sur HTTPS vers le
   backend. **Jamais** d'appel direct du navigateur au fournisseur.
4. Le backend ne persiste la clé que via un **secret store approuvé** ou une
   solution chiffrée dont la gestion de clé est documentée. Si rien n'est
   configuré → **refuser la sauvegarde**, BYOK reste désactivé.
5. **Aucun endpoint de lecture** ne renvoie la clé. Rotation et suppression
   doivent être explicites.
6. Sauvegarder une clé **ne déclenche aucun appel de test ni coût**.
7. Les tests n'utilisent qu'une **chaîne factice**. On ne demande et ne lit
   jamais la vraie clé, le `.env`, le keychain ou les variables secrètes.

## 3. Modèle de données (proposé, non implémenté)

```
ProviderConfig {
  provider:          "exemple"        # nom du fournisseur
  modele:            "exemple-modele"
  region:            "eu"
  budget_tokens_max: 1000             # plafond par tâche
  classe_donnees:    "publique"       # classe autorisée
  approuve:          false            # approbation de dépense explicite
  cle_ref:           "secret://..."   # RÉFÉRENCE opaque, jamais la valeur
  cle_configuree:    false            # booléen dérivé, sans la clé
}
```

La clé elle-même n'apparaît **que** dans le secret store, sous une référence
opaque (`cle_ref`). Le reste du système ne manipule que `cle_configuree`.

## 4. Barrières fail-closed (déjà en place dans le code)

`ConfigurationModele.est_complete()` exige **simultanément** : `fournisseur`,
`modele`, `region`, `budget_tokens_max`, `classe_donnees`, `approuve`.
Tant qu'un champ manque, `ModeleLiteLLM` refuse tout appel
(`ModeleIndisponible`). En Phase 1, même complet, l'appel est refusé :
BYOK n'est pas configuré et aucune clé n'est transmise.

**BYOK ≠ approbation de dépense.** Tant que le propriétaire n'a pas fixé
fournisseur, modèle, région, plafond par tâche/mois et classes de données
autorisées, le provider reste **désactivé** et le graphe utilise le **mock**.

## 5. Tests BYOK (factices)

- aucun secret dans les réponses, logs, erreurs ou checkpoints ;
- config incomplète → provider bloqué ;
- sauvegarde d'une clé factice → aucun appel réseau, aucun coût ;
- aucun endpoint de lecture ne restitue la clé.

Ces tests utilisent une chaîne factice (`"cle-factice-de-test"`), jamais une
vraie clé.

## 6. Décisions bloquantes (à trancher par le propriétaire)

- mécanisme d'authentification de l'UI (VPN + TLS annoncés, mécanisme différé) ;
- secret store retenu (aucun approuvé à ce jour) ;
- fournisseur / modèle / région / plafond / classes de données autorisées ;
- durées de rétention par catégorie.
