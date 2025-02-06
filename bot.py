from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os


TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context):
    await update.message.reply_text("¡Hola! Soy el bot de SiennaCharts.")

async def bienvenida(update: Update, context):
    for usuario in update.message.new_chat_members:
        await update.message.reply_text(f"🎉 ¡Bienvenido/a, {usuario.first_name}! 🎉\nEsperamos que disfrutes en este grupo. No dudes en presentarte para que te conozcamos todos. ☺️")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))
    print("SiennaCharts funcionando ...")
    app.run_polling()

if __name__ == "__main__":
    main()
