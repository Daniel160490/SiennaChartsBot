from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import os
import asyncio

# Variables de entorno
TOKEN_TELEGRAM = os.getenv("BOT_TOKEN")  # Token del bot de Telegram
CHAT_ID = os.getenv("CHAT_ID")  # ID del grupo de Telegram
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")  # ID del usuario de Instagram
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")  # Token de acceso a la API de Instagram

# Diccionario para almacenar las últimas publicaciones enviadas
ultimos_posts = set()

# Función para dar la bienvenida a los nuevos usuarios
async def start(update: Update, context):
    await update.message.reply_text("¡Hola! Soy el bot de SiennaCharts.")

async def bienvenida(update: Update, context):
    for usuario in update.message.new_chat_members:
        await update.message.reply_text(
            f"🎉 ¡Bienvenido/a, {usuario.first_name}! 🎉\n"
            "Esperamos que disfrutes en este grupo. No dudes en presentarte para que te conozcamos todos. ☺️"
        )

# Función para obtener publicaciones de Instagram
async def obtener_posts_instagram():
    global ultimos_posts
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media?fields=id,caption,permalink&access_token={ACCESS_TOKEN}"
    url_stories = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/stories?fields=id,media_type,media_url,permalink&access_token={ACCESS_TOKEN}"

    
    try:
        nuevos_links = []
        
        # Obtener publicaciones normales
        response_media = requests.get(url_media).json()
        for post in response_media.get("data", []):
            post_id = post.get("id")
            link = post.get("permalink")
            media_url = post.get("media_url")
            media_type = post.get("media_type")  # IMAGE, VIDEO, CAROUSEL_ALBUM
            
            if post_id and post_id not in ultimos_posts:
                ultimos_posts.add(post_id)
                mensaje = f"📸 Nueva publicación en Instagram:\n{link}"
                if media_type == "IMAGE":
                    mensaje = f"🖼 Nueva foto en Instagram:\n{link}"
                elif media_type == "VIDEO":
                    mensaje = f"🎥 Nuevo video en Instagram:\n{link}"
                
                nuevos_links.append((mensaje, media_url))

        # Obtener historias
        response_stories = requests.get(url_stories).json()
        for story in response_stories.get("data", []):
            story_id = story.get("id")
            media_url = story.get("media_url")
            
            if story_id and story_id not in ultimos_posts:
                ultimos_posts.add(story_id)
                mensaje = "📖 ¡Nueva historia en Instagram!"
                nuevos_links.append((mensaje, media_url))

        return nuevos_links
    
    except Exception as e:
        print(f"Error obteniendo publicaciones o historias de Instagram: {e}")
        return []


# Función para enviar los enlaces al grupo de Telegram
async def enviar_posts_telegram(app):
    while True:
        nuevos_posts = await obtener_posts_instagram()
        
        for link in nuevos_posts:
            mensaje = f"📸 Nueva publicación en Instagram: {link}"
            url_telegram = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
            requests.post(url_telegram, data={"chat_id": CHAT_ID, "text": mensaje})

        await asyncio.sleep(1800)  # Revisa nuevas publicaciones cada 30 minutos

# Función principal del bot
def main():
    app = Application.builder().token(TOKEN_TELEGRAM).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))

    print("SiennaCharts funcionando ...")

    # Ejecuta la tarea de monitoreo de Instagram en segundo plano
    loop = asyncio.get_event_loop()
    loop.create_task(enviar_posts_telegram(app))

    app.run_polling()

if __name__ == "__main__":
    main()
