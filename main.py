from time import sleep
import telebot
from telebot import types
import TOKEN
import functions
import texts
import database

bot = telebot.TeleBot(TOKEN.token)
item = types.InlineKeyboardButton(text="Убрать", callback_data="Убрать")
delete_markup = types.InlineKeyboardMarkup().add(item)
description_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text="Да", callback_data="Да")) \
    .add(types.InlineKeyboardButton(text="Нет", callback_data="Нет"))
delete_and_input_markup = types.InlineKeyboardMarkup().add(item, types.InlineKeyboardButton(
    text=texts.markup_add_another, callback_data=texts.markup_add_another))


def cancel(func):
    def inner(*args, **kwargs):
        if not args[0].text.startswith('/'):
            func(*args, **kwargs)
        else:
            functions.try_login(args[0]).append_list.clear()
            functions.try_login(args[0]).delete_category = None
            functions.ap(args[0], bot.send_message(args[0].chat.id, texts.cancel_accept, reply_markup=delete_markup))

    return inner


@bot.message_handler(commands=['start'])
def start(message):
    functions.try_login(message)
    bot.send_message(message.chat.id, texts.start)


@bot.message_handler(commands=['input'])
def _input(message):
    """Предлагает ввести категорию"""
    functions.insert(message, message.chat.id)
    bot.register_next_step_handler(msg := (bot.send_message(message.chat.id, texts.input_step_1)), inputStep1)
    functions.ap(message, msg)


@cancel
def inputStep1(message):
    """Ввод категории, проложение ввода вопроса"""
    functions.insert(message, message.text)
    bot.register_next_step_handler(msg := (bot.send_message(message.chat.id, texts.input_step_2)), inputStep2)
    functions.ap(message, msg)


@cancel
def inputStep2(message):
    """Ввод вопроса, предложение ввода ответа"""
    functions.insert(message, message.text)
    bot.register_next_step_handler(msg := (bot.send_message(message.chat.id, texts.input_step_3)), inputStep3)
    functions.ap(message, msg)


@cancel
def inputStep3(message):
    """Ввод ответа, предложение добавления описания"""
    functions.insert(message, message.text)
    functions.ap(message, bot.send_message(message.chat.id, texts.input_step_4, reply_markup=description_markup))


@cancel
def inputStep4(message):
    """Ввод описания"""
    functions.insert(message, message.text, True)
    functions.ap(message, bot.send_message(message.chat.id, texts.input_step_6, reply_markup=delete_and_input_markup))


@bot.message_handler(commands=['delete', 'del'])
def delete(message):
    msg = bot.send_message(message.chat.id, texts.delete_step_1)
    bot.register_next_step_handler(msg, deleteStep1)
    functions.ap(message, msg)


@cancel
def deleteStep1(message):
    if message.text in database.get_category(message.chat.id):
        functions.try_login(message).delete_category = message.text
        msg = bot.send_message(message.chat.id, texts.delete_step_2)
        bot.register_next_step_handler(msg, deleteStep2)
    else:
        msg = bot.send_message(message.chat.id, texts.delete_step_1_except)
        bot.register_next_step_handler(msg, deleteStep1)
    functions.ap(message, msg)


@cancel
def deleteStep2(message):
    try:
        if message.text in database.get_words(message):
            database.connect("delete_string", message)
            msg = bot.send_message(message.chat.id, texts.delete_step3_1 + message.text.strip() + texts.delete_step3_2,
                                   reply_markup=delete_markup)
        else:
            msg = bot.send_message(message.chat.id, texts.delete_step_2_except)
            bot.register_next_step_handler(msg, deleteStep2)
        functions.ap(message, msg)
    except Exception as e:
        print(e)


@bot.message_handler(commands=['list'])
def show_list(message):
    functions.ap(message)
    if data := functions.get_list(message.chat.id):
        for i in data:
            functions.ap(bot.send_message(message.chat.id, i, reply_markup=delete_markup))
    else:
        functions.ap(bot.send_message(message.chat.id, texts.empty_list, reply_markup=delete_markup))


@bot.message_handler(commands=['types'])
def types(message):
    functions.ap(message)
    if data := database.get_category(message.chat.id):
        functions.ap(bot.send_message(message.chat.id, "Ваши категории:\n" + "\n".join(data)))
    else:
        functions.ap(bot.send_message(message.chat.id, texts.empty_list))


@bot.message_handler(commands=['train', 'game'])
def game(message):
    bot.register_next_step_handler((msg := bot.send_message(message.chat.id, texts.game_step_1)), gameStep1)
    functions.ap(message, msg)


@cancel
def gameStep1(message):
    if message.text in database.get_category(message.chat.id):
        functions.start_game(message, message.text)
        if functions.try_login(message).game_list:
            functions.try_login(message).is_game = True
            word = functions.try_login(message).game_list.pop(0)
            functions.try_login(message).last_message_text = word
            msg = bot.send_message(message.chat.id, texts.game_started + '"' + message.text + '"' + '\n' + word)
        else:
            msg = bot.send_message(message.chat.id, texts.input_words)
    else:
        bot.register_next_step_handler((msg := bot.send_message(message.chat.id, texts.game_step_1_except)),
                                       gameStep1)
    functions.ap(message, msg)


@bot.message_handler(commands=['stop'])
def stop(message):
    functions.ap(message, bot.send_message(message.chat.id, functions.stop(message), reply_markup=delete_markup))


@bot.message_handler(content_types=['text'])
def text(message):
    try:
        user = functions.try_login(message)
        if user.is_game:
            if message.text == user.answers[user.last_message_text]:
                string = texts.game_accept
            else:
                string = texts.game_except
            if not user.game_list:
                functions.restart_game(message)
                string += "\n" + texts.game_reset_list_1 + user.game_category + texts.game_reset_list_2
            word = user.game_list.pop(0)
            user.last_message_text = word
            functions.ap(bot.send_message(message.chat.id, string + '\n' + word))
        else:
            functions.ap(bot.send_message(message.chat.id, texts.not_in_use, reply_markup=delete_markup))
    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda x: True)
def callback(call):
    match call.data:
        case "Убрать":
            try:
                for i in functions.try_login(call.message).delete_list:
                    bot.delete_message(call.message.chat.id, i)
            except:
                pass
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            functions.try_login(call.message).delete_list.clear()
        case "Да":
            bot.register_next_step_handler(msg := (bot.send_message(call.message.chat.id, texts.input_step_5)),
                                           inputStep4)
            functions.ap(msg)
        case "Нет":
            functions.insert(call.message, "None", True)
            functions.ap(bot.send_message(call.message.chat.id, texts.input_step_6,
                                          reply_markup=delete_and_input_markup))
        case texts.markup_add_another:
            _input(call.message)
    if call.data in ["Да", "Нет", texts.markup_add_another]:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


if __name__ == "__main__":
    while True:
        try:
            bot.polling()
        except:
            sleep(15)
