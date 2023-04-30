from sqlite3 import connect as cn
import functions


def connect(func, *args, **kwargs):
    db = cn("database.db")
    with db:
        sql = db.cursor()

        def start(restart=False):
            if restart:
                sql.execute("DROP TABLE IF EXISTS data")
                db.commit()
            sql.execute("CREATE TABLE IF NOT EXISTS data (id INT, type TEXT, word TEXT, answer TEXT, description TEXT)")
            db.commit()

        def insert(values):
            if len(values) == 5:
                sql.execute("INSERT INTO data VALUES (?, ?, ?, ?, ?)", values)
                db.commit()

        def delete_string(message):
            category = functions.try_login(message).delete_category
            word = message.text
            sql.execute(f"DELETE FROM data WHERE type = '{category}' and word = '{word}'")
            db.commit()


        match func:
            case "start": start(*args, **kwargs)
            case "insert": insert(*args, **kwargs)
            case "get_category": get_category(*args, **kwargs)
            case "get_words": get_words(*args, **kwargs)
            case "delete_string": delete_string(*args, **kwargs)
    db.close()


def get_category(chat_id):
    categories = set()
    db = cn("database.db")
    with db:
        sql = db.cursor()
        sql.execute(f"SELECT type FROM data WHERE id = {chat_id}")
        if sql.fetchone() is not None:
            for i in sql.execute(f"SELECT type FROM data WHERE id = {chat_id}"):
                categories.add(i[0])
    db.close()
    return sorted(categories)


def get_words(message):
    category = functions.try_login(message).delete_category
    words = set()
    db = cn("database.db")
    with db:
        sql = db.cursor()
        for i in sql.execute(f"SELECT word FROM data WHERE id = {message.chat.id} AND type = '{category}'"):
            words.add(i[0])
    db.close()
    return sorted(words)


def get_all(chat_id: int) -> list:
    db = cn('database.db')
    words = []
    with db:
        sql = db.cursor()
        for i in sql.execute(f"SELECT word, answer, type FROM data WHERE id = {chat_id} ORDER BY type ASC"):
            words.append(i)
    db.close()
    return words


def get_words_by_category(chat_id, category):
    db = cn('database.db')
    words = dict()
    with db:
        sql = db.cursor()
        for word, answer in sql.execute(f"SELECT word, answer FROM data WHERE id = {chat_id} AND type = '{category}'"):
            words[word] = answer
    db.close()
    return words
