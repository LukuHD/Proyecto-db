CREATE DATABASE IF NOT EXISTS hospital CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hospital;

CREATE TABLE IF NOT EXISTS paciente (
  id_paciente INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  apellidos VARCHAR(140) NOT NULL,
  curp CHAR(18) NOT NULL UNIQUE,
  fecha_nac DATE NOT NULL,
  sexo VARCHAR(10) NOT NULL,
  telefono VARCHAR(20) NOT NULL,
  correo VARCHAR(120),
  direccion VARCHAR(255) NOT NULL,
  tipo_sangre VARCHAR(5),
  alergias TEXT,
  enf_cronicas TEXT,
  contacto_emergencia VARCHAR(255),
  estado VARCHAR(20) NOT NULL DEFAULT 'Activo',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medico (
  id_medico INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  apellidos VARCHAR(140) NOT NULL,
  especialidad VARCHAR(120) NOT NULL,
  cedula VARCHAR(40) NOT NULL UNIQUE,
  correo VARCHAR(120),
  telefono VARCHAR(20),
  estado VARCHAR(20) NOT NULL DEFAULT 'Activo',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cita (
  id_cita INT AUTO_INCREMENT PRIMARY KEY,
  id_paciente INT NOT NULL,
  id_medico INT NOT NULL,
  fecha DATE NOT NULL,
  hora TIME NOT NULL,
  motivo VARCHAR(255) NOT NULL,
  estado ENUM('Programada', 'Modificada', 'Cancelada', 'Atendida') NOT NULL DEFAULT 'Programada',
  reprogramada BOOLEAN NOT NULL DEFAULT FALSE,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_cita_paciente FOREIGN KEY (id_paciente) REFERENCES paciente(id_paciente),
  CONSTRAINT fk_cita_medico FOREIGN KEY (id_medico) REFERENCES medico(id_medico),
  INDEX idx_cita_disponibilidad (id_medico, fecha, hora, estado)
);

CREATE TABLE IF NOT EXISTS orden_laboratorio (
  id_orden INT AUTO_INCREMENT PRIMARY KEY,
  folio VARCHAR(20) UNIQUE,
  id_paciente INT NOT NULL,
  tipo_estudio VARCHAR(120) NOT NULL,
  fecha_solicitud DATE NOT NULL,
  medico VARCHAR(140) NOT NULL,
  especialidad VARCHAR(120) NOT NULL,
  descripcion TEXT NOT NULL,
  estado ENUM('Solicitado', 'Realizado', 'Cancelado', 'Liberado') NOT NULL DEFAULT 'Solicitado',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_orden_paciente FOREIGN KEY (id_paciente) REFERENCES paciente(id_paciente),
  INDEX idx_orden_folio (folio),
  INDEX idx_orden_estado (estado)
);

CREATE TABLE IF NOT EXISTS cita_laboratorio (
  id_cita_laboratorio INT AUTO_INCREMENT PRIMARY KEY,
  id_orden INT NOT NULL,
  fecha_consulta DATE NOT NULL,
  fecha_laboratorio DATE NOT NULL,
  hora TIME NOT NULL,
  estado ENUM('Programada', 'Cancelada', 'Realizada') NOT NULL DEFAULT 'Programada',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cita_lab_orden FOREIGN KEY (id_orden) REFERENCES orden_laboratorio(id_orden),
  INDEX idx_cita_lab_fecha (fecha_laboratorio, hora, estado)
);

CREATE TABLE IF NOT EXISTS resultado_laboratorio (
  id_resultado INT AUTO_INCREMENT PRIMARY KEY,
  id_orden INT NOT NULL,
  resultados_json JSON,
  observaciones TEXT,
  fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_resultado_orden FOREIGN KEY (id_orden) REFERENCES orden_laboratorio(id_orden)
);

DROP PROCEDURE IF EXISTS add_column_if_missing;

DELIMITER //

CREATE PROCEDURE add_column_if_missing(
  IN p_table_name VARCHAR(64),
  IN p_column_name VARCHAR(64),
  IN p_column_definition TEXT
)
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = p_table_name
      AND column_name = p_column_name
  ) THEN
    SET @ddl = CONCAT('ALTER TABLE `', p_table_name, '` ADD COLUMN `', p_column_name, '` ', p_column_definition);
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END//

DELIMITER ;

CALL add_column_if_missing('paciente', 'apellidos', 'VARCHAR(140)');
CALL add_column_if_missing('paciente', 'fecha_nac', 'DATE');
CALL add_column_if_missing('paciente', 'sexo', 'VARCHAR(10)');
CALL add_column_if_missing('paciente', 'telefono', 'VARCHAR(20)');
CALL add_column_if_missing('paciente', 'correo', 'VARCHAR(120)');
CALL add_column_if_missing('paciente', 'direccion', 'VARCHAR(255)');
CALL add_column_if_missing('paciente', 'tipo_sangre', 'VARCHAR(5)');
CALL add_column_if_missing('paciente', 'alergias', 'TEXT');
CALL add_column_if_missing('paciente', 'enf_cronicas', 'TEXT');
CALL add_column_if_missing('paciente', 'contacto_emergencia', 'VARCHAR(255)');
CALL add_column_if_missing('paciente', 'estado', 'VARCHAR(20) NOT NULL DEFAULT ''Activo''');

CALL add_column_if_missing('medico', 'apellidos', 'VARCHAR(140)');
CALL add_column_if_missing('medico', 'especialidad', 'VARCHAR(120)');
CALL add_column_if_missing('medico', 'cedula', 'VARCHAR(40)');
CALL add_column_if_missing('medico', 'correo', 'VARCHAR(120)');
CALL add_column_if_missing('medico', 'telefono', 'VARCHAR(20)');
CALL add_column_if_missing('medico', 'estado', 'VARCHAR(20) NOT NULL DEFAULT ''Activo''');

CALL add_column_if_missing('cita', 'id_paciente', 'INT');
CALL add_column_if_missing('cita', 'id_medico', 'INT');
CALL add_column_if_missing('cita', 'fecha', 'DATE');
CALL add_column_if_missing('cita', 'hora', 'TIME');
CALL add_column_if_missing('cita', 'motivo', 'VARCHAR(255)');
CALL add_column_if_missing('cita', 'estado', 'VARCHAR(20) NOT NULL DEFAULT ''Programada''');
CALL add_column_if_missing('cita', 'reprogramada', 'BOOLEAN NOT NULL DEFAULT FALSE');

CALL add_column_if_missing('orden_laboratorio', 'folio', 'VARCHAR(20)');
CALL add_column_if_missing('orden_laboratorio', 'id_paciente', 'INT');
CALL add_column_if_missing('orden_laboratorio', 'id_medico', 'INT');
CALL add_column_if_missing('orden_laboratorio', 'tipo_estudio', 'VARCHAR(120)');
CALL add_column_if_missing('orden_laboratorio', 'fecha_solicitud', 'DATE');
CALL add_column_if_missing('orden_laboratorio', 'medico', 'VARCHAR(140)');
CALL add_column_if_missing('orden_laboratorio', 'especialidad', 'VARCHAR(120)');
CALL add_column_if_missing('orden_laboratorio', 'descripcion', 'TEXT');
CALL add_column_if_missing('orden_laboratorio', 'estado', 'VARCHAR(20) NOT NULL DEFAULT ''Solicitado''');

CALL add_column_if_missing('cita_laboratorio', 'id_orden', 'INT');
CALL add_column_if_missing('cita_laboratorio', 'fecha_consulta', 'DATE');
CALL add_column_if_missing('cita_laboratorio', 'fecha_laboratorio', 'DATE');
CALL add_column_if_missing('cita_laboratorio', 'hora', 'TIME');
CALL add_column_if_missing('cita_laboratorio', 'estado', 'VARCHAR(20) NOT NULL DEFAULT ''Programada''');

CALL add_column_if_missing('resultado_laboratorio', 'id_orden', 'INT');
CALL add_column_if_missing('resultado_laboratorio', 'resultados_json', 'JSON');
CALL add_column_if_missing('resultado_laboratorio', 'observaciones', 'TEXT');

DROP PROCEDURE add_column_if_missing;

INSERT IGNORE INTO medico (id_medico, nombre, apellidos, especialidad, cedula, correo, telefono)
VALUES
  (1, 'Rafael', 'Ramirez', 'Cardiologia', 'CED-78213', 'rramirez@ipn.mx', '5500000001'),
  (2, 'Elena', 'Torres', 'Neurologia', 'CED-65120', 'etorres@ipn.mx', '5500000002');
