# =============================================================================
# ArcZhiin — SQLite Database Schema
# =============================================================================

-- Enable WAL mode for concurrent read/write performance
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- -----------------------------------------------------------------------------
-- Table: conversations
-- Stores chat sessions with metadata.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY,
    title       TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- Table: messages
-- Individual messages within a conversation.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content         TEXT NOT NULL,
    model           TEXT,
    tokens_used     INTEGER DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, created_at);

-- -----------------------------------------------------------------------------
-- Table: semantic_memory
-- Long-term user facts and preferences extracted from conversations.
-- e.g. "User prefers 22°C", "User's company is ZenZhiin"
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS semantic_memory (
    id          TEXT PRIMARY KEY,
    fact        TEXT NOT NULL,
    category    TEXT,
    source_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
    embedding   BLOB,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- Table: episodic_memory
-- Summarized conversation episodes for long-term recall.
-- e.g. "On Aug 14, user discussed building an AI assistant called ArcZhiin"
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS episodic_memory (
    id                TEXT PRIMARY KEY,
    conversation_id   TEXT REFERENCES conversations(id) ON DELETE SET NULL,
    summary           TEXT NOT NULL,
    key_topics        TEXT,
    embedding         BLOB,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- Table: device_registry
-- Cached smart home device information from Home Assistant.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS device_registry (
    entity_id       TEXT PRIMARY KEY,
    friendly_name   TEXT NOT NULL,
    domain          TEXT NOT NULL,
    state           TEXT,
    attributes      TEXT,
    embedding       BLOB,
    last_synced     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- Table: tasks
-- User tasks and reminders managed by ArcZhiin.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'done', 'cancelled')),
    due_date    TIMESTAMP,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
