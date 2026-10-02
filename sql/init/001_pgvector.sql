-- RATISS LABS AGENT — initialisation Phase 0
-- Active pgvector pour la mémoire documentaire (V1).

CREATE EXTENSION IF NOT EXISTS vector;

-- Table minimale de la mémoire documentaire.
-- Le schéma complet sera défini en Phase 3 ; ici on garantit que
-- l'extension et une table d'accueil existent pour ne pas bloquer la stack.

CREATE TABLE IF NOT EXISTS memoire_documentaire (
    id          BIGSERIAL PRIMARY KEY,
    contenu     TEXT NOT NULL,
    embedding   vector(1536),
    source      TEXT,
    sha256      CHAR(64),
    cree_le     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_memoire_embedding
    ON memoire_documentaire USING hnsw (embedding vector_cosine_ops);
