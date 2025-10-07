from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options  # ✅ Import necesario
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv
import time, json, os

# --- CARGAR VARIABLES DEL .env ---
load_dotenv()  # Carga OPENAI_API_KEY, INTRA_USER, INTRA_PASS, etc.
# -------------------

# --- CONFIGURAR ---
LOGIN_URL = os.getenv("URL_PRIVADA")
USERNAME = os.getenv("INTRA_USER")
PASSWORD = os.getenv("INTRA_PASS")
USERNAME_SELECTOR = '#usuario'
PASSWORD_SELECTOR = '#password'
SUBMIT_SELECTOR = '#btAceptar'
CALENDAR_BUTTON_SELECTOR = '.ui-datepicker-trigger'
VOLVER_SELECTOR = '#btVolver'
BUSCADOR_INPUT_SELECTOR = '#textoBusqueda'
BUSCADOR_BOTON_SELECTOR = '#buscar'
# -------------------

# Crear cliente OpenAI con la clave del .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------------------
# 🚀 CREAR DRIVER HEADLESS (nuevo para Render o servidores sin GUI)
# ---------------------------------------------------------------------
def crear_driver_headless():
    """Crea un navegador Chrome en modo headless, ideal para Render o ejecución sin interfaz."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")            # Ejecutar sin ventana
    chrome_options.add_argument("--no-sandbox")              # Requerido por Render
    chrome_options.add_argument("--disable-dev-shm-usage")   # Evita errores de memoria compartida
    chrome_options.add_argument("--disable-gpu")             # Acelera en entornos sin GPU
    chrome_options.add_argument("--window-size=1920,1080")   # Fija tamaño de pantalla virtual
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


# ---------------------------------------------------------------------
# FUNCIONES BASE
# ---------------------------------------------------------------------
def save_cookies(driver, path="cookies.json"):
    with open(path, "w") as f:
        json.dump(driver.get_cookies(), f)

def lunes_de_semana(fecha):
    return fecha - timedelta(days=fecha.weekday())

def hacer_login(driver, wait):
    """Realiza el login en la intranet."""
    driver.get(LOGIN_URL)
    usr = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, USERNAME_SELECTOR)))
    usr.clear()
    usr.send_keys(USERNAME)
    pwd = driver.find_element(By.CSS_SELECTOR, PASSWORD_SELECTOR)
    pwd.clear()
    pwd.send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, SUBMIT_SELECTOR).click()
    time.sleep(3)
    print("✅ Login completado.")

def volver_inicio(driver):
    """Pulsa el botón 'Volver' para regresar a la pantalla principal tras login."""
    try:
        btn_volver = driver.find_element(By.CSS_SELECTOR, VOLVER_SELECTOR)
        btn_volver.click()
        time.sleep(2)
        print("↩️ Volviendo a la pantalla principal...")
    except Exception as e:
        print(f"⚠️ No se pudo pulsar el botón Volver: {e}")

def seleccionar_fecha(driver, fecha_obj):
    """Abre el calendario, navega hasta el mes correcto y selecciona el día correspondiente."""
    wait = WebDriverWait(driver, 15)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, CALENDAR_BUTTON_SELECTOR))).click()
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui-datepicker-calendar")))

    titulo_selector = ".ui-datepicker-title"
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }


    def obtener_mes_anio_actual():
        """Obtiene el mes y año visibles actualmente en el calendario."""
        try:
            titulo = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, titulo_selector)))
            texto = titulo.text.lower().strip()
            partes = texto.split()

            # Asegura que hay al menos dos partes (mes y año)
            if len(partes) < 2:
                raise ValueError(f"Formato inesperado del título del calendario: {texto}")

            mes_visible = meses.get(partes[0], 1)
            anio_visible = int(partes[1])

            return mes_visible, anio_visible
        except Exception as e:
            print(f"⚠️ Error obteniendo mes/año actual: {e}")
            return fecha_obj.month, fecha_obj.year

    # 📆 Obtener mes/año actual
    mes_visible, anio_visible = obtener_mes_anio_actual()

    # 🔁 Navegar hasta el mes/año correcto
    while (anio_visible, mes_visible) < (fecha_obj.year, fecha_obj.month):
        try:
            btn_next = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ui-datepicker-next")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_next)
            btn_next.click()
            time.sleep(0.4)
            mes_visible, anio_visible = obtener_mes_anio_actual()
        except Exception:
            break

    while (anio_visible, mes_visible) > (fecha_obj.year, fecha_obj.month):
        try:
            btn_prev = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ui-datepicker-prev")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_prev)
            btn_prev.click()
            time.sleep(0.4)
            mes_visible, anio_visible = obtener_mes_anio_actual()
        except Exception:
            break

    # 📅 Seleccionar el día
    dia_seleccionado = fecha_obj.day
    print(f"📅 Seleccionando {dia_seleccionado}/{fecha_obj.month}/{fecha_obj.year}")

    try:
        dia_xpath = f"//a[normalize-space(text())='{dia_seleccionado}']"
        elemento_dia = wait.until(EC.element_to_be_clickable((By.XPATH, dia_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_dia)
        elemento_dia.click()
        print(f"✅ Fecha seleccionada correctamente: {fecha_obj.strftime('%d/%m/%Y')}")
    except Exception as e:
        print(f"⚠️ No se pudo seleccionar el día {dia_seleccionado}: {e}")



# ---------------------------------------------------------------------
# NUEVA FUNCIÓN: SELECCIONAR PROYECTO
# ---------------------------------------------------------------------
def seleccionar_proyecto(driver, wait, nombre_proyecto):
    """
    Selecciona el proyecto en la tabla de imputación.
    Si ya existe una línea con ese proyecto, la reutiliza.
    Si no existe, crea una nueva línea, abre el buscador,
    busca el proyecto y lo selecciona.
    """

    def linea_proyecto_existente(nombre_proyecto):
        """Comprueba si ya existe una línea con ese proyecto en la tabla."""
        try:
            filas = driver.find_elements(By.CSS_SELECTOR, "tr[id^='listaEmpleadoHoras']")
            for fila in filas:
                texto = fila.text.lower()
                if nombre_proyecto.lower() in texto:
                    print(f"🧩 Proyecto '{nombre_proyecto}' ya existe, reutilizando línea existente.")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fila)
                    try:
                        fila.click()
                    except Exception:
                        pass
                    time.sleep(0.3)
                    return True
            return False
        except Exception as e:
            print(f"⚠️ Error buscando línea existente: {e}")
            return False

    try:
        # Si el proyecto ya existe, no añadimos una nueva línea
        if linea_proyecto_existente(nombre_proyecto):
            return

        # 1️⃣ Pulsar en "Añadir Línea"
        print("🆕 Añadiendo nueva línea de imputación...")
        btn_nueva_linea = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#btNuevaLinea")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_nueva_linea)
        btn_nueva_linea.click()
        time.sleep(1)

        # 2️⃣ Pulsar en el botón "»" para abrir el buscador
        print("🔍 Abriendo buscador de proyectos...")
        btn_cambiar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#btCambiarSubproyecto")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_cambiar)
        btn_cambiar.click()
        time.sleep(0.8)

        # 3️⃣ Esperar a que aparezca el campo de búsqueda
        print("⌛ Esperando campo de búsqueda...")
        campo_buscar = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#textoBusqueda")))
        campo_buscar.clear()
        campo_buscar.send_keys(nombre_proyecto)

        # 4️⃣ Pulsar en el botón "Buscar"
        print(f"🔎 Buscando proyecto: {nombre_proyecto}")
        btn_buscar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#buscar")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_buscar)
        btn_buscar.click()
        time.sleep(1.2)

        # 5️⃣ Asegurar que el árbol se expanda completamente
        print("🌳 Expandiendo árbol de resultados...")
        driver.execute_script("""
            const tree = document.querySelector('#treeTipologia');
            if (tree && typeof $(tree).jstree === 'function') {
                $(tree).jstree('open_all');
            }
        """)

        time.sleep(1)

        # 6️⃣ Buscar y seleccionar el proyecto
        print("📂 Buscando y seleccionando el proyecto en el árbol...")
        xpath = (
            f"//li[@rel='subproyectos']//a[contains(translate(normalize-space(.), "
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜ', 'abcdefghijklmnopqrstuvwxyzáéíóúü'), "
            f"'{nombre_proyecto.lower()}')]"
        )

        elemento = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
        elemento.click()
        print(f"✅ Proyecto '{nombre_proyecto}' seleccionado correctamente.")
        time.sleep(1.5)

    except Exception as e:
        print(f"⚠️ No se pudo seleccionar el proyecto '{nombre_proyecto}': {e}")


def imputar_horas_semana(driver, wait):
    """
    Imputa las horas de lunes a viernes en la línea actual.
    h1 = lunes ... h5 = viernes
    Lunes a jueves -> 8.5 horas
    Viernes -> 6.5 horas
    Si un campo no está disponible (festivo, deshabilitado, etc.), lo omite.
    """
    print("🕒 Imputando horas de lunes a viernes...")

    horas_semana = {
        "h1": "8.5",  # Lunes
        "h2": "8.5",  # Martes
        "h3": "8.5",  # Miércoles
        "h4": "8.5",  # Jueves
        "h5": "6.5",  # Viernes
    }

    for dia, valor in horas_semana.items():
        try:
            input_selector = f"input[id^='listaEmpleadoHoras'][id$='.{dia}']"
            campo = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, input_selector)))

            # 🔍 Asegurar que el campo esté visible (headless no lo muestra por defecto)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
            time.sleep(0.1)

            if campo.is_enabled():
                campo.clear()
                campo.send_keys(valor)
                print(f"✅ Día {dia.upper()} → {valor} horas")
                time.sleep(0.3)
            else:
                print(f"⚠️ Día {dia.upper()} no editable (festivo o bloqueo)")

        except Exception as e:
            print(f"⚠️ Día {dia.upper()} no disponible (omitido): {e}")

    print("✅ Imputación semanal completada.")


def imputar_horas_dia(driver, wait, dia, horas):
    """
    Imputa una cantidad específica de horas en un día concreto (lunes a viernes)
    dentro de la línea actual de imputación. Si ya hay horas, las suma.
    """
    mapa_dias = {
        "lunes": "h1",
        "martes": "h2",
        "miércoles": "h3",
        "miercoles": "h3",
        "jueves": "h4",
        "viernes": "h5"
    }

    dia_clave = mapa_dias.get(dia.lower())
    if not dia_clave:
        print(f"⚠️ Día no reconocido: {dia}")
        return

    try:
        input_selector = f"input[id^='listaEmpleadoHoras'][id$='.{dia_clave}']"
        campo = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, input_selector)))

        # 🔍 Scroll para asegurar visibilidad en headless
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
        time.sleep(0.1)

        if campo.is_enabled():
            valor_actual = campo.get_attribute("value") or "0"
            try:
                valor_actual = float(valor_actual.replace(",", "."))
            except ValueError:
                valor_actual = 0.0

            nuevas_horas = float(horas)
            total = round(valor_actual + nuevas_horas, 2)

            campo.clear()
            campo.send_keys(str(total))

            print(f"✅ {dia.capitalize()} → {nuevas_horas} horas añadidas (total {total}).")
        else:
            print(f"⚠️ El campo de {dia} no está habilitado.")
    except Exception as e:
        print(f"⚠️ No se pudo imputar horas en {dia}: {e}")


def guardar_linea(driver, wait):
    """Pulsa el botón 'Guardar' tras imputar horas."""
    try:
        btn_guardar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#btGuardarLinea")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_guardar)
        time.sleep(0.1)
        btn_guardar.click()
        time.sleep(1.5)
        print("💾 Línea guardada correctamente.")
    except Exception as e:
        print(f"⚠️ No se pudo pulsar el botón Guardar: {e}")


def emitir_linea(driver, wait):
    """Pulsa el botón 'Emitir' tras imputar horas."""
    try:
        btn_emitir = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#btEmitir")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_emitir)
        time.sleep(0.1)
        btn_emitir.click()
        time.sleep(1.5)
        print("📤 Línea emitida correctamente.")
    except Exception as e:
        print(f"⚠️ No se pudo pulsar el botón Emitir: {e}")


def iniciar_jornada(driver, wait):
    """
    Pulsa el botón 'Inicio jornada' si está disponible.
    Si el botón no está o ya se ha pulsado, lo ignora.
    """
    print("🕒 Intentando iniciar jornada...")

    try:
        btn_inicio = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#botonInicioJornada")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_inicio)
        time.sleep(0.1)

        if btn_inicio.is_enabled():
            btn_inicio.click()
            time.sleep(2)
            print("✅ Jornada iniciada correctamente.")
        else:
            print("⚠️ El botón de inicio de jornada no está habilitado (posible jornada ya iniciada).")

    except Exception as e:
        print(f"⚠️ No se pudo iniciar la jornada: {e}")


def finalizar_jornada(driver, wait):
    """
    Pulsa el botón 'Finalizar jornada' si está disponible.
    Si el botón no está o ya se ha pulsado, lo ignora.
    """
    print("🕓 Intentando finalizar jornada...")

    try:
        btn_fin = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#botonFinJornada")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_fin)
        time.sleep(0.1)

        if btn_fin.is_enabled():
            btn_fin.click()
            time.sleep(2)
            print("✅ Jornada finalizada correctamente.")
        else:
            print("⚠️ El botón de finalizar jornada no está habilitado (posible jornada ya cerrada).")

    except Exception as e:
        print(f"⚠️ No se pudo finalizar la jornada: {e}")



# ---------------------------------------------------------------------
# INTERPRETACIÓN REAL CON GPT (versión robusta para Render)
# ---------------------------------------------------------------------
def interpretar_con_gpt(texto):
    """
    Traduce la frase del usuario en una lista de comandos JSON para automatizar
    la imputación de horas en la intranet.

    Acciones posibles:
    - seleccionar_fecha (requiere 'fecha' en formato YYYY-MM-DD)
    - volver
    - seleccionar_proyecto (requiere 'nombre')
    - imputar_horas_dia (requiere 'dia' y 'horas')
    - imputar_horas_semana
    - iniciar_jornada
    - finalizar_jornada

    Reglas:
    1. Siempre asume que el año es 2025.
    2. Si el usuario dice "esta semana", "la próxima", etc., genera el lunes de esa semana en 2025.
    3. Si mezcla acciones ("imputa horas en el proyecto X la semana del 7 de octubre"),
       el orden debe ser: fecha → proyecto → imputación → guardar/emitir → volver.
    4. Devuelve SOLO JSON válido.
    5. Si no se puede interpretar algo, se ignora.
    """

    prompt = f"""
Eres un asistente que traduce frases en una lista de comandos JSON para automatizar
una web de imputación de horas.

Acciones válidas:
- seleccionar_fecha (requiere "fecha" en formato YYYY-MM-DD)
- volver
- seleccionar_proyecto (requiere "nombre")
- imputar_horas_dia (requiere "dia" y "horas")
- imputar_horas_semana
- iniciar_jornada
- finalizar_jornada

Reglas:
1️⃣ Siempre usa el año 2025 aunque el usuario no lo diga.
2️⃣ Si el usuario menciona varios proyectos y horas en la misma frase (por ejemplo
   "3.5 en Desarrollo y 2 en Dirección el lunes"), genera varias acciones en orden:
   seleccionar_proyecto → imputar_horas_dia → seleccionar_proyecto → imputar_horas_dia.
3️⃣ Si el usuario menciona palabras como "expide", "emite", "envía", "envíalo", "expídelo" o similares,
   añade una acción {{ "accion": "emitir_linea" }} al final de la secuencia.
4️⃣ Si no menciona ninguna de esas palabras, añade {{ "accion": "guardar_linea" }} después de imputar horas.
5️⃣ Si el usuario dice "esta semana", "la próxima semana", etc., genera el lunes correspondiente en 2025.
6️⃣ Solo incluye {{ "accion": "iniciar_jornada" }} si el usuario dice explícitamente
   "inicia jornada", "empieza jornada", "comienza el día", etc.
7️⃣ Devuelve SOLO JSON válido, sin texto ni comentarios.
8️⃣ Orden de las acciones:
   seleccionar_fecha → seleccionar_proyecto → imputar_horas_dia → imputar_horas_semana → guardar/emitir → volver

Ejemplo de salida correcta:
[
  {{ "accion": "iniciar_jornada" }},
  {{ "accion": "seleccionar_fecha", "parametros": {{ "fecha": "2025-10-06" }} }},
  {{ "accion": "seleccionar_proyecto", "parametros": {{ "nombre": "Desarrollo" }} }},
  {{ "accion": "imputar_horas_semana" }}
]

Frase del usuario: "{texto}"
"""

    try:
        # 🔁 Solicitud al modelo
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un traductor de lenguaje natural a comandos JSON válidos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content.strip()
        print("🧠 [DEBUG GPT] Respuesta cruda:", raw)

        # 🧩 Limpieza preventiva de texto extraño
        raw = raw.strip("` \n\t")
        if raw.startswith("json"):
            raw = raw[4:].strip()

        # A veces el modelo devuelve texto rodeado de ```json ... ```
        if raw.startswith("```"):
            raw = raw.strip("```").replace("json", "").strip()

        # Intentar parsear JSON
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            print("⚠️ Error al decodificar JSON:", e)
            print("🔍 Contenido problemático:", raw)
            return []

        # Aceptar tanto lista como dict
        if isinstance(data, dict):
            data = [data]

        # 🔧 Reordenar acciones en orden lógico
        orden_correcto = [
            "iniciar_jornada",
            "seleccionar_fecha",
            "seleccionar_proyecto",
            "imputar_horas_dia",
            "imputar_horas_semana",
            "guardar_linea",
            "emitir_linea",
            "finalizar_jornada",
            "volver"
        ]
        data = sorted(
            data,
            key=lambda x: orden_correcto.index(x["accion"])
            if x.get("accion") in orden_correcto else 99
        )

        print("✅ [DEBUG GPT] Interpretación final:", data)
        return data

    except Exception as e:
        print("❌ Error interpretando respuesta del modelo:", e)
        return []



# ---------------------------------------------------------------------
# EJECUTAR ACCIÓN (versión robusta para Render / headless)
# ---------------------------------------------------------------------
def ejecutar_accion(driver, wait, orden):
    """Ejecuta una acción interpretada del GPT con control de errores y logs claros."""
    accion = orden.get("accion")

    if not accion:
        print(f"⚠️ Orden inválida o sin campo 'accion': {orden}")
        return

    print(f"🚀 Ejecutando acción → {accion}")

    try:
        # 🕒 Iniciar jornada
        if accion == "iniciar_jornada":
            iniciar_jornada(driver, wait)

        # 🕓 Finalizar jornada
        elif accion == "finalizar_jornada":
            finalizar_jornada(driver, wait)

        # 🧮 Imputar horas de un día
        elif accion == "imputar_horas_dia":
            dia_param = orden.get("parametros", {}).get("dia")
            horas = float(orden.get("parametros", {}).get("horas", 0))
            if not dia_param:
                print("⚠️ No se especificó el día en imputar_horas_dia.")
                return

            # Convertir fecha completa a nombre de día si aplica
            try:
                fecha_obj = datetime.fromisoformat(dia_param)
                dia = fecha_obj.strftime("%A").lower()
                dias_map = {
                    "monday": "lunes",
                    "tuesday": "martes",
                    "wednesday": "miércoles",
                    "thursday": "jueves",
                    "friday": "viernes",
                }
                dia = dias_map.get(dia, dia)
            except Exception:
                dia = dia_param.lower()

            imputar_horas_dia(driver, wait, dia, horas)

        # 📅 Seleccionar fecha
        elif accion == "seleccionar_fecha":
            fecha_str = orden.get("parametros", {}).get("fecha")
            if not fecha_str:
                print("⚠️ No se especificó fecha en seleccionar_fecha.")
                return

            try:
                fecha = datetime.fromisoformat(fecha_str)
                seleccionar_fecha(driver, fecha)
            except Exception as e:
                print(f"❌ No se pudo procesar la fecha '{fecha_str}': {e}")

        # ↩️ Volver
        elif accion == "volver":
            volver_inicio(driver)

        # 📂 Seleccionar proyecto
        elif accion == "seleccionar_proyecto":
            nombre = orden.get("parametros", {}).get("nombre")
            if not nombre:
                print("⚠️ No se especificó el nombre del proyecto.")
                return
            seleccionar_proyecto(driver, wait, nombre)

        # ⏱️ Imputar horas semanales
        elif accion == "imputar_horas_semana":
            imputar_horas_semana(driver, wait)

        # 💾 Guardar línea
        elif accion == "guardar_linea":
            guardar_linea(driver, wait)

        # 📤 Emitir línea
        elif accion == "emitir_linea":
            emitir_linea(driver, wait)

        else:
            print(f"🤔 Acción desconocida o no implementada: {accion}")

    except Exception as e:
        print(f"❌ Error ejecutando '{accion}': {e}")


# ---------------------------------------------------------------------
# MAIN LOOP (adaptado para Render/headless)
# ---------------------------------------------------------------------
def main():
    """Inicializa el navegador (headless en Render), hace login y ejecuta comandos."""
    print("🚀 Iniciando asistente de imputación de horas con GPT + Selenium...")

    try:
        driver = crear_driver_headless()  # ✅ usa la función headless definida antes
        wait = WebDriverWait(driver, 15)

        # 🚀 Login automático
        hacer_login(driver, wait)

        print("\n🧠 Asistente con IA (OpenAI) para imputación de horas")
        print("Ya estás logueado en el sistema.")
        print("Puedes decir cosas como:")
        print(" - 'selecciona la semana del 7 de octubre'")
        print(" - 'abre el proyecto Estudio/Investigación de tecnología'")
        print(" - 'vuelve a la pantalla principal'")
        print("Escribe 'salir' para terminar.\n")

        while True:
            try:
                texto = input("🗣️  > ")
            except EOFError:
                # Render o ejecución sin stdin
                print("ℹ️ Entorno sin entrada interactiva. Finalizando.")
                break

            if texto.lower() in ["salir", "exit", "quit"]:
                break

            # 🧠 Interpretar instrucción con GPT
            ordenes = interpretar_con_gpt(texto)
            print("🧾 Interpretación:", ordenes)

            # 🔄 Ordenar: siempre primero la fecha
            ordenes = sorted(ordenes, key=lambda o: 0 if o.get("accion") == "seleccionar_fecha" else 1)

            # Ejecutar cada acción interpretada
            for orden in ordenes:
                ejecutar_accion(driver, wait, orden)

    except Exception as e:
        print(f"💥 Error crítico en main(): {e}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass
        print("🔚 Navegador cerrado correctamente.")
        
if __name__ == "__main__":
    main()