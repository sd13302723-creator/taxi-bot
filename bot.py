import os
import time
import threading
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "9070365602:AAH8GeJL0Y7AfVph_EADfVtPxR2iMwMxAr8"
ADMIN_ID = "8635660651"

bot = telebot.TeleBot(TOKEN)
user_states = {}

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running 24/7!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "🚖 **Игорь | Комфорт-авто**\n"
        "Комфортные пассажирские поездки по маршруту **Кара-Балта ⇄ Бишкек**.\n\n"
        "👨‍✈️ **Водитель:** Игорь\n"
        "• **Стаж вождения:** 15 лет\n"
        "• Аккуратное вождение и знание трассы\n"
        "• Чистый и комфортный салон\n"
        "• Честные фиксированные цены\n"
        "• Помощь с багажом\n\n"
        "📞 **Телефон / WhatsApp:** `+996505910613`\n\n"
        "👇 **Выберите направление:**"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📍 Кара-Балта ➔ Бишкек", callback_data="dir_kb_bish"))
    markup.add(InlineKeyboardButton("📍 Бишкек ➔ Кара-Балта", callback_data="dir_bish_kb"))
    markup.add(InlineKeyboardButton("💬 Написать в WhatsApp", url="https://wa.me/996505910613"))
    markup.add(InlineKeyboardButton("✍️ Свой вопрос", callback_data="dir_other"))
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dir_"))
def callback_direction(call):
    direction_map = {
        "dir_kb_bish": "Кара-Балта ➔ Бишкек",
        "dir_bish_kb": "Бишкек ➔ Кара-Балта",
        "dir_other": "Свой вопрос / Другой маршрут"
    }
    chosen_dir = direction_map.get(call.data, "Не указано")
    user_states[call.from_user.id] = chosen_dir
    
    instruction = (
        f"Вы выбрали направление: *{chosen_dir}*\n\n"
        "✍️ **Отправьте детали поездки одним сообщением:**\n"
        "• Дата и точное время\n"
        "• Откуда забрать и куда везти\n"
        "• Сколько человек / есть ли багаж\n\n"
        "🎙 *Или запишите голосовое сообщение.*\n\n"
        "⚠️ Данные передаются водителю исключительно для организации поездки."
    )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, instruction, parse_mode="Markdown")

@bot.message_handler(content_types=['text', 'voice'])
def handle_order(message):
    user = message.from_user
    user_id = user.id
    chosen_dir = user_states.get(user_id, "Не выбрано")
    username = f"@{user.username}" if user.username else user.first_name
    
    content_desc = "🎙 [Голосовое сообщение]" if message.content_type == 'voice' else message.text

    order_text = (
        f"🚖 **Новый заказ такси!**\n\n"
        f"📍 **Маршрут:** {chosen_dir}\n"
        f"👤 **Пассажир:** {username} (ID: `{user_id}`)\n"
        f"📝 **Детали:** {content_desc}"
    )

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Принять", callback_data=f"accept_{user_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")
    )

    if ADMIN_ID:
        try:
            bot.send_message(ADMIN_ID, order_text, parse_mode="Markdown", reply_markup=markup)
            if message.content_type == 'voice':
                bot.send_voice(ADMIN_ID, message.voice.file_id)
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")

    bot.reply_to(
        message,
        "✅ **Ваша заявка принята!**\n\n"
        "Игорь свяжется с вами для подтверждения поездки.\n"
        "Срочно? Звоните: `+996505910613`",
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def admin_response(call):
    parts = call.data.split("_")
    action = parts[0]
    target_user_id = int(parts[1])
    bot.answer_callback_query(call.id)

    if action == "accept":
        bot.send_message(target_user_id, "✅ **Ваш заказ принят!** Водитель подтвердил поездку.", parse_mode="Markdown")
        bot.edit_message_text(call.message.text + "\n\n🟢 **СТАТУС:** Заказ принят.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        bot.send_message(target_user_id, "❌ К сожалению, машина на это время занята. Свяжитесь по телефону: +996505910613", parse_mode="Markdown")
        bot.edit_message_text(call.message.text + "\n\n🔴 **СТАТУС:** Отклонено.", chat_id=call.message.chat.id, message_id=call.message.message_id)

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка связи: {e}")
            time.sleep(5)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
