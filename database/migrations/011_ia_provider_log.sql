-- ================================================================
-- SIGAB Migration 011 — Log de proveedor IA (WS-3 / WS-4)
-- Registra cada llamada al copilot: qué proveedor respondió,
-- cuántos tokens se usaron y desde qué endpoint se originó.
-- Esto habilita el panel de consumo (WS-4) sin costo de tiempo real.
-- ================================================================
USE sigab;

CREATE TABLE IF NOT EXISTS log_ia_proveedor (
    id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    timestamp     DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    proveedor     ENUM('edge_local','cloud_minimax','no_disponible') NOT NULL,
    modelo        VARCHAR(80)  NOT NULL,
    endpoint      VARCHAR(60)  NOT NULL COMMENT 'copilot.chat | copilot.diagnostico | copilot.resumen | etc.',
    usuario_id    INT UNSIGNED NULL,
    tokens_prompt INT UNSIGNED NULL COMMENT 'Sólo disponible en MiniMax (OpenAI usage)',
    tokens_comp   INT UNSIGNED NULL COMMENT 'Tokens de completion',
    latencia_ms   INT UNSIGNED NULL COMMENT 'Tiempo de respuesta en ms',
    ok            BOOLEAN      NOT NULL DEFAULT TRUE,
    error_msg     VARCHAR(255) NULL,

    INDEX idx_ts   (timestamp),
    INDEX idx_prov (proveedor),
    INDEX idx_user (usuario_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Auditoría de uso de IA — habilita panel de consumo de tokens (WS-4)';

-- Vista diaria de consumo por proveedor
CREATE OR REPLACE VIEW v_ia_consumo_diario AS
SELECT
    DATE(timestamp)                                          AS fecha,
    proveedor,
    COUNT(*)                                                 AS llamadas,
    SUM(IF(ok = TRUE, 1, 0))                                 AS exitosas,
    SUM(IF(ok = FALSE, 1, 0))                                AS fallidas,
    COALESCE(SUM(tokens_prompt + tokens_comp), 0)            AS tokens_totales,
    ROUND(AVG(latencia_ms), 0)                               AS latencia_avg_ms
FROM log_ia_proveedor
GROUP BY DATE(timestamp), proveedor
ORDER BY fecha DESC, proveedor;
