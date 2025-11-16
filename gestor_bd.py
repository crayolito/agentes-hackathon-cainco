import os
import json
import pickle
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.chains import RetrievalQA
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
import re
import requests

class GestorBaseDatos:
    def __init__(self):
        # Configuración PostgreSQL
        self.configuracion_bd = {
            'dbname': 'BDHACKATHON', 
            'user': 'postgres',           
            'password': 'clave123',    
            'host': 'localhost',
            'port': '5432'
        }
        
        # Rutas de archivos - CORRECCIÓN: documento_leyes debe ser un archivo, no una carpeta
        self.BASE_DIR = Path(__file__).resolve().parent
        self.documento_leyes = self.BASE_DIR / 'base_conocimiento_childfund.txt'
        
        # Clave API para OpenAI embeddings - CORRECCIÓN: Usar variable de entorno o configuración
        self.CLAVE_API = os.getenv('OPENAI_API_KEY', '')

        # Auto-inicialización de BD
        self._inicializar_bd()
    
    def obtener_conexion_BaseDatos(self):
        """Establece una conexión a la base de datos PostgreSQL."""
        try:
            conn = psycopg2.connect(**self.configuracion_bd)
            return conn
        except Exception as e:
            print(f"❌ Error al conectar a PostgreSQL: {e}")
            return None
    
    def _inicializar_bd(self):
        """Inicialización automática de la base de datos"""
        print("🚀 Inicializando base de datos PostgreSQL...")
        
        # Verificar conexión
        conn = self.obtener_conexion_BaseDatos()
        if not conn:
            print("❌ Sin conexión a PostgreSQL")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Crear tabla para fragmentos de texto si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fragmentos_leyes_bolivianas (
                    id SERIAL PRIMARY KEY,
                    contenido TEXT NOT NULL,
                    embedding BYTEA,
                    metadata JSONB,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Crear índice para mejor rendimiento
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fragmentos_leyes_bolivianas_fecha 
                ON fragmentos_leyes_bolivianas(fecha_creacion);
            """)
            
            conn.commit()
            print("✅ Base de datos inicializada correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error al inicializar la base de datos: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def verificar_base_datos_lista(self):
        """
        Verifica si la base de datos tiene contenido y está lista para usar
        
        Returns:
            dict: Estado de la base de datos con detalles
        """
        try:
            conn = self.obtener_conexion_BaseDatos()
            if not conn:
                return {"lista": False, "mensaje": "Sin conexión a BD"}
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fragmentos_leyes_bolivianas")
            count_fragmentos = cursor.fetchone()[0]
            
            # Verificar última actualización
            cursor.execute("SELECT MAX(fecha_creacion) FROM fragmentos_leyes_bolivianas")
            ultima_actualizacion = cursor.fetchone()[0]
            
            conn.close()
            
            estado = {
                "lista": count_fragmentos > 0,
                "fragmentos_total": count_fragmentos,
                "ultima_actualizacion": ultima_actualizacion,
                "mensaje": f"Base de datos {'lista' if count_fragmentos > 0 else 'vacía'} con {count_fragmentos} fragmentos"
            }
            
            print(f"📊 Estado BD: {estado['mensaje']}")
            return estado
            
        except Exception as e:
            print(f"❌ Error al verificar estado de la base de datos: {e}")
            return {
                "lista": False,
                "fragmentos_total": 0,
                "ultima_actualizacion": None,
                "mensaje": f"Error al verificar base de datos: {str(e)}"
            }
    
    def cargar_fragmentos_desde_bd(self):
        """
        Carga todos los fragmentos desde PostgreSQL y reconstruye FAISS
        
        Returns:
            FAISS vectorstore o None si hay error
        """
        try:
            conn = self.obtener_conexion_BaseDatos()
            if not conn:
                return None
                    
            cursor = conn.cursor()
            cursor.execute("SELECT id, contenido, embedding, metadata FROM fragmentos_leyes_bolivianas ORDER BY id")
            resultados = cursor.fetchall()
            conn.close()
            
            if not resultados:
                print("⚠️ No se encontraron fragmentos en PostgreSQL")
                return None
            
            # Preparar datos para FAISS
            texts = []
            embeddings_list = []
            metadatas = []
            
            for id_frag, contenido, embedding_bytes, metadata_json in resultados:
                # Deserializar el embedding
                if embedding_bytes:
                    try:
                        embedding = pickle.loads(embedding_bytes)
                        embeddings_list.append(embedding)
                        texts.append(contenido)
                        
                        # Procesar metadata
                        metadata = {}
                        if metadata_json:
                            try:
                                if isinstance(metadata_json, str):
                                    metadata = json.loads(metadata_json)
                                elif isinstance(metadata_json, dict):
                                    metadata = metadata_json
                                else:
                                    metadata = json.loads(str(metadata_json))
                            except Exception as e:
                                print(f"⚠️ Error al procesar metadata para fragmento {id_frag}: {e}")
                        
                        metadatas.append(metadata)
                        
                    except Exception as e:
                        print(f"⚠️ Error al deserializar embedding para fragmento {id_frag}: {e}")
            
            if not texts or not embeddings_list:
                print("❌ No se pudieron cargar embeddings válidos")
                return None
            
            # Crear objeto de embeddings de OpenAI
            vectores = OpenAIEmbeddings(
                api_key=self.CLAVE_API,
                model="text-embedding-ada-002"
            )
            
            # Crear la base de conocimiento utilizando from_embeddings
            base_conocimiento = FAISS.from_embeddings(
                text_embeddings=list(zip(texts, embeddings_list)),
                embedding=vectores,
                metadatas=metadatas if metadatas else None
            )
            
            print(f"📚 Base de conocimiento reconstruida exitosamente desde PostgreSQL con {len(texts)} fragmentos")
            return base_conocimiento
                    
        except Exception as e:
            print(f"❌ ERROR al cargar fragmentos desde PostgreSQL: {e}")
            return None
    
    def procesar_y_guardar_documentos(self):
        """
        Procesa el archivo base_conocimiento_childfund.txt y guarda los fragmentos en PostgreSQL
        
        Returns:
            bool: True si se procesó correctamente, False en caso contrario
        """
        try:
            print("🔄 Procesando documentos para crear fragmentos...")
            
            # CORRECCIÓN: Verificar que existe el archivo directamente
            if not self.documento_leyes.exists():
                print(f"❌ No se encontró el archivo: {self.documento_leyes}")
                print("⚠️ Por favor, añade el archivo 'base_conocimiento_childfund.txt' en el directorio del proyecto.")
                return False
            
            # Cargar el archivo
            textos = []
            try:
                with open(self.documento_leyes, 'r', encoding='utf-8') as archivo:
                    contenido = archivo.read()
                    textos.append(
                        Document(
                            page_content=contenido,
                            metadata={"source": "base_conocimiento_childfund.txt"}
                        )
                    )
                print(f"📖 Archivo base_conocimiento_childfund.txt cargado exitosamente")
            except Exception as e:
                print(f"❌ Error al cargar el archivo base_conocimiento_childfund.txt: {e}")
                return False
            
            if len(textos) == 0:
                print("❌ No se pudo cargar el archivo base_conocimiento_childfund.txt correctamente.")
                return False
            
            # Configurar el divisor de texto
            divisor_texto = RecursiveCharacterTextSplitter(
                chunk_size=1500,          # tamaño de fragmento (caracteres)
                chunk_overlap=300,        # solapamiento entre fragmentos
                separators=[
                    "\n\n",              # separación fuerte por párrafos
                    "\n",                # saltos de línea
                    ". ",                # fin de oración
                    "? ",
                    "! ",
                    "; ",
                    ", "
                ],
                length_function=len,
                is_separator_regex=False  # usamos separadores simples, no regex
            )
            
            # Dividir en fragmentos
            fragmentos = divisor_texto.split_documents(textos)
            print(f"📄 Se han creado {len(fragmentos)} fragmentos de texto")
            
            # Crear embeddings
            vectores = OpenAIEmbeddings(
                api_key=self.CLAVE_API,
                model="text-embedding-ada-002"
            )
            
            # Guardar fragmentos en PostgreSQL
            conn = self.obtener_conexion_BaseDatos()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Limpiar tabla existente
            cursor.execute("TRUNCATE TABLE fragmentos_leyes_bolivianas RESTART IDENTITY")
            print("🔄 Tabla fragmentos_leyes_bolivianas limpiada, insertando nuevos fragmentos...")
            
            # Preparar datos para inserción masiva
            datos = []
            for fragmento in fragmentos:
                # Generar embedding para el fragmento
                embedding = vectores.embed_query(fragmento.page_content)
                embedding_bytes = pickle.dumps(embedding)
                
                datos.append((
                    fragmento.page_content,
                    psycopg2.Binary(embedding_bytes),
                    json.dumps(fragmento.metadata)
                ))
            
            print(f"💾 Insertando {len(datos)} fragmentos en PostgreSQL...")
            
            # Insertar todos los fragmentos
            execute_values(
                cursor,
                "INSERT INTO fragmentos_leyes_bolivianas (contenido, embedding, metadata) VALUES %s",
                datos,
                template="(%s, %s, %s)"
            )
            
            # Verificar que se guardaron correctamente
            cursor.execute("SELECT COUNT(*) FROM fragmentos_leyes_bolivianas")
            count = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            print(f"✅ {count} fragmentos guardados exitosamente en PostgreSQL")
            return True
            
        except Exception as e:
            print(f"❌ Error al procesar y guardar documentos: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return False
    
    def obtener_base_conocimiento(self):
        """
        Obtiene la base de conocimiento FAISS, cargándola desde BD o procesando documentos si es necesario
        
        Returns:
            FAISS vectorstore o None si hay error
        """
        # Verificar estado de la base de datos
        estado = self.verificar_base_datos_lista()
        
        if estado["lista"]:
            # Si hay fragmentos en BD, cargarlos
            print("📚 Cargando base de conocimiento desde PostgreSQL...")
            return self.cargar_fragmentos_desde_bd()
        else:
            # Si no hay fragmentos, procesarlos desde archivo
            print("📄 Base de datos vacía, procesando documentos...")
            if self.procesar_y_guardar_documentos():
                # Después de procesar, cargar la base de conocimiento
                return self.cargar_fragmentos_desde_bd()
            else:
                print("❌ No se pudieron procesar los documentos")
                return None
    
    def limpiar_base_datos(self):
        """
        Limpia la tabla de fragmentos
        
        Returns:
            bool: True si se limpió correctamente
        """
        try:
            conn = self.obtener_conexion_BaseDatos()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("TRUNCATE TABLE fragmentos_leyes_bolivianas RESTART IDENTITY CASCADE")
            conn.commit()
            conn.close()
            
            print("🧹 Base de datos limpiada exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error al limpiar la base de datos: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return False

# CORRECCIÓN: Cambiar nombre de clase de ejemplo
if __name__ == "__main__":
    # Crear instancia del gestor de BD
    gestor_bd = GestorBaseDatos()
    
    # Verificar estado
    estado = gestor_bd.verificar_base_datos_lista()
    print("Estado de la BD:", estado)
    
    # Obtener base de conocimiento (carga desde BD o procesa documentos automáticamente)
    base_conocimiento = gestor_bd.obtener_base_conocimiento()
    
    if base_conocimiento:
        print("✅ Base de conocimiento lista para usar")
        print(f"Tipo: {type(base_conocimiento)}")
    else:
        print("❌ No se pudo obtener la base de conocimiento")