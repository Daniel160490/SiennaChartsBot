from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import os
import asyncio

# Variables de entorno
TOKEN_TELEGRAM = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")  # Asegúrate de que este es el ID de Instagram Business
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

ultimos_posts = set()  # Almacena los últimos posts para evitar duplicados

async def start(update: Update, context):
    print("Comando /start ejecutado")
    await update.message.reply_text("¡Hola! Soy el bot de SiennaCharts.")

async def bienvenida(update: Update, context):
    for usuario in update.message.new_chat_members:
        print(f"Nuevo usuario detectado: {usuario.first_name}")
        await update.message.reply_text(
            f"🎉 ¡Bienvenido/a, {usuario.first_name}! 🎉\n"
            "Esperamos que disfrutes en este grupo."
        )

async def obtener_posts_instagram():
    global ultimos_posts
    print("Obteniendo publicaciones de Instagram...")

    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media?fields=id,caption,media_type,permalink&access_token={ACCESS_TOKEN}"

    try:
        response_media = requests.get(url)
        print(f"Respuesta de Instagram (código {response_media.status_code}): {response_media.text}")

        if response_media.status_code != 200:
            return []

        data = response_media.json()
        nuevos_links = []

        for post in data.get("data", []):
            post_id = post.get("id")
            permalink = post.get("permalink")

            if post_id and post_id not in ultimos_posts:
                ultimos_posts.add(post_id)

                media_response = requests.get(
                    f"https://graph.facebook.com/v19.0/{post_id}?fields=media_url&access_token={ACCESS_TOKEN}"
                ).json()

                media_url = media_response.get("media_url", "")

                mensaje = f"📸 Nueva publicación en Instagram:\n{permalink}"
                nuevos_links.append((mensaje, media_url))

        print(f"Se encontraron {len(nuevos_links)} nuevas publicaciones.")
        return nuevos_links

    except Exception as e:
        print(f"⚠️ Error obteniendo publicaciones: {e}")
        return []

async def enviar_posts_telegram():
    print("⏳ Iniciando el proceso de envío de publicaciones a Telegram...")
    
    while True:
        nuevos_posts = await obtener_posts_instagram()

        for mensaje, media_url in nuevos_posts:
            print(f"📤 Enviando post a Telegram: {mensaje}")

            url_imagen = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto"
            response = requests.post(url_imagen, data={"chat_id": CHAT_ID, "photo": media_url, "caption": mensaje})
            
            print(f"📨 Respuesta de Telegram: {response.status_code} - {response.text}")

        print("🔁 Esperando 60 segundos antes de la próxima verificación...")
        await asyncio.sleep(60)

async def detener_instancia_anterior():
    try:
        await app.stop()
    except:
        pass

def main():
    print("🚀 Iniciando bot SiennaCharts...")

    global app
    app = Application.builder().token(TOKEN_TELEGRAM).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))

    print("✅ Bot iniciado correctamente.")

    # Iniciar la verificación de publicaciones en un loop asíncrono
    asyncio.run(iniciar_procesos())

def iniciar_bot():
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

async def iniciar_procesos():
    await detener_instancia_anterior()  # Asegura que no haya otra instancia corriendo
    asyncio.create_task(enviar_posts_telegram())  # Comienza a verificar publicaciones de IG en segundo plano
    iniciar_bot()  # Inicia el bot en modo polling

if __name__ == "__main__":
    main()
