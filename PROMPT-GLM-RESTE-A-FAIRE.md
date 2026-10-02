# 🤖 PROMPT GLM — CE QUI RESTE À FAIRE POUR QUE RATISS LABS AGENT MARCHE

> **À l'agent qui lit ce fichier (GLM, puis DeepSeek pour l'installation).**
> Tu reprends le dépôt `jonathansearch/RATISS-LABS-AGENT`. Ton but est simple : **que l'agent tourne pour de vrai sur l'ordinateur du chef**, avec une interface de chat, des outils MCP, des règles de sécurité et une traçabilité SHA-256.
> **Tu assembles, tu ne réinventes pas.** Toutes les briques sont déjà choisies, vérifiées et versionnées. Tu écris seulement la colle.

---

## 0. LIS D'ABORD (obligatoire, dans cet ordre)

1. `ETAT-DU-PROJET.md` : où on en est.
2. `MONTAGE.md` : les 12 étapes, avec leurs contrôles de passage.
3. `VERSIONS.md` : versions exactes. **Python 3.12, Node ≥ 22.19.** N'en change aucune sans le noter.
4. `COMPATIBILITE.md` : comment chaque brique se branche (adresses, transports, paramètres).
5. `LICENCES.md` : ce qu'on a le droit d'utiliser.
6. `contrats/` : les 6 schémas. **Ils sont figés : tu t'y conformes, tu ne les modifies pas.**
7. `src/ratiss_agent/` : le noyau existant (LangGraph, registre, événements, hashes, manifeste, reprise, adaptateur de modèle verrouillé). 107 tests passent. **Tu pars de là.**

## 1. RÈGLES ABSOLUES

1. **Aucune clé dans git.** Les clés vont dans `.env` (déjà dans `.gitignore`) ; seul `.env.example` est versionné, avec des valeurs factices.
2. **Les contrats ne bougent pas.** Si un contrat te bloque, tu t'arrêtes et tu le signales.
3. **Une étape = une branche = une PR.** Tu **ne fusionnes jamais** : c'est le chef qui fusionne.
4. **Chaque étape se termine par son contrôle** (§ 3). Tu donnes le résultat exact de `pytest` et des commandes de contrôle, **sans l'embellir**. Un échec est une donnée : tu le rapportes.
5. **Tu ne lances aucun service sur une machine sans que le chef l'ait demandé.** Tu écris le Compose et les scripts ; c'est l'installateur (DeepSeek) qui démarre, sur ordre.
6. **Les actions dangereuses** (écriture hors du dossier de travail, push git, réseau, outils cyber actifs, suppression) passent par la politique : **REQUIRE_APPROVAL ou DENY**, jamais ALLOW par défaut.
7. **Rien d'inventé.** Pas de faux résultat, pas de faux sceau : un run mock reste marqué `scelle: false`.
8. **Simplicité (brief § 46).** Pas de Kubernetes, pas de swarm multi-agents, pas d'application mobile, pas de voix en V1.

## 2. ARCHITECTURE CIBLE V1 (rappel)

```text
Navigateur du chef (PC ou téléphone sur le réseau local)
        │
   [ui] Open WebUI (banc d'essai) ──► [api] RATISS API (FastAPI)
                                          │
                                   [runtime] LangGraph + deepagents
                                   ├─ middleware RATISS ──► [opa] OPA (ALLOW/DENY/REQUIRE_APPROVAL)
                                   ├─ interrupt() ──► approbation humaine dans l'UI
                                   ├─ modèle ──► [llm-gateway] LiteLLM ──► GLM / DeepSeek / Ollama local
                                   ├─ outils ──► [mcp-gateway] ContextForge, serveur virtuel « ratiss-v1 »
                                   │                ├─ filesystem (volume de travail uniquement)
                                   │                ├─ git / github (push = approbation)
                                   │                ├─ fetch / arxiv
                                   │                ├─ sandbox-python (llm-sandbox + gVisor si Linux)
                                   │                └─ playwright (navigateur)
                                   └─ provenance ──► SHA-256 chaîné ──► journal + manifeste de run
                                   
Stockage : [postgres] PostgreSQL 16 + pgvector (checkpoints, mémoire, événements) · [objects] RustFS (artefacts)
```

---

## 3. LES ÉTAPES QUI RESTENT (dans cet ordre)

Les étapes 0 (contrats) et le noyau mock sont **faits**. Il reste ceci.

### ÉTAPE A — Socle Docker (MONTAGE, étape 1)
**But :** la base de données et le stockage démarrent avec une seule commande.
- Compléter `docker-compose.yml` :
  - `postgres` : image `pgvector/pgvector:pg16`, déjà présente, port lié à `127.0.0.1` ;
  - `redis` : nécessaire à ContextForge et LiteLLM ;
  - `objects` : RustFS 1.0.0, port lié à `127.0.0.1`, volume persistant.
- Réseaux Docker :
  - `core` (interne) ;
  - `tools` (outils, **sans internet sauf exceptions explicites**) ;
  - `edge` (UI et API seulement).
- Fichier `.env.example` complet : toutes les variables, valeurs factices, une ligne de commentaire par variable.
- Script `scripts/preflight.sh` (et `preflight.ps1` pour Windows) qui vérifie :
  - Docker présent et démarré, Docker Compose v2 ;
  - Python 3.12 et Node ≥ 22.19 ;
  - mémoire libre ≥ 8 Go, disque libre ≥ 20 Go ;
  - ports libres ;
  - présence de KVM (information seulement).
- ✅ **Contrôle :**
  - `docker compose up -d postgres redis objects` → les 3 services sont `healthy` ;
  - `CREATE EXTENSION vector` passe ;
  - un objet écrit dans RustFS se relit avec le même SHA-256.

### ÉTAPE B — Model Gateway (MONTAGE, étape 2)
**But :** un seul point d'entrée pour tous les modèles.
- Service `llm-gateway` : LiteLLM proxy 1.103.2, **hors dossier `enterprise/`**.
- Fichier `config/litellm.yaml` avec des alias stables :
  - `ratiss-principal` → GLM (clé `GLM_API_KEY`) ;
  - `ratiss-secours` → DeepSeek (clé `DEEPSEEK_API_KEY`) ;
  - `ratiss-local` → Ollama (option, aucun coût).
- **Plafond de coût** dans LiteLLM : budget mensuel en variable `RATISS_BUDGET_USD`, avec 10 par défaut (proposition, à confirmer par le chef). Au-delà, refus.
- Déverrouiller `model_adapter.py` : l'appel réel passe **par le proxy** (`ChatOpenAI` pointé sur `http://llm-gateway:4000`, recette documentée par LiteLLM), **seulement si** la clé et le budget sont configurés. Sinon, le mock reste actif.
- ✅ **Contrôle :**
  - une même requête répond via 2 alias ;
  - sans clé → message clair, aucun crash ;
  - le budget dépassé est refusé (testé avec un budget de 0).

### ÉTAPE C — MCP Gateway + outils de base (MONTAGE, étape 3)
**But :** l'agent voit ses outils au travers d'**une seule adresse**.
- Service `mcp-gateway` : ContextForge 1.0.11 (PostgreSQL + Redis de l'étape A).
- Enregistrer les serveurs MCP suivants :
  - `filesystem` (modelcontextprotocol/servers), limité au volume `/workspace` ;
  - `git` ;
  - `fetch` ;
  - `github-mcp-server` v1.14.0, avec un jeton GitHub lu depuis `.env` (option : si absent, le serveur est désactivé) ;
  - `arxiv-mcp-server` 0.7.3.
- Créer le serveur virtuel **`ratiss-v1`** : endpoint `http://mcp-gateway:4444/servers/<UUID>/mcp`, en **Streamable HTTP** avec un jeton Bearer.
- Script `scripts/enregistrer_outils.py` : lit `tools.yaml` et enregistre les serveurs et outils dans ContextForge. Il est idempotent : le relancer ne crée pas de doublon.
- ✅ **Contrôle :**
  - la liste des outils de `ratiss-v1` correspond exactement à `tools.yaml` ;
  - `read_file` dans `/workspace` réussit ;
  - `read_file /etc/passwd` est refusé.

### ÉTAPE D — Admission des outils (MONTAGE, étape 4)
- Script `scripts/admettre_serveur.py` :
  1. exporte les définitions d'outils ;
  2. lance Cisco mcp-scanner 4.8.5 en mode **YARA hors ligne** ;
  3. calcule le SHA-256 des définitions ;
  4. l'écrit dans `tools.yaml` (champ `x-ratiss.sha256`).
- Au démarrage du runtime : si le hash d'un outil a changé → l'outil est **suspendu**, et un événement `ratiss.tool.suspended` est émis.
- ✅ **Contrôle :**
  - les serveurs de l'étape C sont scannés, avec 0 finding critique ;
  - une modification manuelle de la description d'un outil le fait suspendre.

### ÉTAPE E — Runtime réel : deepagents + MCP (MONTAGE, étape 5)
- Ajouter `deepagents==0.7.21` et `langchain[mcp]==1.4.3` (bêta, version figée).
- Le runtime utilise `create_deep_agent(...)` avec :
  - le modèle via LiteLLM (étape B) ;
  - les outils via `MCPAdapter` pointé sur `ratiss-v1`. **Pas `langchain-mcp-adapters`, qui est archivé. Pas SSE, qui est déprécié** ;
  - `skills=["./skills/"]` (étape I) ;
  - le checkpointer PostgreSQL `langgraph-checkpoint-postgres==3.1.2`, à la place du checkpoint en RAM actuel.
- Conserver l'existant : registre, événements CloudEvents, hashes, manifeste.
- ✅ **Contrôle :**
  - la tâche « lis `/workspace/test.txt` et résume-le » va de bout en bout avec le vrai modèle ;
  - `docker kill runtime` en cours de tâche, puis redémarrage → la tâche **reprend depuis le checkpoint PostgreSQL** (c'est la limite reconnue de la phase 1 : il faut maintenant la lever).

### ÉTAPE F — Politique + approbation humaine (MONTAGE, étape 6) ⭐ pièce maison n° 1
- Service `opa` : OPA v1.21.1. Politiques dans `policies/ratiss.rego`, alignées sur `contrats/policy.schema.json` :
  - lecture dans `/workspace` → **ALLOW** ;
  - écriture dans `/workspace`, `fetch` réseau, exécution en sandbox → **REQUIRE_APPROVAL** ;
  - `git push`, création de PR → **REQUIRE_APPROVAL** ;
  - tout ce qui sort de `/workspace`, suppression récursive, outils cyber actifs → **DENY** ;
  - un outil inconnu → **DENY**.
- **Middleware RATISS** à brancher via `middleware=` de deepagents. Avant chaque appel d'outil :
  - il envoie `{tool, arguments, user, task_id, run_id}` à OPA ;
  - `DENY` → refus + événement `ratiss.policy.denied` ;
  - `REQUIRE_APPROVAL` → `interrupt()`, puis l'humain approuve, modifie ou rejette, et l'événement est journalisé.
  - **Tout effet de bord se place APRÈS l'interrupt** (sinon il est rejoué à la reprise).
  - **L'approbation est liée au hash du payload** : si le payload change, l'approbation est invalide (c'est déjà codé dans `resume.py` : le réutiliser).
- ✅ **Contrôle :**
  - 3 tests réels, un par décision ;
  - `git push` → demande d'approbation ;
  - `rm -rf /` → refus ;
  - un payload modifié après approbation → refus.

### ÉTAPE G — Sandboxes (MONTAGE, étape 7)
- **Python :** `llm-sandbox==0.3.45`, exposé comme outil MCP, dans le réseau `tools` **sans internet**.
  - **Linux :** gVisor `runsc` déclaré dans `/etc/docker/daemon.json`. Le preflight teste `docker run --runtime=runsc hello-world`.
  - **Windows / macOS :** Docker standard (isolation plus faible). Le preflight l'**affiche clairement**.
- **Navigateur :** `@playwright/mcp` 0.0.83, dans un conteneur, avec internet filtré.
- **Jupyter** (option) : JupyterLab + `jupyter-mcp-server` 2.2.3.
- ✅ **Contrôle :**
  - du code qui lit `/etc` ou ouvre le réseau est bloqué ;
  - une page web est lue et résumée ;
  - un calcul Python renvoie un résultat et un artefact hashé.

### ÉTAPE H — Mémoire + provenance RATISS (MONTAGE, étape 8) ⭐ pièce maison n° 2
- **Mémoire de conversation et de tâche :** checkpoints PostgreSQL (étape E).
- **Mémoire documentaire :** table pgvector (`documents` : id, contenu, embedding, sha256, source, date).
- **Pont de provenance :**
  - chaque événement CloudEvents et chaque artefact est hashé en SHA-256 ;
  - les hashes sont **chaînés** (chaque entrée contient le hash de la précédente) dans une table `ratiss_journal` ;
  - à la fin d'un run, `manifest.py` produit un **manifeste de run** : modèle et version, outils appelés avec leur hash, entrées, sorties, approbations, hash final de la chaîne.
  - Interface avec `jonathansearch/RATISS-Framework` : réutiliser son format de journal et de hash s'il existe, sinon le documenter dans `docs/architecture/PROVENANCE.md`.
- Commande `ratiss verifier <run_id>` : recalcule la chaîne et dit OK ou CASSÉ, en indiquant l'entrée fautive.
- ✅ **Contrôle :**
  - en rejouant le manifeste, on retrouve les mêmes hashes d'entrée ;
  - un artefact modifié à la main → `verifier` dit CASSÉ.

### ÉTAPE I — Skills (MONTAGE, étape 9)
- Dossier `skills/` : **10 à 20 skills au maximum** en V1, chacun conforme à `contrats/skill.schema.json`.
- Sélection proposée :
  - 5 K-Dense (science : revue de littérature, analyse de données…) ;
  - 5 Anthropic-Cybersecurity-Skills (défensif uniquement : analyse de logs, durcissement…) ;
  - 1 diagram-design ;
  - `mcp-builder` et `skill-creator` d'anthropics/skills (**Apache-2.0 seulement**).
  - **Garder la licence de chaque skill.**
- Script `scripts/admettre_skill.py` : validation par le schéma, puis scan (snyk-agent-scan s'il est disponible, sinon revue manuelle), puis SHA-256 enregistré dans `skills.yaml`.
- Vérifier ici le point en suspens : **deepagents lit-il `allowed-tools` ou `allowed_tools` ?** Tester, puis l'adapter dans le chargeur (pas dans le contrat).
- ✅ **Contrôle :** au démarrage, seuls le nom et la description sont chargés ; le bon skill est choisi pour 3 tâches tests (science, cyber défensif, diagramme).

### ÉTAPE J — API + interface (MONTAGE, étape 10)
- **RATISS API** (FastAPI), avec ces routes :
  - `POST /sessions`, `POST /sessions/{id}/messages` (réponse en streaming) ;
  - `GET /tasks`, `GET /runs/{id}`, `GET /runs/{id}/events` ;
  - `GET /approvals` (en attente), `POST /approvals/{id}` (approve, edit, reject) ;
  - une **route compatible OpenAI** `/v1/chat/completions`, pour qu'Open WebUI parle à RATISS comme à un modèle.
- **UI V1 = Open WebUI v0.11.4** branchée sur cette route. Moins de 50 utilisateurs, donc la clause de marque ne pose aucun problème.
- **Approbations visibles et validables depuis le téléphone** : à défaut de mieux en V1, une page HTML simple `/approvals` servie par l'API.
- **Accès :** l'API et l'UI sont liées à `127.0.0.1` par défaut. Une option `RATISS_LAN=1` permet l'accès depuis le téléphone sur le réseau local, **avec un mot de passe obligatoire** (`RATISS_UI_PASSWORD` dans `.env`).
- ✅ **Contrôle :**
  - depuis le navigateur, une question reçoit une réponse ;
  - une action `git push` fait apparaître une approbation, validée depuis le téléphone ;
  - la page du run montre les événements et le hash final.

### ÉTAPE K — Workflows métier (MONTAGE, étape 11)
- Créer 3 profils (chacun = une sélection d'outils + de skills + une politique) :
  - **Recherche** : arxiv + fetch + K-Dense + sandbox Python ;
  - **Dev** : filesystem + git + github + diagram-design ;
  - **Cyber défensif** : skills défensifs seulement en V1. Les outils offensifs (FuzzingLabs mcp-security-hub) restent **désactivés**, et seront activables plus tard par décision explicite du chef, dans un réseau isolé.
- ✅ **Contrôle :** une tâche réelle par profil, de bout en bout, avec son manifeste.

### ÉTAPE L — Installation sur l'ordinateur du chef (pour DeepSeek)
- Script unique `scripts/installer.sh` (Linux / WSL2) et `installer.ps1` (Windows). Il fait :
  1. le preflight ;
  2. la copie de `.env.example` vers `.env`, puis **demande** les clés une par une (jamais affichées, jamais committées) ;
  3. `docker compose pull`, puis `up -d` ;
  4. l'enregistrement des outils (étape C) et leur admission (étape D) ;
  5. un test de fumée : 1 question, 1 lecture de fichier, 1 approbation ;
  6. l'affichage de l'adresse de l'UI.
- **Windows :** passer par **Docker Desktop + WSL2**. gVisor n'est pas disponible : le signaler.
- `docs/INSTALLATION.md` : pas à pas, avec captures d'écran textuelles, et une section « problèmes fréquents » (port occupé, Docker non démarré, mémoire insuffisante, clé invalide).
- Commandes utiles dans un `Makefile` :
  - `make up` / `make down` ;
  - `make logs` ;
  - `make test` ;
  - `make verifier RUN=<id>` ;
  - `make sauvegarde` (dump PostgreSQL + RustFS).
- ✅ **Contrôle final :**
  - sur une machine vierge, `installer` → l'UI répond en moins de 30 minutes ;
  - les 3 profils fonctionnent ;
  - `make test` est vert.

---

## 4. DÉCISIONS DU CHEF — VALEURS PAR DÉFAUT PROPOSÉES (modifiables dans `.env`)

| Sujet | Défaut proposé | Variable |
|---|---|---|
| Auth UI | Utilisateur unique ; mot de passe obligatoire dès que l'accès LAN est activé | `RATISS_UI_PASSWORD` |
| Clés (BYOK) | Fichier `.env` local, hors git, permissions 600 | `GLM_API_KEY`, `DEEPSEEK_API_KEY` |
| Modèle | `ratiss-principal` = GLM ; `ratiss-secours` = DeepSeek | `RATISS_MODELE` |
| Plafond de coût | 10 USD/mois, refus au-delà | `RATISS_BUDGET_USD` |
| Rétention | Journal de provenance conservé **indéfiniment** ; conversations 90 jours | `RATISS_RETENTION_JOURS` |
| Accès réseau | Local uniquement (`127.0.0.1`) | `RATISS_LAN=0` |

➡️ **Ce sont des propositions.** Le chef peut changer chaque valeur sans toucher au code.

## 5. FORMAT DE RAPPORT EXIGÉ À LA FIN DE CHAQUE ÉTAPE

```text
ÉTAPE X — <nom>
Branche : …   PR : #…   (non fusionnée)
Fichiers ajoutés / modifiés : …
pytest : <sortie exacte, dernière ligne>
Contrôle de passage : <commande> → <résultat exact>
Ce qui ne marche pas / limites : …
Décision attendue du chef : …
```

## 6. CE QUE TU NE FAIS PAS

- Modifier `contrats/`, ou les docs Arena (`CATALOGUE`, `MONTAGE`, `COMPATIBILITE`, `VERSIONS`, `LICENCES`, `SOURCES`).
- Fusionner une PR, ou pousser sur `main`.
- Committer une clé ou un `.env`.
- Activer des outils cyber offensifs.
- Ajouter une brique hors catalogue sans la justifier dans la PR (lien, licence, raison).
- Écrire « ça marche » sans la sortie de la commande qui le prouve.

---

**Ordre de livraison :** A → B → C → D → E → F → G → H → I → J → K → L.

**Priorité si le temps manque :** A, B, C, E, F, J, L, c'est-à-dire un agent qui répond, utilise des outils et demande l'approbation. On ajoutera D, G, H, I et K ensuite.

*Rédigé par l'agent Arena à partir de la campagne du 02/10/2026 et de l'état du dépôt à `65ba507`.*
