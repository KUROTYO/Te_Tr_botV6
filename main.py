# Full working version of the Telegram Translation Bot
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from deep_translator import GoogleTranslator
from flask import Flask
from threading import Thread
from time import sleep

# Flask setup for Fly.io keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive!"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_web).start()

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variable Check
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "Traveler_01"
if not BOT_TOKEN:
    raise ValueError("Missing BOT_TOKEN environment variable.")

TRANSLATION_LANGUAGES = {
    'Arabic': 'ar', 'English': 'en', 'Afrikaans': 'af', 'Azerbaijani': 'az', 'Bulgarian': 'bg',
    'Chinese': 'zh-CN', 'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl', 'Finnish': 'fi',
    'French': 'fr', 'Georgian': 'ka', 'German': 'de', 'Greek': 'el', 'Gujarati': 'gu',
    'Hebrew': 'he', 'Hindi': 'hi', 'Hungarian': 'hu', 'Indonesian': 'id', 'Italian': 'it',
    'Japanese': 'ja', 'Korean': 'ko', 'Malay': 'ms', 'Nepali': 'ne', 'Norwegian': 'no',
    'Persian': 'fa', 'Polish': 'pl', 'Portuguese': 'pt', 'Punjabi': 'pa', 'Romanian': 'ro',
    'Russian': 'ru', 'Slovak': 'sk', 'Slovenian': 'sl', 'Spanish': 'es', 'Swahili': 'sw',
    'Swedish': 'sv', 'Tamil': 'ta', 'Telugu': 'te', 'Thai': 'th', 'Turkish': 'tr',
    'Ukrainian': 'uk', 'Urdu': 'ur', 'Vietnamese': 'vi'
}

user_text_to_translate = {}
user_interface_language = {}

PROMPTS = {
    'en': {
        "choose_interface_lang": "Please select the language you want me to speak:",
        "welcome": "Welcome {user_mention}! 🌍",
        "send_text_to_translate": "📝 Send a text to translate it!",
        "subscribe_prompt": "To use this bot, please subscribe to our channel first:\n@{channel_username}\n\nAfter subscribing, click 'Check Subscription' below.",
        "subscribe_button": "Subscribe to Channel",
        "check_subscription_button": "Check Subscription",
        "subscription_confirmed": "✅ Subscription confirmed! Now send the text you want to translate.",
        "not_subscribed": "❌ You're still not subscribed. Please subscribe and then click 'Check Subscription' again.",
        "please_subscribe": "Please subscribe to our channel @{channel_username} to use the bot. Click 'Check Subscription' after subscribing.",
        "choose_target_language": "Please choose the target language for your text:",
        "translate_to_arabic": "Translate to Arabic 🇸🇦",
        "translate_to_english": "Translate to English 🇬🇧",
        "more_languages": "More Languages 🌐",
        "back_button": "⬅️ Back",
        "no_text_found": "❗ No text found to translate. Please send a text message first.",
        "translation_error": "An error occurred during translation. Please try again or send a different text.",
        "send_another_text": "Send another text to translate again.",
        "help_message": "📝 Send any text. Then, choose a language to translate it into.",
        "original_text": "📝 Original:",
        "translated_text": "🌍 Translated ({language_name}):",
        "welcome_back_no_text": "Welcome back! Send a text to translate."
    },
    'ar': {
        "choose_interface_lang": "الرجاء اختيار اللغة التي تريدني أن أتحدث بها:",
        "welcome": "مرحبًا {user_mention}! 🌍",
        "send_text_to_translate": "📝 أرسل نصًا لترجمته!",
        "subscribe_prompt": "لاستخدام هذا البوت، يرجى الاشتراك في قناتنا أولاً:\n@{channel_username}\n\nبعد الاشتراك، انقر على 'التحقق من الاشتراك' أدناه.",
        "subscribe_button": "اشترك في القناة",
        "check_subscription_button": "التحقق من الاشتراك",
        "subscription_confirmed": "✅ تم تأكيد الاشتراك! الآن أرسل النص الذي تريد ترجمته.",
        "not_subscribed": "❌ أنت لم تشترك بعد. يرجى الاشتراك ثم النقر على 'التحقق من الاشتراك' مرة أخرى.",
        "please_subscribe": "يرجى الاشتراك في قناتنا @{channel_username} لاستخدام البوت. انقر على 'التحقق من الاشتراك' بعد الاشتراك.",
        "choose_target_language": "الرجاء اختيار اللغة المستهدفة لنصك:",
        "translate_to_arabic": "ترجمة إلى العربية 🇸🇦",
        "translate_to_english": "ترجمة إلى الإنجليزية 🇬🇧",
        "more_languages": "المزيد من اللغات 🌐",
        "back_button": "⬅️ رجوع",
        "no_text_found": "❗ لم يتم العثور على نص للترجمة. يرجى إرسال رسالة نصية أولاً.",
        "translation_error": "حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى أو إرسال نص مختلف.",
        "send_another_text": "أرسل نصًا آخر للترجمة مجددًا.",
        "help_message": "📝 أرسل أي نص. ثم اختر لغة لترجمته إليها.",
        "original_text": "📝 الأصلي:",
        "translated_text": "🌍 الترجمة ({language_name}):",
        "welcome_back_no_text": "مرحبًا بعودتك! أرسل نصًا للترجمة."
    }
}

def get_prompt(user_id, key):
    lang = user_interface_language.get(user_id, 'en')
    return PROMPTS[lang].get(key, PROMPTS['en'][key])

def create_interface_language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en")],
        [InlineKeyboardButton("العربية 🇸🇦", callback_data="set_lang_ar")]
    ])

def create_main_translation_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_prompt(user_id, "translate_to_arabic"), callback_data="translate_to_ar"),
            InlineKeyboardButton(get_prompt(user_id, "translate_to_english"), callback_data="translate_to_en")
        ],
        [InlineKeyboardButton(get_prompt(user_id, "more_languages"), callback_data="show_more_languages")]
    ])

def create_all_translation_languages_keyboard(user_id):
    keyboard = []
    filtered = {k: v for k, v in TRANSLATION_LANGUAGES.items() if k not in ['Arabic', 'English']}
    sorted_langs = sorted(filtered.items())
    for i in range(0, len(sorted_langs), 2):
        row = []
        for j in range(2):
            if i + j < len(sorted_langs):
                lang_name, code = sorted_langs[i + j]
                row.append(InlineKeyboardButton(lang_name, callback_data=f"translate_to_{code}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(get_prompt(user_id, "back_button"), callback_data="back_to_main_languages")])
    return InlineKeyboardMarkup(keyboard)

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_interface_language:
        await update.message.reply_text(
            PROMPTS['en']["choose_interface_lang"] + "\n\n" + PROMPTS['ar']["choose_interface_lang"],
            reply_markup=create_interface_language_keyboard()
        )
        return
    await proceed_after_lang_selection(update, context)

async def proceed_after_lang_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if not await check_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton(get_prompt(user_id, "subscribe_button"), url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton(get_prompt(user_id, "check_subscription_button"), callback_data="check_subscription")]
        ]
        await update.message.reply_text(
            f"{get_prompt(user_id, 'welcome').format(user_mention=user.mention_html())}\n\n{get_prompt(user_id, 'subscribe_prompt').format(channel_username=CHANNEL_USERNAME)}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    await update.message.reply_text(
        f"{get_prompt(user_id, 'welcome').format(user_mention=user.mention_html())}\n\n{get_prompt(user_id, 'send_text_to_translate')}",
        parse_mode='HTML',
    )

async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_interface_language:
        await update.message.reply_text(
            PROMPTS['en']["choose_interface_lang"] + "\n\n" + PROMPTS['ar']["choose_interface_lang"],
            reply_markup=create_interface_language_keyboard()
        )
        return
    await update.message.reply_text(
        get_prompt(user_id, "choose_target_language"),
        reply_markup=create_all_translation_languages_keyboard(user_id)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_interface_language:
        await update.message.reply_text(
            PROMPTS['en']["choose_interface_lang"] + "\n\n" + PROMPTS['ar']["choose_interface_lang"],
            reply_markup=create_interface_language_keyboard()
        )
        return
    await update.message.reply_text(get_prompt(user_id, "help_message"))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_interface_language:
        await update.message.reply_text(
            PROMPTS['en']["choose_interface_lang"] + "\n\n" + PROMPTS['ar']["choose_interface_lang"],
            reply_markup=create_interface_language_keyboard()
        )
        return

    if not await check_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton(get_prompt(user_id, "subscribe_button"), url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton(get_prompt(user_id, "check_subscription_button"), callback_data="check_subscription")]
        ]
        await update.message.reply_text(
            get_prompt(user_id, "please_subscribe").format(channel_username=CHANNEL_USERNAME),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    user_text_to_translate[user_id] = update.message.text
    await update.message.reply_text(
        get_prompt(user_id, "choose_target_language"),
        reply_markup=create_main_translation_keyboard(user_id)
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith("set_lang_"):
        lang_code = query.data.replace("set_lang_", "")
        user_interface_language[user_id] = lang_code
        await query.edit_message_text(
            get_prompt(user_id, "choose_interface_lang") + "\n\n" +
            ("✅ English selected." if lang_code == 'en' else "✅ تم اختيار العربية.")
        )
        await proceed_after_lang_selection(update, context)
        return

    if user_id not in user_interface_language:
        await query.edit_message_text(
            PROMPTS['en']["choose_interface_lang"] + "\n\n" + PROMPTS['ar']["choose_interface_lang"],
            reply_markup=create_interface_language_keyboard()
        )
        return

    if query.data == "check_subscription":
        if await check_subscription(user_id, context):
            await query.edit_message_text(get_prompt(user_id, "subscription_confirmed"))
        else:
            keyboard = [
                [InlineKeyboardButton(get_prompt(user_id, "subscribe_button"), url=f"https://t.me/{CHANNEL_USERNAME}")],
                [InlineKeyboardButton(get_prompt(user_id, "check_subscription_button"), callback_data="check_subscription")]
            ]
            await query.edit_message_text(get_prompt(user_id, "not_subscribed"), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif query.data == "show_more_languages":
        await query.edit_message_text(
            get_prompt(user_id, "choose_target_language"),
            reply_markup=create_all_translation_languages_keyboard(user_id)
        )
        return

    elif query.data == "back_to_main_languages":
        if user_id not in user_text_to_translate:
            await query.edit_message_text(get_prompt(user_id, "welcome_back_no_text"))
            return
        await query.edit_message_text(
            get_prompt(user_id, "choose_target_language"),
            reply_markup=create_main_translation_keyboard(user_id)
        )
        return

    elif query.data.startswith("translate_to_"):
        target_lang_code = query.data.replace("translate_to_", "")
        target_lang_name = next((name for name, code in TRANSLATION_LANGUAGES.items() if code == target_lang_code), "Unknown")
        if user_id not in user_text_to_translate:
            await query.edit_message_text(get_prompt(user_id, "no_text_found"))
            return

        original_text = user_text_to_translate[user_id]
        try:
            translator = GoogleTranslator(source='auto', target=target_lang_code)
            translated_text = translator.translate(original_text)
        except:
            sleep(1)
            try:
                translated_text = translator.translate(original_text)
            except:
                await query.edit_message_text(get_prompt(user_id, "translation_error"))
                return

        await query.edit_message_text(
            f"{get_prompt(user_id, 'original_text')} {original_text}\n"
            f"{get_prompt(user_id, 'translated_text').format(language_name=target_lang_name)} {translated_text}\n\n"
            f"{get_prompt(user_id, 'send_another_text')}"
        )
        del user_text_to_translate[user_id]

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Error processing update: %s", update, exc_info=context.error)
    if update and update.effective_message:
        user_id = update.effective_user.id if update.effective_user else None
        await update.effective_message.reply_text(
            get_prompt(user_id, "translation_error")
        )

def main():
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("languages", languages_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)
    logger.info("Bot is starting polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
