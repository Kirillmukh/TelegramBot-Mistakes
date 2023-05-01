import database
from random import shuffle
import texts


user_dict = dict()


class User:
    def __init__(self, mid):
        self.mid = mid
        self.delete_list = list()

        self.append_list = list()
        self.delete_category = None

        self.is_game = False
        self.answers = dict()
        self.game_list = list()
        self.last_message_text = None
        self.game_category = None


def login(mid):
    user_dict[mid] = User(mid)


def ap(*args):
    "Добавляет сообщение в список для удаления"
    for message in args: try_login(message).delete_list.append(message.message_id)


def try_login(message):
    "Возвращает ссылку на класс"
    try:
        user = user_dict[message.chat.id]
    except:
        login(message.chat.id)
        user = user_dict[message.chat.id]
    return user


def insert(message, text, final = False):
    user = try_login(message)
    user.append_list.append(text)
    if final:
        database.connect("insert", user.append_list)
        user.append_list.clear()


def get_list(chat_id):
    data = database.get_all(chat_id)
    indexes = []
    for i in range(len(data) - 1):
        if data[i][-1] != data[i + 1][-1]:
            indexes.append(i + 1)
    for i in sorted(indexes, reverse=True):
        data.insert(i, "\n")
    count = 1
    for i in range(len(data) - 1):
        temp = ""
        if len(data[i]) == 3:
            word, answer, category = data[i]
            temp = f"{count}. {word} - {answer} [{category}]\n"
        elif len(data[i]) == 4:
            word, answer, description, category = data[i]
            temp = f"{count}. {word} - {answer} [{category}]\n{texts.description}{description}\n"
        if len(data[i]) >= 3 and len(data[i + 1]) >= 3:
            if data[i][-1] != data[i + 1][-1]:
                count = 1
            else:
                count += 1
        if len(data[i]) < 3: count = 1
        if temp: data[i] = temp
    if data:
        if len(data[-1]) == 3:
            word, answer, category = data[-1]
            data[-1] = f"{count}. {word} - {answer} [{category}]\n"
        elif len(data[-1]) == 4:
            word, answer, description, category = data[-1]
            data[-1] = f"{count}. {word} - {answer} [{category}]\n{texts.description}{description}\n"

    strings, index = [[]], 0
    while data:
        while len(strings[index]) < 100 and data:
            if data:
                strings[index].append(data.pop(0))
        index += 1
        strings.append([])
    if strings[0]: strings[0].insert(0, "номер. вопрос - ответ [категория]\n\n")
    for index, value in enumerate(strings):
        strings[index] = "".join(value)
    strings.remove("")
    return strings


def start_game(message, category):
    try_login(message).answers = database.get_words_by_category(message.chat.id, category)
    try_login(message).game_list = list(try_login(message).answers.keys())
    try_login(message).game_category = category
    shuffle(try_login(message).game_list)


def restart_game(message):
    try_login(message).game_list = list(try_login(message).answers.keys())
    shuffle(try_login(message).game_list)


def stop(message):
    user = try_login(message)
    user.is_game = False
    user.game_list.clear()
    user.answers.clear()
    user.last_message_text = None
    user.game_category = None
    return texts.game_ended
