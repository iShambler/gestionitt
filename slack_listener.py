from slack_bolt import App
import os
from dotenv import load_dotenv
load_dotenv()

# Variables de entorno (no pongas el token directo en el código)
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

# Función para procesar los mensajes que tú le mandes
@app.message("")
def handle_message(message, say):
    user = message["user"]
    text = message["text"]

    # Aquí puedes filtrar para que solo tú interactúes con el bot
    if user != "TU_USER_ID":  # lo explico abajo
        return

    # Aquí llamas a tu asistente existente
    resultado = f"🧠 He recibido tu orden: {text}"
    say(f"<@{user}> {resultado}")

# Iniciar el servidor local
if __name__ == "__main__":
    app.start(port=3000)
