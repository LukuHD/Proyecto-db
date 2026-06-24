/**
 * SISTEMA CENTRALIZADO - HOSPITAL GENERAL DEL SUR
 * Archivo central de validaciones del lado del cliente.
 * Mapeo estricto a las Especificaciones del Proyecto (Casos de Uso, RN y Tabla de Errores).
 */

// 1. EXPRESIONES REGULARES (Reglas de formato general)
const regexLetras     = /^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$/; 
const regexTelefono   = /^[0-9]{10}$/;
const regexCurp       = /^[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z][0-9]$/; 
const regexCorreoGral = /^[^\s@]+@[^\s@]+\.[^\s@]+$/; 
const regexCorreoInst = /^[a-zA-Z0-9._-]+@ipn\.mx$/; // RN-08 y login

// 2. FUNCIONES AUXILIARES DE INTERFAZ
function mostrarError(mensaje, idError) {
    const pError = document.getElementById(idError);
    if (pError) pError.innerText = mensaje;
}

function limpiarErrores() {
    document.querySelectorAll('.text-danger').forEach(el => el.innerText = "");
}

function soloLetras(input) {
    input.value = input.value.replace(/[^A-Za-zÁÉÍÓÚÑáéíóúñ\s]/g, "");
}

function soloNumeros(input) {
    input.value = input.value.replace(/\D/g, "");
}

// =====================================================================
// MÓDULO DE RECEPCIÓN (ACT-01)
// =====================================================================

/**
 * CU-02 / RF-01: Registrar paciente nuevo
 * Extrae, valida y estructura los campos del formulario según Mockup 4.3.1.
 * Retorna un objeto JSON listo (RT-06) o null si la validación falla.
 */
function extraerYValidarPaciente() {
    limpiarErrores();
    let valido = true;

    // Campos del paciente
    const nombres = document.getElementById("nombres")?.value.trim();
    const apellidos = document.getElementById("apellidos")?.value.trim();
    const curp = document.getElementById("curp")?.value.trim().toUpperCase();
    const fechaNac = document.getElementById("fechaNac")?.value;
    const sexo = document.getElementById("sexo")?.value;
    const telefono = document.getElementById("telefono")?.value.trim();
    const correo = document.getElementById("correo")?.value.trim();
    const direccion = document.getElementById("direccion")?.value.trim();
    const tipoSangre = document.getElementById("tipoSangre")?.value;
    const alergias = document.getElementById("alergias")?.value.trim();
    const enfCronicas = document.getElementById("enfCronicas")?.value.trim();
    const contactoEme = document.getElementById("contactoEmergencia")?.value.trim();

    // Validaciones obligatorias (NOM-004-SSA3-2012)
    if (!nombres || !regexLetras.test(nombres)) { mostrarError("Nombre obligatorio y solo letras.", "errorNombres"); valido = false; }
    if (!apellidos || !regexLetras.test(apellidos)) { mostrarError("Apellidos obligatorios y solo letras.", "errorApellidos"); valido = false; }
    if (!curp || !regexCurp.test(curp)) { mostrarError("Formato de CURP inválido.", "errorCurp"); valido = false; }
    if (!fechaNac) { mostrarError("Fecha de nacimiento requerida.", "errorFechaNac"); valido = false; }
    if (!sexo) { mostrarError("Seleccione el sexo.", "errorSexo"); valido = false; }
    if (!telefono || !regexTelefono.test(telefono)) { mostrarError("El teléfono debe tener 10 dígitos.", "errorTelefono"); valido = false; }
    if (!direccion) { mostrarError("La dirección es obligatoria.", "errorDireccion"); valido = false; }
    
    // Validación opcional de correo
    if (correo && !regexCorreoGral.test(correo)) { mostrarError("Formato de correo inválido.", "errorCorreo"); valido = false; }

    if (!valido) return null;

    return { 
        nombres, apellidos, curp, fechaNac, sexo, telefono, correo, 
        direccion, tipoSangre, alergias, enfCronicas, contactoEme 
    };
}

/**
 * CU-04: Actualizar datos del paciente 
 * Mapeo a ERR-05: Modificación de parámetros clínicos por recepción genera denegación.
 * Se ejecuta al cargar la vista de actualización de un paciente.
 */
function bloquearSignosVitalesRecepcion() {
    const camposVitales = document.querySelectorAll('.signos-vitales-input');
    camposVitales.forEach(campo => {
        campo.readOnly = true;
        campo.style.backgroundColor = "#e9ecef"; // Estilo visual de bloqueo
        campo.title = "ERR-05: La modificación de signos vitales es exclusiva de enfermería.";
    });
}

/**
 * CU-10 / RN-03: Agendar cita de laboratorio
 * Mapeo a ERR-06: Registro fuera de margen temporal.
 */
function validarTemporalidadLaboratorio(fechaConsultaStr, fechaLabStr) {
    limpiarErrores();
    
    if (!fechaConsultaStr || !fechaLabStr) return false;

    // Convertir y ajustar zona horaria a medianoche para evitar saltos de horas
    const fechaConsulta = new Date(fechaConsultaStr + 'T00:00:00');
    const fechaLab = new Date(fechaLabStr + 'T00:00:00');
    
    // Cálculo de días de diferencia
    const diffMilisegundos = fechaConsulta - fechaLab;
    const diffDias = Math.floor(diffMilisegundos / (1000 * 60 * 60 * 24));

    if (diffDias >= 7 && diffDias <= 14) {
        return true;
    } else {
        mostrarError("ERR-06: Error de temporalidad. El estudio debe agendarse entre 1 y 2 semanas antes de la consulta médica.", "errorFechaLab");
        return false;
    }
}

// =====================================================================
// MÓDULO DE LABORATORIO (ACT-02)
// =====================================================================

/**
 * CU-12 / CU-13: Capturar, Validar y liberar resultados (RN-04)
 * Estructura de extracción de resultados antes de enviar JSON.
 */
function extraerResultadosLaboratorio() {
    limpiarErrores();
    
    const folioOrden = document.getElementById("folioOrden")?.value.trim();
    const observaciones = document.getElementById("observacionesClinicas")?.value.trim();
    
    // En el futuro, aquí se iterará sobre los inputs de la tabla (Imagen 4.3.4)
    // para extraer: Hemoglobina, Leucocitos, etc.
    
    if(!folioOrden) {
        mostrarError("ERR-04: No se puede registrar el resultado. Verifique que exista la orden de laboratorio.", "errorFolio");
        return null;
    }

    return {
        folio: folioOrden,
        observaciones: observaciones,
        // resultadosAnaliticos: arreglo_de_valores_extraidos
    };
}