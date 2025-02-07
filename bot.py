from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import os
import asyncio

# Variables de entorno
TOKEN_TELEGRAM = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

ultimos_posts = set()  # Almacena los últimos posts para evitar duplicados

async def start(update: Update, context):
    await update.message.reply_text("¡Hola! Soy el bot de SiennaCharts.")

async def bienvenida(update: Update, context):
    for usuario in update.message.new_chat_members:
        await update.message.reply_text(
            f"🎉 ¡Bienvenido/a, {usuario.first_name}! 🎉\n"
            "Esperamos que disfrutes en este grupo."
        )

async def obtener_posts_instagram():
    global ultimos_posts
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media?fields=id,caption,permalink,media_type&access_token={ACCESS_TOKEN}"

    try:
        nuevos_links = []
        response_media = requests.get(url).json()
        print("Respuesta de Instagram:", response_media)
        for post in response_media.get("data", []):
            post_id = post.get("id")
            permalink = post.get("permalink")
            media_type = post.get("media_type")

            if post_id and post_id not in ultimos_posts:
                ultimos_posts.add(post_id)
                media_response = requests.get(
                    f"https://graph.facebook.com/v19.0/{post_id}?fields=media_url&access_token={ACCESS_TOKEN}"
                ).json()
                media_url = media_response.get("media_url", "")
                
                mensaje = f"📸 Nueva publicación en Instagram:\n{permalink}"
                nuevos_links.append((mensaje, media_url))

        return nuevos_links
    except Exception as e:
        print(f"Error obteniendo publicaciones: {e}")
        return []

async def enviar_posts_telegram():
    while True:
        nuevos_posts = await obtener_posts_instagram()
        for mensaje, media_url in nuevos_posts:
            url_imagen = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto"
            requests.post(url_imagen, data={"chat_id": CHAT_ID, "photo": media_url, "caption": mensaje})
        await asyncio.sleep(300)  # 🔹 Cambiado a 5 minutos (300 segundos)

async def iniciar_verificacion(app):
    await enviar_posts_telegram(app)

def main():
    app = Application.builder().token(TOKEN_TELEGRAM).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))

    print("SiennaCharts funcionando ...")

    # Inicia la verificación dentro del loop de la aplicación
    app.job_queue.run_repeating(lambda _: asyncio.create_task(enviar_posts_telegram(app)), interval=1800)

    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    # Ejecutar todo directamente sin usar `asyncio.run()` ni `get_event_loop()`
    print("Iniciando el bot...")
    asyncio.run(main())  # Usamos `asyncio.run()` aquí, que es la forma recomendada con Python 3.7+
