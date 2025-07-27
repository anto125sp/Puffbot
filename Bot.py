import os
import telebot
from telebot import types
from keep_alive import keep_alive  # Solo per Replit/Glitch

# Configurazione
TOKEN = os.getenv("TOKEN", "8216477597:AAEVRkRZA8tLJZxrRjgr6tF4FAFDtJYgJ7Y")  # Usa variabile d'ambiente per sicurezza
CANALE_ORDINI = os.getenv("CANALE_ORDINI", "@ordini_puff_privato")  # Canale privato per notifiche
PREZZO = "15€"
ADMIN_ID = "123456789"  # Sostituisci con il tuo ID Telegram

# Inizializzazione bot
bot = telebot.TeleBot(TOKEN)

# Database semplice (per demo, sostituisci con un DB vero in produzione)
ordini = {}

# Lista gusti con numerazione specifica
GUSTI = {
    "1": "Blue Razz",
    "3": "Blackberry Red Raspberry",
    "5": "Pink Lemonade",
    "9": "Cherry Coke",
    "10": "Double Apple"
}

# --------------------------
# FUNZIONALITÀ DEL BOT
# --------------------------

@bot.message_handler(commands=['start'])
def start(message):
    """Messaggio di benvenuto con tastiera principale"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍️ Ordina ora"),
        types.KeyboardButton("📞 Contatti"),
        types.KeyboardButton("ℹ️ Info")
    )
    
    # Invio immagine del prodotto (percorso assoluto o URL)
    try:
        with open("puff.jpg", "rb") as photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption=f"🌟 *Benvenuto nel Puff Store!* 🌟\n\n"
                       f"• Prezzo fisso: *{PREZZO}* per puff\n"
                       f"• Gusti disponibili:\n{_lista_gusti()}\n\n"
                       f"Premi *Ordina ora* per iniziare!",
                reply_markup=markup,
                parse_mode="Markdown"
            )
    except Exception as e:
        bot.reply_to(
            message,
            f"📦 *Ecco i nostri prodotti!*\n\n"
            f"Prezzo: *{PREZZO}*\n\n"
            f"Gusti:\n{_lista_gusti()}\n\n"
            f"Usa /ordina per iniziare.",
            parse_mode="Markdown"
        )

@bot.message_handler(func=lambda msg: msg.text == "🛍️ Ordina ora")
def avvia_ordine(message):
    """Mostra tastiera inline con i gusti"""
    markup = types.InlineKeyboardMarkup()
    for codice, gusto in GUSTI.items():
        markup.add(types.InlineKeyboardButton(gusto, callback_data=f"gusto_{codice}"))
    
    bot.send_message(
        message.chat.id,
        "👇 *Scegli il tuo gusto preferito:* 👇",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("gusto_"))
def gestisci_gusto(call):
    """Gestisce la selezione del gusto"""
    codice = call.data.split("_")[1]
    gusto = GUSTI[codice]
    
    # Salva temporaneamente l'ordine
    ordini[call.from_user.id] = {"gusto": gusto}
    
    # Richiede la quantità
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("1 Puff", callback_data=f"qta_1_{codice}"),
        types.InlineKeyboardButton("2 Puff (sconto 10%)", callback_data=f"qta_2_{codice}"),
        types.InlineKeyboardButton("5 Puff (sconto 20%)", callback_data=f"qta_5_{codice}")
    )
    
    bot.edit_message_text(
        f"🍬 *Gusto selezionato:* {gusto}\n\n"
        f"Ora scegli la quantità:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("qta_"))
def gestisci_quantita(call):
    """Gestisce la selezione della quantità"""
    _, qta, codice = call.data.split("_")
    gusto = GUSTI[codice]
    
    # Calcolo prezzo in base alla quantità
    if qta == "1":
        prezzo = PREZZO
    elif qta == "2":
        prezzo = f"27€ (invece di 30€)"
    else:
        prezzo = f"60€ (invece di 75€)"
    
    # Aggiorna ordine temporaneo
    ordini[call.from_user.id].update({
        "quantita": qta,
        "prezzo": prezzo
    })
    
    # Richiede l'Instagram tag
    bot.delete_message(call.message.chat.id, call.message.message_id)
    msg = bot.send_message(
        call.message.chat.id,
        f"📝 *Riepilogo ordine:*\n\n"
        f"• Gusto: *{gusto}*\n"
        f"• Quantità: *{qta}*\n"
        f"• Prezzo: *{prezzo}*\n\n"
        "Per confermare, invia il tuo *Instagram @tag* (es. @mionome):",
        parse_mode="Markdown"
    )
    
    bot.register_next_step_handler(msg, conferma_ordine, call.from_user.id)

def conferma_ordine(message, user_id):
    """Finalizza l'ordine"""
    if not message.text.startswith("@"):
        bot.send_message(message.chat.id, "❌ Formato non valido. Invia @username.")
        return
    
    instagram = message.text.strip()
    ordine = ordini.get(user_id, {})
    
    if not ordine:
        bot.send_message(message.chat.id, "❌ Ordine scaduto. Riprova.")
        return
    
    # Invia conferma all'utente
    bot.send_message(
        message.chat.id,
        f"🎉 *Ordine confermato!* 🎉\n\n"
        f"Ecco i dettagli:\n"
        f"• Gusto: *{ordine['gusto']}*\n"
        f"• Quantità: *{ordine['quantita']}*\n"
        f"• Prezzo: *{ordine['prezzo']}*\n"
        f"• Instagram: *{instagram}*\n\n"
        "Ti contatteremo entro 24h per la spedizione!",
        parse_mode="Markdown"
    )
    
    # Notifica al canale privato
    bot.send_message(
        CANALE_ORDINI,
        f"📦 *NUOVO ORDINE!* 📦\n\n"
        f"• Cliente: @{message.from_user.username}\n"
        f"• Instagram: {instagram}\n"
        f"• Gusto: {ordine['gusto']}\n"
        f"• Quantità: {ordine['quantita']}\n"
        f"• Prezzo: {ordine['prezzo']}\n\n"
        f"ID: `{user_id}`",
        parse_mode="Markdown"
    )
    
    # Notifica all'admin
    bot.send_message(
        ADMIN_ID,
        f"⚠️ Nuovo ordine da @{message.from_user.username}",
        parse_mode="Markdown"
    )
    
    # Pulisci l'ordine temporaneo
    if user_id in ordini:
        del ordini[user_id]

# --------------------------
# FUNZIONI AUSILIARIE
# --------------------------

def _lista_gusti():
    """Formatta la lista dei gusti per i messaggi"""
    return "\n".join([f"- {gusto}" for gusto in GUSTI.values()])

# --------------------------
# AVVIO DEL BOT
# --------------------------

if __name__ == "__main__":
    # Configurazione per hosting web (Render/Railway)
    if "RAILWAY_STATIC_URL" in os.environ or "RENDER" in os.environ:
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return "Bot online!"
        
        import threading
        threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 3000}).start()
    
    # Avvio il bot
    print("🤖 Bot avviato! Premi CTRL+C per fermarlo")
    bot.infinity_polling()
