CREATE TABLE IF NOT EXISTS aptguide3_users (
  user_id VARCHAR(64) PRIMARY KEY,
  source VARCHAR(32) NOT NULL DEFAULT 'lease',
  display_name VARCHAR(128) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_sessions (
  session_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  active_task VARCHAR(64) NULL,
  rolling_summary TEXT NOT NULL,
  context JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_sessions_user_id (user_id),
  INDEX idx_aptguide3_sessions_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_messages (
  message_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  request_id VARCHAR(80) NOT NULL,
  role VARCHAR(32) NOT NULL,
  content TEXT NOT NULL,
  metadata JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_messages_session_id (session_id),
  INDEX idx_aptguide3_messages_user_id (user_id),
  INDEX idx_aptguide3_messages_request_id (request_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_pending_actions (
  pending_action_id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  action_type VARCHAR(80) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  payload JSON NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_pending_actions_session_id (session_id),
  INDEX idx_aptguide3_pending_actions_user_id (user_id),
  INDEX idx_aptguide3_pending_actions_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_memories (
  memory_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  kind VARCHAR(64) NOT NULL,
  key_name VARCHAR(128) NOT NULL,
  value_json JSON NOT NULL,
  source_session_id VARCHAR(64) NOT NULL DEFAULT '',
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_memories_user_id (user_id),
  INDEX idx_aptguide3_memories_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_memory_candidates (
  candidate_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  session_id VARCHAR(64) NOT NULL,
  kind VARCHAR(64) NOT NULL,
  payload JSON NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_memory_candidates_user_id (user_id),
  INDEX idx_aptguide3_memory_candidates_session_id (session_id),
  INDEX idx_aptguide3_memory_candidates_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_handoff_tickets (
  ticket_id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'open',
  trigger_type VARCHAR(64) NOT NULL,
  summary JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_handoff_tickets_session_id (session_id),
  INDEX idx_aptguide3_handoff_tickets_user_id (user_id),
  INDEX idx_aptguide3_handoff_tickets_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_operator_messages (
  message_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  ticket_id VARCHAR(64) NOT NULL,
  sender VARCHAR(32) NOT NULL,
  content TEXT NOT NULL,
  metadata JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_operator_messages_ticket_id (ticket_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_trace_events (
  event_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  trace_id VARCHAR(80) NOT NULL,
  request_id VARCHAR(80) NOT NULL DEFAULT '',
  session_id VARCHAR(64) NOT NULL DEFAULT '',
  event_name VARCHAR(128) NOT NULL,
  payload JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_trace_events_trace_id (trace_id),
  INDEX idx_aptguide3_trace_events_session_id (session_id),
  INDEX idx_aptguide3_trace_events_request_id (request_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_procedure_runs (
  run_id VARCHAR(80) PRIMARY KEY,
  request_id VARCHAR(80) NOT NULL,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  procedure_name VARCHAR(80) NOT NULL,
  route VARCHAR(64) NOT NULL,
  task VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  metadata JSON NOT NULL,
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME NULL,
  INDEX idx_aptguide3_procedure_runs_session_id (session_id),
  INDEX idx_aptguide3_procedure_runs_request_id (request_id),
  INDEX idx_aptguide3_procedure_runs_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_audit_log (
  audit_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL DEFAULT '',
  session_id VARCHAR(64) NOT NULL DEFAULT '',
  event_type VARCHAR(128) NOT NULL,
  payload JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_audit_log_user_id (user_id),
  INDEX idx_aptguide3_audit_log_event_type (event_type)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_room_identity_map (
  source_system VARCHAR(32) NOT NULL,
  source_record_id VARCHAR(128) NOT NULL,
  canonical_room_id VARCHAR(128) NOT NULL DEFAULT '',
  business_system VARCHAR(32) NOT NULL DEFAULT 'lease',
  business_room_id VARCHAR(128) NULL,
  verification_status VARCHAR(32) NOT NULL DEFAULT 'unmapped',
  match_method VARCHAR(64) NOT NULL DEFAULT 'unmapped',
  match_confidence DECIMAL(5,4) NOT NULL DEFAULT 0.0000,
  metadata JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (source_system, source_record_id),
  INDEX idx_aptguide3_room_identity_business_room_id (business_room_id),
  INDEX idx_aptguide3_room_identity_verification_status (verification_status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
