import re
from typing import Dict, List


class NormalizadorOracion:
    """
    Clase para normalizar oraciones reemplazando modismos bolivianos por términos estándar.
    """
    
    def __init__(self):
        """
        Inicializa el normalizador con el diccionario de modismos bolivianos.
        """
            
 # Diccionario de modismos bolivianos orientados a emprendimiento
        self.modismos = {
            # Términos para dinero
            "lucas": "dinero",
            "platita": "dinero",
            "guita": "dinero",
            "billete": "dinero",
            "pisto": "dinero",
            "fierros": "dinero",
            "capitalito": "capital",
            "capital semilla": "capital inicial",
            "fondito": "fondo",
            "ahorritos": "ahorros",

            # Términos para ventas y clientes
            "caserito": "cliente frecuente",
            "caserita": "cliente frecuente",
            "caseritos": "clientes frecuentes",
            "hacer caserito": "fidelizar cliente",
            "parar la olla": "generar ingresos",
            "hacer platita": "generar ingresos",
            "mover merca": "vender productos",
            "mover producto": "vender productos",
            "sacar la mercadería": "vender inventario",
            "rematar": "vender con descuento",
            "ofertita": "oferta",
            "rebajita": "descuento",
            "fiado": "venta a crédito",
            "fiar": "vender a crédito",
            "fiadito": "venta a crédito",
            "a plazos": "pago en cuotas",
            "cuotitas": "cuotas",
            "al toque": "rápido",
            "rapidito": "rápido",
            "de pasadita": "compra rápida",
            "lleve caserito": "oferta al cliente",

            # Términos para negocio/emprendimiento
            "changuita": "trabajo pequeño",
            "chamba": "trabajo",
            "negocito": "negocio pequeño",
            "emprendimientito": "emprendimiento pequeño",
            "hacerla": "tener éxito",
            "salir adelante": "progresar",
            "pararse solito": "ser sostenible",
            "poner algo": "iniciar negocio",
            "abrir un puestito": "abrir negocio pequeño",
            "tener su tiendita": "tener negocio pequeño",
            "informalito": "negocio informal",
            "negocio formalito": "negocio formal",
            "meterle ganas": "esforzarse",
            "meterle duro": "trabajar intensamente",
            "empujar el carro": "sacar el negocio adelante",
            "hacer crecer": "escalar negocio",
            "no da": "no es rentable",
            "no está rindiendo": "no es rentable",
            "recién está arrancando": "fase inicial",
            "recién estamos empezando": "fase inicial",
            "marcha blanca": "periodo de prueba",

            # Términos para productos y servicios
            "cositas": "productos",
            "mercadería": "productos",
            "mercancía": "productos",
            "agüita": "bebida",
            "salchipapas": "comida rápida",
            "comidita": "alimento",
            "cosméticos": "productos de belleza",
            "ropa americana": "ropa usada importada",
            "ropa usada": "ropa de segunda mano",
            "servicitos": "servicios",
            "chamberos": "servicios varios",
            "delivery": "entrega a domicilio",
            "reparto": "entrega a domicilio",

            # Términos para marketing y redes
            "subir al face": "publicar en facebook",
            "subir al insta": "publicar en instagram",
            "hacer flyer": "hacer afiche digital",
            "hacer videíto": "hacer video corto",
            "hacer historia": "publicar historia en redes",
            "viralito": "contenido viral",
            "harto alcance": "alto alcance",
            "poquito alcance": "bajo alcance",
            "promito": "promoción",
            "promo": "promoción",
            "publicidadita": "publicidad",
            "hacer ruido": "generar atención",

            # Términos para costos y contabilidad
            "gastos fijos": "costos fijos",
            "gastos variables": "costos variables",
            "ganancita": "ganancia",
            "ganancia limpia": "ganancia neta",
            "ganancia bruta": "ganancia bruta",
            "saldo": "dinero disponible",
            "estar en rojo": "tener pérdidas",
            "estar tablas": "punto de equilibrio",
            "salir hecho": "no ganar ni perder",
            "perder platita": "tener pérdidas",

            # Términos para trámites y Estado
            "papeleo": "trámites",
            "trámite": "gestión administrativa",
            "hacer papeles": "hacer trámites",
            "sacar NIT": "obtener NIT",
            "jurídica": "persona jurídica",
            "unipersonal": "empresa unipersonal",
            "licencia de funcionamiento": "permiso municipal",
            "permiso municipal": "licencia de funcionamiento",
            "impuestos": "impuestos nacionales",
            "la alcaldía": "gobierno municipal",
            "la gobernación": "gobierno departamental",
            "aduana": "aduana nacional",
            "regularizar": "formalizar negocio",

            # Términos de riesgo y problemas
            "no se mueve": "no hay ventas",
            "está muerto": "sin ventas",
            "está flojo": "pocas ventas",
            "está parado": "actividad baja",
            "bajón": "baja de ventas",
            "bajita la venta": "pocas ventas",
            "me estoy ahogando": "problemas financieros",
            "estoy colgado": "endeudado",
            "debo en el banco": "tengo deuda bancaria",
            "me está pisando el banco": "presión de deuda",
            "no llega la plata": "falta de pago",

            # Términos para apoyo y redes
            "socito": "socio",
            "socita": "socia",
            "mi socio": "socio",
            "mi socia": "socia",
            "aliadito": "aliado",
            "apoyito": "apoyo",
            "mentorcito": "mentor",
            "capacitacióncita": "capacitación",
            "tallercito": "taller",
            "feria de emprendimiento": "feria empresarial",
            "feria productiva": "feria de productos",

            # Términos para tiempo y organización
            "al día": "actualizado",
            "al hilo": "ordenado",
            "desordenadito": "desordenado",
            "a última hora": "improvisado",
            "sobre la hora": "al límite de tiempo",
            "de a poco": "gradualmente",
            "pasito a pasito": "progresivamente",
        }
        
    def normalizar_oracion(self, texto: str) -> str:
            """
            Normaliza una oración reemplazando modismos bolivianos por términos estándar.
            
            Args:
                texto (str): La oración a normalizar
                
            Returns:
                str: La oración normalizada
            """
            # Convertir a minúsculas para hacer la búsqueda insensible a mayúsculas
            texto_normalizado = texto.lower()
            
            # Ordenar las frases por longitud (más largas primero) para evitar reemplazos parciales
            frases_ordenadas = sorted(self.modismos.keys(), key=len, reverse=True)
            
            # Reemplazar cada modismo encontrado
            for modismo in frases_ordenadas:
                # Usar regex con word boundaries para evitar reemplazos parciales
                patron = r'\b' + re.escape(modismo) + r'\b'
                texto_normalizado = re.sub(patron, self.modismos[modismo], texto_normalizado)
            
            return texto_normalizado

    def normalizar_con_detalles(self, texto: str) -> Dict[str, str]:
        """
        Normaliza una oración y devuelve tanto el texto original como el normalizado
        junto con los reemplazos realizados.
        
        Args:
            texto (str): La oración a normalizar
            
        Returns:
            Dict[str, str]: Diccionario con texto original, normalizado y reemplazos
        """
        texto_original = texto
        texto_normalizado = self.normalizar_oracion(texto)
        
        # Encontrar los reemplazos realizados
        reemplazos = []
        if texto_original.lower() != texto_normalizado:
            reemplazos.append("Se realizaron normalizaciones")
        
        return {
            "original": texto_original,
            "normalizado": texto_normalizado,
            "hay_cambios": texto_original.lower() != texto_normalizado
        }

    def ejemplos_de_uso(self):
        """
        Método con ejemplos de uso del normalizador
        """
        oraciones_ejemplo = [
            "El verde me paro en la tranca porque iba muy rapido",
            "Me chaparon sin papeles y me pidieron coima",
            "El paco me levanto multa porque no traje el carton",
            "Choque mi trufi contra un micro en el semaforo",
            "Me agarraron chupado manejando la moto"
        ]
        
        print("=== EJEMPLOS DE NORMALIZACIÓN ===\n")
        
        for i, oracion in enumerate(oraciones_ejemplo, 1):
            resultado = self.normalizar_con_detalles(oracion)
            print(f"Ejemplo {i}:")
            print(f"Original:    {resultado['original']}")
            print(f"Normalizado: {resultado['normalizado']}")
            print(f"Cambios:     {'Sí' if resultado['hay_cambios'] else 'No'}")
            print("-" * 50)

if __name__ == "__main__":
    # Crear una instancia del normalizador
    normalizador = NormalizadorOracion()
    
    # Ejecutar ejemplos
    normalizador.ejemplos_de_uso()
    
    # Ejemplo de uso interactivo
    print("\n=== PRUEBA TU PROPIA ORACIÓN ===")
    print("Ejemplo: normalizador.normalizar_oracion('El verde me paro porque iba rapido')")
    
    # Ejemplo de uso directo
    ejemplo_texto = "El verde me paro porque iba rapido"
    resultado = normalizador.normalizar_oracion(ejemplo_texto)
    print(f"\nEjemplo directo:")
    print(f"Original: {ejemplo_texto}")
    print(f"Normalizado: {resultado}")