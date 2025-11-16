from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from adaptador_contexto_boliviano import NormalizadorOracion
from gestor_bd import GestorBaseDatos
from modelo_consulta import AgenteIA

# Crear la aplicación Flask
app = Flask(__name__)
CORS(app)

# Instanciar módulos personalizados
normalizacion_pregunta = NormalizadorOracion() 
bd = GestorBaseDatos()
agenteIA = AgenteIA(bd)

# CORRECCIÓN 2: Función llamar_gpt que estaba faltante
def llamar_gpt(prompt):
    """
    Función para llamar al modelo usando el agente IA existente
    """
    try:
        # Usar el método consultar_con_contexto del agente
        resultado = agenteIA.consultar_con_contexto(prompt, "")
        return resultado
    except Exception as e:
        print(f"Error en llamar_gpt: {e}")
        return f"Error: {str(e)}"

PROMPT_ANALISIS_CLASIFICACION = """
# ===== IDENTIDAD DEL AGENTE =====
Eres "IncubaBot", un especialista en análisis empresarial y psicológico para clasificar emprendedores jóvenes bolivianos en rutas de aprendizaje personalizadas.

# ===== TU MISIÓN =====
Analizar el perfil completo del usuario y generar un JSON con:
1. Clasificación automática (PRE-INCUBADORA vs INCUBADORA)
2. Análisis empresarial detallado
3. Perfil psicológico y emocional
4. Recomendaciones específicas para su contexto boliviano

# ===== DATOS DE ENTRADA =====
INFORMACIÓN PERSONAL:
- Nombre: {nombre}
- Edad: {edad}
- Ciudad: {ciudad}
- Nivel educativo: {educacion}

ESTADO ACTUAL DEL NEGOCIO:
- Descripción: {descripcion_negocio}
- Tiempo en funcionamiento: {tiempo_funcionamiento}
- Ingresos mensuales: {ingresos_mensuales}
- Número de clientes: {numero_clientes}
- Productos/servicios: {productos_servicios}

CONOCIMIENTOS TÉCNICOS (Escala 1-5):
- Finanzas básicas: {conocimiento_finanzas}
- Marketing digital: {conocimiento_marketing}
- Ventas: {conocimiento_ventas}
- Modelo de negocio: {conocimiento_modelo_negocio}
- Uso de tecnología: {conocimiento_tecnologia}

PERFIL PSICOLÓGICO (Escala 1-5):
- Resilencia ante fracasos: {resilencia}
- Motivación emprendedora: {motivacion}
- Gestión del estrés: {gestion_estres}
- Habilidades de comunicación: {comunicacion}
- Autoestima: {autoestima}
- Capacidad de liderazgo: {liderazgo}

CONTEXTO BOLIVIANO:
- Rubro del emprendimiento: {rubro}
- Zona/barrio donde opera: {zona_operacion}
- Apoyo familiar: {apoyo_familiar}
- Acceso a internet: {acceso_internet}
- Disponibilidad de tiempo semanal: {tiempo_disponible}

Responde ÚNICAMENTE con un JSON válido con la clasificación y análisis detallado.
"""

PROMPT_GENERADOR_RETOS = """
# ===== IDENTIDAD DEL AGENTE =====
Eres "RetoBot", un especialista en crear desafíos gamificados para emprendedores bolivianos.

# ===== DATOS DE CONTEXTO DEL USUARIO =====
- Nombre: {nombre}
- Ciudad: {ciudad}
- Tipo negocio: {tipo_negocio}
- Nivel: {nivel}
- Ingresos: {ingresos_actuales}

Genera 3 retos personalizados en formato JSON.
"""

PROMPT_GENERAL_EMPRENDEDORES = """
# ===== IDENTIDAD DEL AGENTE =====
Eres "IncubaBot", un acompañante integral para jóvenes emprendedores bolivianos.

# ===== TU MISIÓN =====
Ayudar al usuario con:
- Ideas de negocio y validación
- Finanzas básicas
- Marketing y ventas
- Organización y motivación

Responde de forma clara, breve y accionable.

PREGUNTA_LIBRE: {pregunta}
CONTEXTO: {contexto}
"""

@app.route('/consulta_general', methods=['POST'])
def consulta_general():
    try:
        if not request.is_json:
            return jsonify({"estado": "error", "mensaje": "El contenido debe ser JSON"}), 400

        datos = request.get_json() or {}
        pregunta = (datos.get("pregunta") or "").strip()
        contexto = (datos.get("contexto") or "").strip()

        if not pregunta:
            return jsonify({"estado": "error", "mensaje": "El campo 'pregunta' es obligatorio"}), 400

        # Crear prompt con los datos
        prompt = PROMPT_GENERAL_EMPRENDEDORES.format(
            pregunta=pregunta,
            contexto=contexto
        )

        # Llamar al agente IA
        respuesta = llamar_gpt(prompt)

        return jsonify({
            "estado": "success",
            "mensaje": "Consulta general procesada",
            "data": {"respuesta": respuesta}
        }), 200
        
    except Exception as e:
        return jsonify({"estado": "error", "mensaje": "Error interno", "detalle": str(e)}), 500

@app.route('/consulta_designacion', methods=['POST'])
def consulta_designacion():
    try:
        if not request.is_json:
            return jsonify({"estado": "error", "mensaje": "El contenido debe ser JSON"}), 400

        datos = request.get_json() or {}

        # Verificar campos requeridos
        campos_requeridos = [
            'nombre', 'edad', 'ciudad', 'educacion', 'descripcion_negocio', 
            'tiempo_funcionamiento', 'ingresos_mensuales', 'numero_clientes', 
            'productos_servicios', 'conocimiento_finanzas', 'conocimiento_marketing',
            'conocimiento_ventas', 'conocimiento_modelo_negocio', 'conocimiento_tecnologia',
            'resilencia', 'motivacion', 'gestion_estres', 'comunicacion', 'autoestima',
            'liderazgo', 'rubro', 'zona_operacion', 'apoyo_familiar', 'acceso_internet',
            'tiempo_disponible'
        ]
        
        for campo in campos_requeridos:
            if campo not in datos:
                return jsonify({
                    "estado": "error",
                    "mensaje": f"Falta el campo requerido: {campo}"
                }), 400

        # Formatear prompt
        prompt = PROMPT_ANALISIS_CLASIFICACION.format(**datos)
        
        # Llamar al agente IA
        salida = llamar_gpt(prompt)

        # Intentar parsear JSON
        try:
            json_salida = json.loads(salida)
        except:
            json_salida = {"raw": salida}

        return jsonify({
            "estado": "success",
            "mensaje": "Clasificación generada",
            "data": json_salida
        }), 200

    except Exception as e:
        return jsonify({
            "estado": "error",
            "mensaje": "Error interno en consulta_designacion",
            "detalle": str(e)
        }), 500

@app.route('/consulta_retos', methods=['POST'])
def consulta_retos():
    try:
        if not request.is_json:
            return jsonify({"estado": "error", "mensaje": "El contenido debe ser JSON"}), 400

        datos = request.get_json() or {}
        
        # Verificar campos básicos
        campos_basicos = ['nombre', 'ciudad', 'tipo_negocio', 'nivel', 'ingresos_actuales']
        for campo in campos_basicos:
            if campo not in datos:
                return jsonify({
                    "estado": "error",
                    "mensaje": f"Falta el campo requerido: {campo}"
                }), 400

        prompt = PROMPT_GENERADOR_RETOS.format(**datos)
        salida = llamar_gpt(prompt)

        try:
            json_salida = json.loads(salida)
        except:
            json_salida = {"raw": salida}

        return jsonify({
            "estado": "success",
            "mensaje": "Retos generados",
            "data": json_salida
        }), 200

    except Exception as e:
        return jsonify({
            "estado": "error",
            "mensaje": "Error interno en consulta_retos",
            "detalle": str(e)
        }), 500

@app.route('/estado', methods=['GET'])
def verificar_estado():
    try:
        estado = agenteIA.estado_sistema()
        return jsonify({
            "estado": "success",
            "mensaje": "Estado del sistema obtenido",
            "data": estado
        }), 200
    except Exception as e:
        return jsonify({
            "estado": "error",
            "mensaje": "Error obteniendo estado del sistema",
            "data": None,
            "error_details": str(e)
        }), 500

@app.route('/reinicializar', methods=['POST'])
def reinicializar_sistema():
    try:
        # CORRECCIÓN 3: Usar inicializar_sistema() en lugar de reinicializar()
        resultado = agenteIA.inicializar_sistema()
        
        if resultado:
            return jsonify({
                "estado": "success",
                "mensaje": "Sistema reinicializado correctamente",
                "data": None
            }), 200
        else:
            return jsonify({
                "estado": "error",
                "mensaje": "Error reinicializando el sistema",
                "data": None
            }), 500
    except Exception as e:
        return jsonify({
            "estado": "error",
            "mensaje": "Error interno al reinicializar",
            "data": None,
            "error_details": str(e)
        }), 500

@app.route('/salud', methods=['GET'])
def check_salud():
    return jsonify({
        "estado": "success",
        "mensaje": "Servicio funcionando correctamente",
        "data": {
            "servicio": "Agente IA Emprendedores Bolivia",
            "version": "1.0.0"
        }
    }), 200

@app.errorhandler(404)
def no_encontrado(error):
    return jsonify({
        "estado": "error",
        "mensaje": "Endpoint no encontrado",
        "data": None
    }), 404

@app.errorhandler(405)
def metodo_no_permitido(error):
    return jsonify({
        "estado": "error",
        "mensaje": "Método no permitido para este endpoint",
        "data": None
    }), 405

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask...")
    print("📍 Endpoints disponibles:")
    print("   POST /consulta_general - Consultas generales de emprendimiento")
    print("   POST /consulta_designacion - Análisis y clasificación de emprendedores")
    print("   POST /consulta_retos - Generador de retos personalizados")
    print("   GET  /estado - Verificar estado del sistema")
    print("   POST /reinicializar - Reinicializar sistema")
    print("   GET  /salud - Check de salud")
    
    app.run(debug=False, host='0.0.0.0', port=5000)