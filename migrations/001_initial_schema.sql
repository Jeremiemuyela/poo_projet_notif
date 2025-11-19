-- Migration initiale - Schéma complet de la base de données
-- Version: 001
-- Date: 2025-11-19

-- ==================== TABLE: users ====================
-- Stocke les utilisateurs authentifiés (admin, operator, viewer)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CHECK (role IN ('admin', 'operator', 'viewer'))
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(active);


-- ==================== TABLE: students ====================
-- Stocke les étudiants avec leurs informations
CREATE TABLE IF NOT EXISTS students (
    id VARCHAR(50) PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telephone VARCHAR(20),
    langue VARCHAR(5) DEFAULT 'fr',
    faculte VARCHAR(100),
    promotion VARCHAR(10),
    canal_prefere VARCHAR(20) DEFAULT 'email',
    actif BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (langue IN ('fr', 'en')),
    CHECK (canal_prefere IN ('email', 'sms', 'app'))
);

CREATE INDEX IF NOT EXISTS idx_students_faculte ON students(faculte);
CREATE INDEX IF NOT EXISTS idx_students_promotion ON students(promotion);
CREATE INDEX IF NOT EXISTS idx_students_actif ON students(actif);
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);


-- ==================== TABLE: preferences ====================
-- Stocke les préférences de notification des étudiants
CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(50) UNIQUE NOT NULL,
    langue VARCHAR(5),
    canal_prefere VARCHAR(20),
    actif BOOLEAN DEFAULT 1,
    notifications_meteo BOOLEAN DEFAULT 1,
    notifications_securite BOOLEAN DEFAULT 1,
    notifications_sante BOOLEAN DEFAULT 1,
    notifications_infra BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_preferences_student ON preferences(student_id);


-- ==================== TABLE: notifications_log ====================
-- Journal de toutes les notifications envoyées
CREATE TABLE IF NOT EXISTS notifications_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type VARCHAR(20) NOT NULL,
    titre VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    priorite VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_by_user_id INTEGER,
    nb_destinataires INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    FOREIGN KEY (sent_by_user_id) REFERENCES users(id),
    CHECK (type IN ('meteo', 'securite', 'sante', 'infra')),
    CHECK (priorite IN ('CRITIQUE', 'HAUTE', 'NORMALE'))
);

CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications_log(type);
CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON notifications_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_by ON notifications_log(sent_by_user_id);


-- ==================== TABLE: notifications_recipients ====================
-- Détail des destinataires pour chaque notification
CREATE TABLE IF NOT EXISTS notifications_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id INTEGER NOT NULL,
    student_id VARCHAR(50) NOT NULL,
    canal VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered BOOLEAN DEFAULT 0,
    read BOOLEAN DEFAULT 0,
    read_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (notification_id) REFERENCES notifications_log(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recipients_notification ON notifications_recipients(notification_id);
CREATE INDEX IF NOT EXISTS idx_recipients_student ON notifications_recipients(student_id);
CREATE INDEX IF NOT EXISTS idx_recipients_read ON notifications_recipients(read);


-- ==================== TABLE: queue_tasks ====================
-- File d'attente persistante des tâches de notification
CREATE TABLE IF NOT EXISTS queue_tasks (
    id VARCHAR(36) PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    data TEXT NOT NULL,  -- JSON stringifié
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error TEXT,
    result TEXT,  -- JSON stringifié
    CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON queue_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON queue_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON queue_tasks(type);


-- ==================== TABLE: metrics ====================
-- Métriques de performance des notifications
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notifier_name VARCHAR(50) NOT NULL,
    duration REAL NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metrics_notifier ON metrics(notifier_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_success ON metrics(success);


-- ==================== TABLE: translations ====================
-- Traductions manuelles pour le système multilingue
CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_text TEXT NOT NULL UNIQUE,
    fr TEXT,
    en TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_translations_key ON translations(key_text);


-- ==================== TABLE: circuit_breaker_state ====================
-- État des circuit breakers pour chaque notificateur
CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    notifier_name VARCHAR(50) PRIMARY KEY,
    failures INTEGER DEFAULT 0,
    is_open BOOLEAN DEFAULT 0,
    last_failure_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==================== TABLE: config ====================
-- Configuration système (retry, circuit breaker, etc.)
CREATE TABLE IF NOT EXISTS config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    namespace VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(namespace, key),
    CHECK (value_type IN ('string', 'integer', 'float', 'boolean', 'json'))
);

CREATE INDEX IF NOT EXISTS idx_config_namespace ON config(namespace);


-- ==================== VUES UTILES ====================

-- Vue pour obtenir rapidement les statistiques par faculté
CREATE VIEW IF NOT EXISTS v_stats_facultes AS
SELECT 
    faculte,
    COUNT(*) as nb_etudiants,
    SUM(CASE WHEN actif = 1 THEN 1 ELSE 0 END) as nb_actifs,
    COUNT(DISTINCT promotion) as nb_promotions
FROM students
WHERE faculte IS NOT NULL AND faculte != ''
GROUP BY faculte;


-- Vue pour les statistiques de notifications par type
CREATE VIEW IF NOT EXISTS v_stats_notifications AS
SELECT 
    type,
    COUNT(*) as total,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as reussis,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as echecs,
    AVG(nb_destinataires) as avg_destinataires,
    MAX(timestamp) as derniere_notification
FROM notifications_log
GROUP BY type;


-- Vue pour les métriques de performance par notificateur
CREATE VIEW IF NOT EXISTS v_performance_notificateurs AS
SELECT 
    notifier_name,
    COUNT(*) as total_executions,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as reussites,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as echecs,
    ROUND(AVG(duration), 3) as avg_duration,
    ROUND(MIN(duration), 3) as min_duration,
    ROUND(MAX(duration), 3) as max_duration,
    ROUND(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM metrics
GROUP BY notifier_name;


-- ==================== TRIGGERS ====================

-- Trigger pour mettre à jour updated_at automatiquement sur students
CREATE TRIGGER IF NOT EXISTS update_students_timestamp 
AFTER UPDATE ON students
FOR EACH ROW
BEGIN
    UPDATE students SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;


-- Trigger pour mettre à jour updated_at automatiquement sur preferences
CREATE TRIGGER IF NOT EXISTS update_preferences_timestamp 
AFTER UPDATE ON preferences
FOR EACH ROW
BEGIN
    UPDATE preferences SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;


-- Trigger pour mettre à jour updated_at automatiquement sur translations
CREATE TRIGGER IF NOT EXISTS update_translations_timestamp 
AFTER UPDATE ON translations
FOR EACH ROW
BEGIN
    UPDATE translations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;


-- Trigger pour mettre à jour updated_at automatiquement sur config
CREATE TRIGGER IF NOT EXISTS update_config_timestamp 
AFTER UPDATE ON config
FOR EACH ROW
BEGIN
    UPDATE config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;


-- ==================== DONNÉES INITIALES ====================

-- Configuration par défaut pour Retry
INSERT OR IGNORE INTO config (namespace, key, value, value_type) VALUES
    ('retry', 'attempts', '3', 'integer'),
    ('retry', 'delay', '1', 'integer'),
    ('retry', 'backoff', '2', 'integer');

-- Configuration par défaut pour Circuit Breaker
INSERT OR IGNORE INTO config (namespace, key, value, value_type) VALUES
    ('circuit_breaker', 'threshold', '3', 'integer'),
    ('circuit_breaker', 'cooldown', '5', 'integer');

-- Traductions de base
INSERT OR IGNORE INTO translations (key_text, fr, en) VALUES
    ('alerte_meteo', 'Alerte météorologique', 'Weather Alert'),
    ('alerte_securite', 'Alerte de sécurité', 'Security Alert'),
    ('alerte_sante', 'Alerte de santé', 'Health Alert'),
    ('alerte_infra', 'Alerte infrastructure', 'Infrastructure Alert'),
    ('ÉVACUATION IMMÉDIATE', 'ÉVACUATION IMMÉDIATE', 'IMMEDIATE EVACUATION'),
    ('Tempête prévue ce soir', 'Tempête prévue ce soir', 'Storm expected tonight');

