from slack_bolt import App
import os
import re
from dotenv import load_dotenv
from login_imputaciones import interpretar_con_gpt, ejecutar_accion, crear_driver_headless
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

driver = crear_driver_headless()
wait = WebDriverWait(driver, 15)

@app.message(re.compile(".*"))
def handle_message(message, say):
    user = message["user"]
    text = message["text"]

    if user != os.getenv("SLACK_ALLOWED_USER_ID"):
        say(f"🚫 No estás autorizado para usar este bot, <@{user}>.")
        return

    ordenes = interpretar_con_gpt(text)
    say(f"🧠 Interpretación: {ordenes}")

    for orden in ordenes:
        ejecutar_accion(driver, wait, orden)

    say(f"✅ Tarea completada, <@{user}>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.start(port=port)
