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
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media?fields=id,caption,permalink,media_type&access_token={ACCESS_TOKEN}"
    url_stories = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/stories?fields=id,media_type,media_url,permalink&access_token={ACCESS_TOKEN}"

    try:
        nuevos_links = []
        
        # Obtener publicaciones normales
        response_media = requests.get(url).json()
        for post in response_media.get("data", []):
            post_id = post.get("id")
            permalink = post.get("permalink")
            media_type = post.get("media_type")
            
            if post_id and post_id not in ultimos_posts:
                ultimos_posts.add(post_id)
                
                # Obtener la URL real del contenido
                media_response = requests.get(f"https://graph.facebook.com/v19.0/{post_id}?fields=media_url&access_token={ACCESS_TOKEN}").json()
                media_url = media_response.get("media_url", "")
                
                mensaje = f"📸 Nueva publicación en Instagram:\n{permalink}"
                if media_type == "IMAGE":
                    mensaje = f"🖼 Nueva foto en Instagram:\n{permalink}"
                elif media_type == "VIDEO":
                    mensaje = f"🎥 Nuevo video en Instagram:\n{permalink}"
                
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
async def enviar_posts_telegram():
    while True:
        nuevos_posts = await obtener_posts_instagram()
        
        for mensaje, media_url in nuevos_posts:
            url_texto = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
            url_imagen = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto"

            if media_url:
                requests.post(url_imagen, data={"chat_id": CHAT_ID, "photo": media_url, "caption": mensaje})
            else:
                requests.post(url_texto, data={"chat_id": CHAT_ID, "text": mensaje})

        await asyncio.sleep(1800)  # Revisa nuevas publicaciones cada 30 minutos

# Función principal del bot
async def main():
    app = Application.builder().token(TOKEN_TELEGRAM).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))

    print("SiennaCharts funcionando ...")

    # Ejecutar `enviar_posts_telegram` en paralelo sin interferir con `run_polling`
    asyncio.create_task(enviar_posts_telegram())

    # Iniciar el bot en modo polling
    await app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
