
def first_answer(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Пока не умею отвечать')
