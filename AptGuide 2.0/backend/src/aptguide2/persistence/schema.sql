-- AptGuide 2.0 MySQL Schema
-- Run: mysql -h 192.168.211.128 -u chove -p least < schema.sql
-- 使用 least 数据库，所有表以 aptguide_ 前缀避免冲突

CREATE TABLE IF NOT EXISTS aptguide_sessions (
  session_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  phase VARCHAR(64) NOT NULL DEFAULT 'idle',
  active_task VARCHAR(64) NULL,
  task_slots JSON NOT NULL,
  rolling_summary TEXT NOT NULL,
  long_term_profile_snapshot JSON NOT NULL,
  handoff_state JSON NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide_sessions_user_id (user_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide_recent_messages (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  role VARCHAR(32) NOT NULL,
  content TEXT NOT NULL,
  request_id VARCHAR(80) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide_recent_messages_session_id (session_id),
  INDEX idx_aptguide_recent_messages_user_id (user_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide_pending_actions (
  confirmation_id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  action_type VARCHAR(80) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  payload JSON NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide_pending_actions_session_id (session_id),
  INDEX idx_aptguide_pending_actions_user_id (user_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide_user_profiles (
  user_id VARCHAR(64) PRIMARY KEY,
  profile JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide_memory_candidates (
  candidate_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  session_id VARCHAR(64) NOT NULL,
  kind VARCHAR(64) NOT NULL,
  payload JSON NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide_memory_candidates_user_id (user_id),
  INDEX idx_aptguide_memory_candidates_session_id (session_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide_handoff_tickets (
  ticket_id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'open',
  trigger_type VARCHAR(64) NOT NULL,
  summary JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide_handoff_tickets_session_id (session_id),
  INDEX idx_aptguide_handoff_tickets_user_id (user_id),
  INDEX idx_aptguide_handoff_tickets_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide_operator_messages (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  ticket_id VARCHAR(64) NOT NULL,
  sender VARCHAR(32) NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide_operator_messages_ticket_id (ticket_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide_audit_log (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  session_id VARCHAR(64) NOT NULL DEFAULT '',
  event_type VARCHAR(80) NOT NULL,
  payload JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide_audit_log_user_id (user_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
