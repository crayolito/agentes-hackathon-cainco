import requests
import json
import pickle
import os
import io
from datetime import datetime
from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

class AgenteIA:
    def __init__(self, gestor_bd):
        # Configuración API OpenAI
        self.api_key = ""
        self.endpoint = 'https://api.openai.com/v1/chat/completions'
        
        # Clientes OpenAI
        self.cliente_openai = OpenAI(api_key=self.api_key)
        
        # Gestor de base de conocimiento
        self.gestor_bd = gestor_bd
        
        # Headers para requests
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # Variables para QA
        self.llm = None
        self.qa = None
        self.base_conocimiento = None
        
        # Template del prompt con contexto de conversación
        self.template_con_contexto = """

        """

        # Inicializar sistema
        self.inicializar_sistema()
    
    def inicializar_sistema(self):
        """Inicializa el sistema completo de QA"""
        try:
            print("⚡ Inicializando sistema de consultas legales...")
            
            # 1. Cargar base de conocimiento
            print("📚 Cargando base de conocimiento...")
            self.base_conocimiento = self.gestor_bd.obtener_base_conocimiento()
            
            if not self.base_conocimiento:
                print("❌ Error: No se pudo cargar la base de conocimiento")
                return False
            
            print("✅ Base de conocimiento cargada exitosamente")
            
            # 2. Configurar sistema QA
            print("🔧 Configurando sistema QA...")
            if self.configurar_qa():
                print("✅ Sistema QA configurado exitosamente")
                print("🚀 AgenteIARRapida LISTO PARA USAR")
                return True
            else:
                print("❌ Error configurando sistema QA")
                return False
                
        except Exception as e:
            print(f"❌ Error inicializando sistema: {e}")
            return False
    
    def configurar_qa(self):
        """Configura el sistema de preguntas y respuestas"""
        try:
            if self.base_conocimiento is None:
                print("❌ Base de conocimiento no disponible")
                return False
            
            # Configurar el modelo LLM
            self.llm = ChatOpenAI(
                openai_api_key=self.api_key,
                model_name="gpt-4o-mini",
                temperature=0.3,
                max_tokens=250,
                top_p=0.9,
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error configurando QA: {e}")
            return False
    
    def crear_qa_con_template(self, conversacion=""):
        """Crea una instancia de QA con un template específico"""
        try:
            # Construir el template sin f-strings para evitar conflictos
            template_con_contexto = """
                # ===== IDENTIDAD DEL AGENTE =====
                Eres "Amigo Legal", un agente especializado en leyes de tránsito bolivianas. Tu función es analizar consultas legales y proporcionar respuestas precisas basadas en tu base de conocimiento RAG.
                # ===== PERSONALIDAD Y COMPORTAMIENTO =====
                - 🗣️ CONVERSACIONAL: Hablas como un amigo cercano que domina leyes 
                - 📱 CHAT-OPTIMIZADO: Respuestas concisas para WhatsApp/Telegram (máximo 150 palabras)
                - 🛡️ PROTECTOR: Tu prioridad es defender los derechos del usuario aunque sea culpable o inocente
                - 📚 PRECISO: Solo usas información verificada del contexto RAG
                - ⚡ EFICIENTE: Detectas automáticamente el tipo de situación

                # ===== VARIABLES DE ENTRADA =====
                CONVERSACIÓN PREVIA: """ + conversacion + """
                INFORMACIÓN LEGAL DISPONIBLE: {context}
                CONSULTA ACTUAL: {question}

                # ===== PROTOCOLO DE ANÁLISIS AUTOMÁTICO =====
                ANTES de responder, analiza automáticamente basándote en la CONSULTA ACTUAL y CONVERSACIÓN PREVIA:
                1. ¿Es EMERGENCIA ACTIVA? (usuario con policía AHORA, palabras clave: "me paró", "están aquí", "ahora mismo", "urgente")
                2. ¿Es MULTA RECIBIDA? (ya tiene papeleta, palabras clave: "me multaron", "tengo multa", "cuánto pagar")
                3. ¿Es CONSULTA PREVENTIVA? (pregunta general, palabras clave: "puedo", "es legal", "qué pasa si")
                4. ¿Es SEGUIMIENTO? (continúa conversación anterior, CONVERSACIÓN PREVIA no vacía)

                # ===== FUENTES DE INFORMACIÓN =====
                - PRIMARIA: INFORMACIÓN LEGAL DISPONIBLE del contexto RAG
                - RESTRICCIÓN: Si contexto no tiene información específica, deriva a SEGIP (800-XX-XXXX)

                # ===== FORMATO DE RESPUESTA AUTOMÁTICA =====
                Analiza la situación según las variables de entrada y responde automáticamente con el formato correspondiente:
                
                ## 🚨 SI DETECTAS EMERGENCIA ACTIVA:
                **🚨 TU SITUACIÓN LEGAL**
                [Diagnóstico directo basado en INFORMACIÓN LEGAL DISPONIBLE: qué está pasando según la ley]
                
                **🛡️ TUS DERECHOS AHORA**
                • [Derecho principal - Art. X extraído del contexto]
                • [Lo que NO pueden hacer - Art. Z del contexto]
                • ⏰ [Tiempo límite que tienes según contexto]
                
                **💬 DI ESTO EXACTAMENTE**
                "[Frase textual específica para defenderte basada en INFORMACIÓN LEGAL DISPONIBLE]"
                
                **💰 MULTA/CONSECUENCIAS**
                • 💵 Monto: Bs. [cantidad exacta del contexto]
                • 🚗 ¿Retienen vehículo?: [SÍ/NO - cuándo según contexto]
                • 📅 Plazo: [días específicos del contexto]
                
                **⚠️ SI SE PONEN DIFÍCILES**
                📞 Denuncia: [número específico del contexto]
                📖 Ley aplicable: [cita exacta de INFORMACIÓN LEGAL DISPONIBLE]
                ---
                
                ## 💸 SI DETECTAS MULTA RECIBIDA:
                **📋 TU MULTA - QUÉ DICE LA LEY**
                [Base legal de la infracción según INFORMACIÓN LEGAL DISPONIBLE]
                
                **💰 DETALLES DE TU SANCIÓN**
                • 💵 Monto: Bs. [cantidad específica del contexto]
                • ⏰ Plazo para pagar: [días exactos del contexto]
                • 🏃‍♂️ Descuento pronto pago: [porcentaje si aparece en contexto]
                
                **🏢 DÓNDE PAGAR**
                [Lugares específicos según INFORMACIÓN LEGAL DISPONIBLE]
                
                **⚖️ PUEDES APELAR SI**
                [Condiciones específicas del contexto]
                
                **⚠️ CONSECUENCIAS SI NO PAGAS**
                [Recargos y procedimientos según contexto]
                📖 Base legal: [artículo específico de INFORMACIÓN LEGAL DISPONIBLE]
                ---
                
                ## ❓ SI DETECTAS CONSULTA PREVENTIVA:
                **📖 QUÉ DICE LA LEY**
                [Explicación directa según INFORMACIÓN LEGAL DISPONIBLE]
                
                **🛡️ TUS DERECHOS**
                • [Derecho 1 - Art. X del contexto]
                • [Derecho 2 - Art. Y del contexto]
                
                **📋 PROCEDIMIENTO CORRECTO**
                1️⃣ [Paso principal según contexto]
                2️⃣ [Dónde consultar/ir según contexto]
                
                **💸 MULTA SI LO HACES MAL**
                💵 Bs. [monto del contexto] - [artículo específico de INFORMACIÓN LEGAL DISPONIBLE]
                
                **💡 CONSEJO PRÁCTICO**
                [Tip útil basado en contexto]
                📚 Referencia legal: [ley específica de INFORMACIÓN LEGAL DISPONIBLE]
                ---
                
                ## 🔄 SI DETECTAS SEGUIMIENTO (CONVERSACIÓN PREVIA no vacía):
                **🔄 CONTINUANDO TU CONSULTA**
                [Respuesta específica basada en INFORMACIÓN LEGAL DISPONIBLE y CONVERSACIÓN PREVIA]
                
                **ℹ️ INFORMACIÓN ADICIONAL**
                [Datos relevantes del contexto relacionados con la CONVERSACIÓN PREVIA]
                
                **❓ ¿ALGO MÁS SOBRE ESTO?**
                [Pregunta para mantener conversación basada en el hilo previo]
                📖 Ref: [artículo aplicable de INFORMACIÓN LEGAL DISPONIBLE]
                
                # ===== RESTRICCIONES CRÍTICAS =====
                - MÁXIMO 150 palabras por respuesta
                - SOLO información de INFORMACIÓN LEGAL DISPONIBLE (contexto RAG proporcionado)
                - SIEMPRE cita fuente exacta del contexto: "Art. XXX", "Ley XXX", "D.S. XXX"
                - Montos SIEMPRE en "Bs." (bolivianos) como aparecen en el contexto
                - Si INFORMACIÓN LEGAL DISPONIBLE no tiene información específica: "Consulta en SEGIP: 800-XX-XXXX"
                - PROHIBIDO inventar leyes, artículos o montos no presentes en el contexto
                - Lenguaje coloquial boliviano pero profesional
                
                # ===== MANEJO DE ERRORES =====
                Si INFORMACIÓN LEGAL DISPONIBLE está vacía o no contiene información relevante para la CONSULTA ACTUAL:
                "🤷‍♂️ Hermano, esa consulta específica no la tengo en mi base legal actual. 📞 Te recomiendo consultar directamente en SEGIP (800-XX-XXXX) o la oficina de tránsito de tu municipio. ❓ ¿Puedo ayudarte con algo más general sobre tránsito?"
                
                # ===== INSTRUCCIÓN FINAL =====
                Detecta automáticamente el tipo de consulta basándote en:
                1. CONSULTA ACTUAL (palabras clave y contexto)
                2. CONVERSACIÓN PREVIA (si no está vacía, es seguimiento)
                3. INFORMACIÓN LEGAL DISPONIBLE (determina qué responder)
                Responde INMEDIATAMENTE con el formato correspondiente sin explicar por qué elegiste determinado formato.
            """

            prompt = PromptTemplate(
                template=template_con_contexto,
                input_variables=["context", "question"]
            )
            
            qa = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.base_conocimiento.as_retriever(
                    search_type="mmr",   
                    search_kwargs={
                        "k": 12,                    
                        "fetch_k": 20,              
                        "lambda_mult": 0.7,        
                        "score_threshold": 0.4      
                    }
                ),
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": prompt
                }
            )
            
            return qa
            
        except Exception as e:
            print(f"❌ Error creando QA: {e}")
            return None

    def procesar_consulta_con_contexto(self, pregunta, conversacion=""):
        """
        Procesa una consulta considerando el contexto de conversación previa
        
        Args:
            pregunta (str): La pregunta actual del usuario
            conversacion (str): El historial de conversación previa
            
        Returns:
            dict: Respuesta con estado, mensaje y data
        """
        try:
            # Verificar que el sistema esté listo
            if self.llm is None:
                print("⚠️ Sistema LLM no configurado, intentando reconfigurar...")
                if not self.configurar_qa():
                    return {
                        "estado": "error",
                        "mensaje": "No se pudo configurar el sistema LLM",
                        "data": None
                    }
            
            # Validar entrada
            if not pregunta or not pregunta.strip():
                return {
                    "estado": "error",
                    "mensaje": "La pregunta no puede estar vacía",
                    "data": None
                }
            
            print(f"🔍 Procesando consulta con contexto: {pregunta[:50]}...")
            
            # Decidir qué template usar
            usar_contexto = conversacion and conversacion.strip()
            # template = self.template_con_contexto if usar_contexto else self.template_simple
            template = self.template_con_contexto

            
            # Crear QA con el template apropiado
            qa = self.crear_qa_con_template(conversacion)
            
            if qa is None:
                return {
                    "estado": "error",
                    "mensaje": "Error configurando el sistema de consultas",
                    "data": None
                }
            
            # Construir consulta - conversación siempre opcional
            if conversacion and conversacion.strip():
                # CON contexto previo
                consulta_completa = f"CONVERSACIÓN PREVIA:\n{conversacion}\n\nCONSULTA ACTUAL:\n{pregunta}"
                print(f"📝 Procesando CON contexto previo")
            else:
                # SIN contexto previo
                consulta_completa = f"CONSULTA:\n{pregunta}"
                print(f"🆕 Procesando SIN contexto previo")

            # Ejecutar consulta (siempre igual)
            resultado = qa.invoke({"query": consulta_completa})
            
            respuesta = resultado.get('result', '')
            documentos = resultado.get('source_documents', [])
            
            print(f"✅ Consulta procesada - {len(documentos)} documentos encontrados")
            
            return {
                "estado": "success",
                "mensaje": "Consulta procesada correctamente",
                "data": respuesta,
            }
            
        except Exception as e:
            print(f"❌ Error procesando consulta: {e}")
            return {
                "estado": "error",
                "mensaje": "Error interno del servidor",
                "data": None,
                "error_details": str(e)
            }
    
    def consultar_con_contexto(self, pregunta, conversacion=""):
        """
        Método simplificado para consultas con contexto
        
        Args:
            pregunta (str): La pregunta del usuario
            conversacion (str): El historial de conversación
            
        Returns:
            str: Respuesta directa o mensaje de error
        """
        resultado = self.procesar_consulta_con_contexto(pregunta, conversacion)
        
        if resultado["estado"] == "success":
            return resultado["data"]
        else:
            return f"❌ Error: {resultado['mensaje']}"

    def estado_sistema(self):
        """
        Verifica el estado del sistema
        
        Returns:
            dict: Estado completo del sistema
        """
        estado_bd = self.gestor_bd.verificar_base_datos_lista()
        
        return {
            "base_datos": estado_bd,
            "base_conocimiento_cargada": self.base_conocimiento is not None,
            "llm_configurado": self.llm is not None,
            "sistema_listo": all([
                estado_bd["lista"],
                self.base_conocimiento is not None,
                self.llm is not None
            ])
        } 


