# 🛠️ WORKFLOW DE MONTAGE — RATISS LABS AGENT v0.1

Ce document est tiré de la campagne de recherche du 02/10/2026 : 84 dépôts vérifiés, README et licences lus, jonctions établies (voir `COMPATIBILITE.md`).

**Principe : on assemble, on ne reconstruit pas.**

**Règle de passage :** on ne passe à l'étape suivante que lorsque le **contrôle** de l'étape en cours est vert. Si un contrôle échoue, on le note : un crash est une donnée.

---

## 🗺️ Vue d'ensemble

```text
ÉTAPE 0  Contrat (schémas)                         → rien ne tourne encore
ÉTAPE 1  Socle : PostgreSQL+pgvector, Redis, RustFS
ÉTAPE 2  Model Gateway : LiteLLM (+ Ollama)
ÉTAPE 3  MCP Gateway : ContextForge + 3 serveurs de base
ÉTAPE 4  Admission MCP : Cisco mcp-scanner + Inspector
ÉTAPE 5  Runtime : LangGraph + deepagents + langchain.mcp
ÉTAPE 6  Policy + approbation : OPA ↔ HITL deepagents   ← seul vrai collage
ÉTAPE 7  Sandboxes : llm-sandbox + gVisor, Playwright, browser-use
ÉTAPE 8  Mémoire + vérification : pgvector + RATISS-Framework (SHA-256)
ÉTAPE 9  Skills : format SKILL.md + 5 dépôts à garder (sélection)
ÉTAPE 10 UI : Open WebUI (banc d'essai), puis assistant-ui
ÉTAPE 11 Workflows métier : recherche, dev, cyber
```

Correspondance avec la feuille de route du brief :
- phase 0 = étape 0 ;
- noyau = étapes 1 à 6 ;
- exécution = étape 7 ;
- mémoire et vérification RATISS = étape 8 ;
- skills = étape 9 ;
- UI = étape 10.

---

## ÉTAPE 0 — Contrat (phase 0 du brief)

- **Objectif :** figer les 6 schémas avant toute installation.
- **S'appuyer sur :**
  - la spécification MCP (`modelcontextprotocol/modelcontextprotocol`) pour le schéma **Tool** (nom, description, inputSchema) ;
  - CloudEvents (`cloudevents/spec`) pour **Event** (id, source, type, time, data) ;
  - le format SKILL.md (`anthropics/skills`, skills Apache-2.0 seulement) pour **Skill** ;
  - le §32 du brief et RATISS-Framework pour **Run** (manifest + hashes).
- **À produire (par GLM) :**
  - schémas Tool / Skill / Task / Event / Run / Policy ;
  - `tools.yaml` et `skills.yaml` (registres) ;
  - une politique de départ : lecture = ALLOW ; écriture et réseau = REQUIRE_APPROVAL ; suppression, push et cyber actif = DENY par défaut.
- **Versions :** utiliser celles de `VERSIONS.md` (Python 3.12, Node ≥ 22.19).
- **Schéma Skill :** reprendre la spécification Agent Skills suivie par deepagents : `name` ≤ 64 caractères (minuscules et tirets), `description` ≤ 1024, et en option `license`, `compatibility`, `metadata`, `allowed_tools`. Ajouter un champ RATISS : `sha256`.
- ✅ **Contrôle :** chaque schéma est validé sur 1 exemple réel, et le fichier des versions est scellé en SHA-256.

## ÉTAPE 1 — Socle

- **Briques :**
  - PostgreSQL : image officielle, avec l'extension pgvector (`pgvector/pgvector`) ;
  - Redis ;
  - RustFS (`rustfs/rustfs`) pour le stockage objet S3.
- **Montage :** 3 services dans le `docker-compose.yml`, sur un réseau interne `ratiss-core`, avec des volumes persistants.
- ✅ **Contrôle :**
  - la base répond et `CREATE EXTENSION vector` passe ;
  - un objet écrit dans RustFS se relit à l'identique (même SHA-256).

## ÉTAPE 2 — Model Gateway

- **Briques :** LiteLLM proxy (`BerriAI/litellm`, rien du dossier `enterprise/`) et Ollama (`ollama/ollama`) pour les modèles locaux.
- **Montage :**
  - déclarer dans la configuration LiteLLM les modèles autorisés (GLM, Claude…, et un modèle local Ollama) ;
  - les clés restent dans un `.env` **hors git** (même règle que `MES-CLES`).
- ✅ **Contrôle :**
  - une même requête au format OpenAI répond via 2 fournisseurs différents ;
  - les coûts et les appels sont visibles dans les logs du proxy.

## ÉTAPE 3 — MCP Gateway + 3 serveurs de base

- **Briques :**
  - ContextForge (`IBM/mcp-context-forge`), branché sur le PostgreSQL et le Redis de l'étape 1 ;
  - serveurs de base : `filesystem` et `git` (`modelcontextprotocol/servers`), puis `github/github-mcp-server`.
- **Montage :**
  - enregistrer les 3 serveurs dans ContextForge (les serveurs stdio passent par son wrapper) ;
  - créer **un serveur virtuel « ratiss-v1 »** qui regroupe uniquement les outils autorisés ;
  - le dossier de travail de `filesystem` est un volume dédié, jamais le disque entier.
- ✅ **Contrôle :**
  - la liste des outils du serveur virtuel correspond exactement à `tools.yaml` ;
  - un appel `read_file` réussit, un appel hors du dossier est refusé.

## ÉTAPE 4 — Admission MCP (aucun serveur sans scan)

- **Briques :**
  - Cisco mcp-scanner (`cisco-ai-defense/mcp-scanner`, moteur YARA hors ligne) ;
  - MCP Inspector (`modelcontextprotocol/inspector`) ;
  - en option, `snyk/agent-scan`, qui dépend du service Snyk.
- **Procédure d'admission d'un serveur MCP :**
  1. exporter ses définitions d'outils ;
  2. les passer au scan hors ligne ;
  3. les inspecter à la main dans Inspector ;
  4. calculer le SHA-256 des définitions et l'enregistrer dans `tools.yaml` ;
  5. ajouter le serveur au serveur virtuel.
- **Intérêt :** si les définitions changent plus tard, le hash ne correspond plus → serveur suspendu. C'est la parade contre le « rug pull ».
- ✅ **Contrôle :** les 3 serveurs de l'étape 3 sont scannés, avec 0 finding critique et leurs hashes enregistrés.

## ÉTAPE 5 — Agent Runtime

- **Briques :**
  - LangGraph (`langchain-ai/langgraph`) ;
  - deepagents (`langchain-ai/deepagents`) ;
  - `langchain.mcp` (`langchain-ai/langchain` v1.4+, bêta : version figée).
  - ⚠️ **Ne pas utiliser** `langchain-mcp-adapters` : il est archivé.
- **Montage :**
  - le runtime voit **un seul** serveur MCP : le serveur virtuel « ratiss-v1 » de ContextForge, à l'adresse `http://mcp-gateway:4444/servers/<UUID>/mcp`, en **Streamable HTTP** avec un jeton Bearer. Côté LangChain, on utilise `MCPAdapter` (pas SSE : déprécié) ;
- le modèle passe par LiteLLM : `ChatOpenAI` pointé sur `http://llm-gateway:4000` (recette documentée par LiteLLM) ;
  - les modèles passent par LiteLLM ;
  - les checkpoints LangGraph sont stockés dans PostgreSQL (persistance des tâches et reprise après coupure) ;
  - Router, Planner et Executor du brief correspondent au planificateur et aux sous-agents de deepagents.
- ✅ **Contrôle :**
  - une tâche « lis tel fichier et résume-le » va de bout en bout ;
  - si on tue le conteneur en cours de tâche, elle reprend depuis le checkpoint.

## ÉTAPE 6 — Policy Engine + approbation humaine (le seul vrai collage)

- **Briques :** OPA (`open-policy-agent/opa`) et le HITL de deepagents (approve / edit / reject).
- **Constat :** ContextForge ne fait pas appel à OPA. La décision doit donc être prise **dans le runtime**.
- **Points d'ancrage officiels de deepagents :** `middleware=` (ajouter un middleware à la pile), `interrupt_on=` (pause avant un appel d'outil) et `permissions=` (droits par chemin sur le filesystem).
- **À écrire (par GLM), sous forme d'un middleware RATISS :** avant chaque appel d'outil, le runtime envoie à OPA `{outil, arguments, utilisateur, tâche}` et applique la réponse :
  - `ALLOW` → l'appel s'exécute ;
  - `DENY` → l'appel est refusé et journalisé ;
  - `REQUIRE_APPROVAL` → `interrupt()`, l'humain valide, modifie ou rejette.
- **Règle d'or :** tout effet de bord se place **après** l'interrupt, sinon il est rejoué à la reprise (pattern documenté par LangGraph).
- ✅ **Contrôle :**
  - 3 tests, un par décision ;
  - un `git push` déclenche une demande d'approbation ;
  - une suppression hors du dossier de travail est refusée.

## ÉTAPE 7 — Sandboxes (brief §47 : Python, Browser, Repository)

- **Python :**
  - llm-sandbox (`vndee/llm-sandbox`) avec son serveur MCP ;
  - Docker configuré avec le runtime `runsc` de gVisor (`google/gvisor`), déclaré dans `/etc/docker/daemon.json` (`runtimes.runsc.path`). Test : `docker run --runtime=runsc … dmesg` doit afficher « Starting gVisor ». Sur systemd, prévoir le réglage du pilote cgroup si besoin ;
  - les notebooks passent par `datalayer/jupyter-mcp-server` et un service JupyterLab dédié.
- **Browser :**
  - `microsoft/playwright-mcp` pour la navigation outillée ;
  - `browser-use/browser-use` pour les tâches de navigation autonomes.
- **Repository :** `github-mcp-server` (étape 3), plus un clone de travail dans un volume isolé.
- **Admission :** chaque nouveau serveur passe par l'étape 4.
- ✅ **Contrôle :**
  - un code qui tente de lire `/etc` ou d'ouvrir le réseau est bloqué ;
  - une page web est lue et résumée ;
  - une PR de test est créée **après approbation**.

## ÉTAPE 8 — Mémoire + vérification RATISS

- **Briques :**
  - pgvector pour la mémoire documentaire ;
  - les checkpoints LangGraph pour la mémoire de tâche ;
  - `jonathansearch/RATISS-Framework` pour la provenance ;
  - `thedotmack/claude-mem` comme **modèle** de compression mémoire (il a été conçu pour Claude Code, ce n'est pas une brique serveur).
- **Montage :**
  - chaque Event (au format CloudEvents) et chaque artefact sont hashés en SHA-256 ;
  - les hashes sont chaînés dans le journal RATISS ;
  - chaque run produit un **manifest de run** (modèles, versions, outils appelés, hashes).
- **Option :** Langfuse (`langfuse/langfuse`, sans les dossiers `ee/`) pour visualiser les traces. Ses intégrations LangChain et LiteLLM sont documentées.
- ✅ **Contrôle :**
  - en rejouant le manifest d'un run, on retrouve les mêmes hashes d'entrée ;
  - un artefact modifié à la main est détecté.

## ÉTAPE 9 — Skills (chargement progressif)

- **Briques :**
  - format SKILL.md (`anthropics/skills` : copier seulement les skills Apache-2.0, comme `mcp-builder` et `skill-creator`) ;
  - K-Dense (science), Anthropic-Cybersecurity-Skills (cyber), diagram-design (diagrammes).
- **Règle (brief §46) :** 10 à 20 skills prioritaires, **pas 817**. On sélectionne, chaque skill est hashé et enregistré dans `skills.yaml`.
- **Chargement (documenté par deepagents, 3 niveaux) :** ① au démarrage, seuls `name` et `description` entrent dans le contexte ; ② le corps du SKILL.md est lu quand le skill est invoqué ; ③ les fichiers `scripts/`, `references/` et `assets/` sont lus seulement si les instructions les demandent. Corps conseillé : < 5 000 tokens. Montage : `skills=["./skills/"]`.
- **Admission :** les skills passent aussi au scan (Snyk agent-scan sait scanner les skills).
- ✅ **Contrôle :**
  - le contexte de départ reste petit ;
  - le bon skill est chargé pour 3 tâches tests (science, cyber, diagramme).

## ÉTAPE 10 — Interface

- **Banc d'essai :** Open WebUI (`open-webui/open-webui`), connecté au runtime ou à MCP. La marque Open WebUI doit rester, ce qui est sans conséquence en dessous de 50 utilisateurs.
- **Produit RATISS :** assistant-ui (`assistant-ui/assistant-ui`, MIT) avec 3 vues : **Chat / Tâches / Activité** (flux d'Events et approbations en attente). Modèle de référence : `vercel/chatbot`.
- **Accès :** reverse proxy HTTPS avec authentification devant l'UI et l'API ; Pomerium plus tard.
- ✅ **Contrôle :** une approbation demandée par le runtime apparaît dans l'UI et se valide depuis un téléphone.

## ÉTAPE 11 — Workflows métier

| Workflow | Serveurs MCP | Skills | Sandbox |
|---|---|---|---|
| 🔬 Recherche | arxiv-mcp-server (+ academic-mcp en test), fetch | K-Dense | Python / Jupyter |
| 💻 Dev | filesystem, git, github-mcp-server, context7 | diagram-design | Repository |
| 🛡️ Cyber | mcp-security-hub (nmap, nuclei, semgrep, yara, trivy) dans un **réseau Docker isolé**, cibles autorisées uniquement, actions actives = REQUIRE_APPROVAL | Cybersecurity-Skills (sélection) | Browser + gVisor, puis Firecracker plus tard |

---

## 🧱 Carte du `docker-compose.yml` V1 (services, sans code)

| Service | Brique | Réseau |
|---|---|---|
| `postgres` | PostgreSQL + pgvector | core |
| `redis` | Redis | core |
| `objects` | RustFS | core |
| `llm-gateway` | LiteLLM | core |
| `ollama` | Ollama (option) | core |
| `mcp-gateway` | ContextForge | core + tools |
| `opa` | OPA | core |
| `runtime` | LangGraph + deepagents + API | core |
| `sandbox-python` | llm-sandbox (runtime `runsc`) | tools (sans internet) |
| `jupyter` | JupyterLab + jupyter-mcp-server | tools |
| `browser` | playwright-mcp | tools (internet filtré) |
| `ui` | Open WebUI, puis assistant-ui | edge |
| `proxy` | reverse proxy HTTPS/Auth | edge |
| `traces` | Langfuse (option) | core |

Le brief interdit en V1 : Kubernetes, swarm, inférence distribuée, application mobile, voix.

---

## 🧭 Ce que GLM doit réellement écrire

Tout le reste est de la configuration de briques existantes. GLM n'écrit que 5 choses :

1. les 6 schémas et les 2 registres YAML (étape 0) ;
2. le **hook de politique** runtime ↔ OPA ↔ `interrupt()` (étape 6) ;
3. le **pont de provenance** : Events → SHA-256 → journal RATISS-Framework → manifest de run (étape 8) ;
4. le **script d'admission** : scan → hash → registre (étape 4) ;
5. l'UI maison (étape 10, à la fin seulement).
