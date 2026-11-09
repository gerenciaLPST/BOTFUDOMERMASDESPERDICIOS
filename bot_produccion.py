import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("FUDO_USER")
PASSWORD = os.environ.get("FUDO_PASS")

# --------------------------------------------------------------------------
# ENLACE CSV DE TU HOJA TURNOACTUAL
URL_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSjaoq33UjW8sdggf2dovAqwLj4WhPh0zWfisibShqrccenyIL1ymcbDyLKNb6-KK0k5XE6T8H6QE0p/pub?gid=1962636174&single=true&output=csv"
# --------------------------------------------------------------------------

def obtener_datos():
    df = pd.read_csv(URL_GOOGLE_SHEETS)
    if 'tipo' in df.columns or 'Tipo' in df.columns:
        col = 'tipo' if 'tipo' in df.columns else 'Tipo'
        df = df[df[col].astype(str).str.upper().str.contains("PRODUC")]
    return df

def procesar_produccion(page, fila):
    producto = fila.get('Producto') or fila.get('producto')
    cantidad = fila.get('Cantidad') or fila.get('cantidad')
    comentario = fila.get('Comentario') or fila.get('comentario', '')

    print(f"\n[PRODUCCIÓN] Procesando: {producto} | Cantidad a sumar: +{cantidad}")

    page.get_by_role("link", name="Productos").click()
    time.sleep(1)
    page.get_by_role("link", name="Stock").click()
    time.sleep(1)
    page.get_by_role("link", name="Control de Stock").click()
    time.sleep(2)

    campo_busqueda = page.get_by_placeholder("Buscar")
    campo_busqueda.fill("")
    campo_busqueda.fill(str(producto))
    time.sleep(1)
    page.get_by_text(str(producto), exact=False).first.click()
    time.sleep(1)

    page.get_by_role("button", name="Editar Stock").click()
    time.sleep(1)

    campo_stock = page.locator("input[name='stock']").first
    stock_actual_str = campo_stock.input_value()
    try:
        stock_actual = float(stock_actual_str)
    except ValueError:
        stock_actual = 0.0

    nuevo_stock = stock_actual + float(cantidad)
    campo_stock.fill("")
    campo_stock.fill(str(nuevo_stock))
    time.sleep(1)

    if pd.notna(comentario) and str(comentario).strip() != "":
        campo_comentario = page.locator("textarea[name='comment'], input[name='comment']").first
        campo_comentario.fill(str(comentario))
        time.sleep(1)

    page.get_by_role("button", name="Guardar").click()
    time.sleep(1)
    page.get_by_role("button", name="Aceptar").click()
    time.sleep(2)
    print(f"¡Producción guardada para {producto}!")

def ejecutar_bot():
    try:
        df = obtener_datos()
        print(f"Registros de Producción encontrados: {len(df)}")
    except Exception as e:
        print(f"Error cargando hoja: {str(e)}")
        return

    if df.empty:
        print("No hay registros pendientes.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Iniciando sesión en Fudo...")
        page.goto("https://app.fudola.com/")
        page.get_by_placeholder("Email").fill(USERNAME)
        page.get_by_placeholder("Contraseña").fill(PASSWORD)
        page.get_by_role("button", name="Ingresar").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        for _, fila in df.iterrows():
            try:
                procesar_produccion(page, fila)
            except Exception as e:
                print(f"Error en {fila.get('Producto') or fila.get('producto')}: {str(e)}")

        browser.close()
        print("Finalizado Bot Producción.")

if __name__ == "__main__":
    ejecutar_bot()
