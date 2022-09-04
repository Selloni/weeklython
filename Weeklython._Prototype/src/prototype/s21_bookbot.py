from gc import callbacks
import telebot, sqlite3, datetime
from telebot import types
from autent import get_login, check_pass
import backend

token='5711233653:AAHVtS--fLwneSbj1YvS6Fimpwu7M0iitdQ'
bot=telebot.TeleBot(token)
USER = 0


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Здравствуйте, я - бот для бронирования.')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('АДМ', callback_data = 'adm'), types.InlineKeyboardButton('Участник', callback_data = 'member'), types.InlineKeyboardButton('Абитуриент', callback_data = 'abiturient'))
    bot.send_message(message.chat.id, "А вы?", reply_markup=markup)


@bot.callback_query_handler(func = lambda call: call.data.startswith('adm') or call.data.startswith('member') or call.data.startswith('abiturient'))
def answer(call):
    msg = bot.send_message(call.message.chat.id, f'Хорошо, теперь напишите свой логин')
    group = call.data
    bot.register_next_step_handler(msg, nickname, group)


def nickname(message, group):
    login = message.text
    code = get_login(group, login)
    if (group == 'adm'):
        msg = bot.send_message(message.chat.id, f'Приятно познакомиться, {login}! На вашу почту {login}@21-school.ru был отправлен код доступа, напишите его сюда.')
    else:
        msg = bot.send_message(message.chat.id, f'Приятно познакомиться, {login}! На вашу почту {login}@student.21-school.ru был отправлен код доступа, напишите его сюда')
    bot.register_next_step_handler(msg, mail_code, code, group, login)


def mail_code(message, code, group, login):
    code = str(code)
    if (message.text == code):
        if (group == 'adm'):
            mail = login + '@21-school.ru'
        else:
            mail = login + '@student.21-school.ru'
        new_user = backend.User(group, login, mail, 'kzn', 'username')

        global USER
        USER = new_user

        db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
        c = db.cursor()
        backend.add_user_to_db(c, USER)
        db.commit()
        db.close()

        msg = bot.send_message(message.chat.id, f'Вы успешно аутентифицировались.')
        booking(msg)
    else:
        if (message.text != '/start'):
            msg = bot.send_message(message.chat.id, f'Код неверен, попробуйте ещё раз.')
            bot.register_next_step_handler(msg, mail_code, code, group, login)


@bot.message_handler(commands=['du'])
def deafault_user(message):
    # функция для простоты демонстрации и отладки
    global USER
    USER = backend.User('adm', 'testuser', 'testuser@testuser.ru', 'kzn', 'username')
    msg = bot.send_message(message.chat.id, 'Создан тестовый пользователь.')
    USER.print_info()
    booking(msg)


@bot.message_handler(commands=['new'])
def booking(message):
    if (USER):
        mk = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        if USER.role == 'adm':
            mk.add(types.KeyboardButton("Переговорную"), types.KeyboardButton("Книги"), types.KeyboardButton("Игры"), types.KeyboardButton("Кухню"), \
            types.KeyboardButton("Показать мои брони"))
        else:
            mk.add(types.KeyboardButton("Переговорную"), types.KeyboardButton("Книги"), types.KeyboardButton("Игры"), \
            types.KeyboardButton("Показать мои брони"))            
        msg = bot.send_message(message.chat.id, 'Что хотите забронировать?', reply_markup = mk)
        bot.register_next_step_handler(msg, whattotake)
    else:
        bot.send_message(message.chat.id, 'Чтобы воспользоваться командами, необходимо пройти аутентификацию')


def whattotake(message):
    if (message.text == 'Книги'):
        print_books_list(message)
    elif (message.text == 'Переговорную'):
        print_conf_rooms_list(message)
    elif (message.text == 'Игры'):
        print_games_list(message)
    elif (message.text == 'Показать мои брони'):
        show_my_booking(message)
    elif (message.text == 'Кухню'):
        print_kitchen_list(message)


def print_kitchen_list(message):
    db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
    c = db.cursor()
    c.execute("SELECT * FROM booking_objects WHERE kind='kitchen'")
    kitchens = []

    for i in c.fetchall():
        new_object = backend.BookingObject(i[0], i[1], i[2], i[3], i[4], i[5], backend.str_to_datelist(i[6]), backend.str_to_datelist(i[7]), i[8].split(";"), i[9])
        kitchens.append(new_object)

    db.close()

    kitchens.sort(key = lambda x: x.floor)

    s = ''
    i = 1
    for k in kitchens:
        s += f"{i}. {k.name}\n"
        i += 1

    s += "\nКакую кухню вы хотите забронировать, а главное - зачем? Введите номер.\n"
    bot.send_message(message.chat.id, s)
    bot.register_next_step_handler(message, choose_kitchen_number, kitchens)


def choose_kitchen_number(message, kitchens):
    try:
        k_index = int(message.text)
    except:
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_kitchen_number, kitchens)
        return

    if (k_index < 1 or k_index > len(kitchens)):
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_kitchen_number, kitchens)
    else:
        chosen_k = kitchens[k_index-1]\

        s = "Выберите дату:\n"
        today = datetime.datetime.today()
        for i in range(1, 8):
            s += '\n' + (f'{i}. {today.strftime("%d/%m")}')
            today += datetime.timedelta(days=1)
        
        bot.send_message(message.chat.id, s)

        # получаем номер выбранной даты
        bot.register_next_step_handler(message, choose_kitchen_date_number, chosen_k)



def choose_kitchen_date_number(message, chosen_k):
    try:
        date_index = int(message.text)
    except:
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_conf_date_number, chosen_room)
        return

    if (date_index < 1 or date_index > 7):
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_conf_date_number, chosen_room)
    else:
        # выбранная дата
        chosen_date = datetime.date.today() + datetime.timedelta(days=date_index-1)

        new_beg_date = datetime.datetime(chosen_date.year, chosen_date.month, chosen_date.day, 0, 0)
        new_end_date = new_beg_date + datetime.timedelta(days = 1)

        if not chosen_k.booking_begin:
            chosen_k.booking_begin = []
        chosen_k.booking_begin.append(new_beg_date)

        if not chosen_k.booking_end:
            chosen_k.booking_end = []
        chosen_k.booking_end.append(new_end_date)

        if not chosen_k.booking_nicks:
            chosen_k.booking_nicks = []
        chosen_k.booking_nicks.append(USER.login)

        # добавляем новое время бронирования в базу данных 
        backend.add_new_booktime(chosen_k, USER)
        bot.send_message(message.chat.id, 'Поздравляем, вы можете пользоваться кухней целые сутки! (А чего мелочиться? Вы ведь АДМ!)')

        booking(message)


def print_games_list(message):
    db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
    c = db.cursor()
    c.execute("SELECT * FROM booking_objects WHERE kind='game' or kind='sport' or kind = 'boardgame'")
    games = []

    for i in c.fetchall():
        new_object = backend.BookingObject(i[0], i[1], i[2], i[3], i[4], i[5], backend.str_to_datelist(i[6]), backend.str_to_datelist(i[7]), i[8].split(";"), i[9])
        games.append(new_object)

    games.sort(key = lambda x: x.name)
    games.sort(key = lambda x: x.kind)

    db.close()

    # 1. boardgame, 2. game, 3. sport
    s = ''
    flag = 0
    num = 1
    for game in games:
        if game.kind == 'boardgame':
            if flag < 1: 
                s += 'Настольные игры:\n'
                flag = 1
            s += f'{num}. "{game.name}"\n'
        elif game.kind == 'game':
            if flag < 2: 
                s += '\nДиски для PlayStation:\n'
                flag = 2
            s += f'{num}. "{game.name}"\n'
        elif game.kind == 'sport':
            if flag < 3: 
                s += '\nСпортивный инвентарь:\n'
                flag = 3
            s += f'{num}. {game.name}\n'
        num += 1

    s += '\nВведите номер объекта бронирования:'

    bot.send_message(message.chat.id, s)

    # получаем номер
    bot.register_next_step_handler(message, choose_game_number, games)


def choose_game_number(message, games):
    try:
        game_index = int(message.text)
    except:
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_game_number, games)
        return

    if (game_index < 1 or game_index > len(games)):
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_game_number, games)
    else:
        chosen_game = games[game_index-1]
        s = f"Вы выбрали {chosen_game.name}\n"
        bot.send_message(message.chat.id, s)

        if chosen_game.name == 'Манчкин':
            bot.send_photo(message.chat.id, open('img/Манчкин.jpeg', 'rb'))
        elif chosen_game.name == 'Кошмарики':
            bot.send_photo(message.chat.id, open('img/Кошмариум.jpeg', 'rb'))
        elif chosen_game.name == 'Гномы вредители':
            bot.send_photo(message.chat.id, open('img/Gnomes.jpeg', 'rb'))
        elif chosen_game.name == 'Свинтус':
            bot.send_photo(message.chat.id, open('img/Свинтус.jpeg', 'rb'))
        elif chosen_game.name == 'Шахматы':
            bot.send_photo(message.chat.id, open('img/Шахматы.jpeg', 'rb'))

        if not chosen_game.booking_begin:
            chosen_game.booking_begin = []

        if not chosen_game.booking_end:
            chosen_game.booking_end = []

        today = datetime.datetime.today()
        chosen_game.booking_begin.append(today)
        book_end = today + datetime.timedelta(days=7)
        chosen_game.booking_end.append(book_end)
        chosen_game.booking_nicks.append(USER.login)
        # chosen_game.quantity -= 1

        s = f'Вы успешно забронировали {chosen_game.name} с {today.strftime("%H:%M %d/%m/%y")} по {book_end.strftime("%H:%M %d/%m/%y")}.'
        backend.add_new_booktime(chosen_game, USER)
        bot.send_message(message.chat.id, s)
        booking(message)


def print_books_list(message):
    db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
    c = db.cursor()
    c.execute("SELECT * FROM booking_objects WHERE kind='book'")
    books = []

    for i in c.fetchall():
        new_object = backend.BookingObject(i[0], i[1], i[2], i[3], i[4], i[5], backend.str_to_datelist(i[6]), backend.str_to_datelist(i[7]), i[8].split(";"), i[9])
        books.append(new_object)

    books.sort(key = lambda x: x.name) 

    db.close()

    num = 1
    s = ''
    for book in books:
        s += (f"\n{num}. \"{book.name}\", {book.description}")
        num += 1
        if (num % 50 == 0) or (num == len(books)):
            bot.send_message(message.chat.id, s)
            s = ''

    bot.send_message(message.chat.id, 'Введите номер книги:')

    # получаем номер книги
    bot.register_next_step_handler(message, choose_book_number, books)


def choose_book_number(message, books):

    try:
        book_index = int(message.text)
    except:
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_book_number, books)
        return

    if (book_index < 1 or book_index > len(books)):
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_book_number, books)
    else:
        chosen_book = books[book_index-1]
        s = f"Выбранная книга: \"{chosen_book.name}\", {chosen_book.description}.\n"
        
        if (chosen_book.quantity == 0):
            s += '\nВ данный момент свободных экземпляров нет.\n'
            return

        s += f"В наличии {chosen_book.quantity} экз.\n"

        if not chosen_book.booking_begin:
            chosen_book.booking_begin = []

        if not chosen_book.booking_end:
            chosen_book.booking_end = []

        today = datetime.datetime.today()
        chosen_book.booking_begin.append(today)
        book_end = today + datetime.timedelta(hours=3)
        chosen_book.booking_end.append(book_end)
        chosen_book.booking_nicks.append(USER.login)
        chosen_book.quantity -= 1

        s += f'Вы успешно забронировали книгу с {today.strftime("%H:%M %d/%m/%y")} по {book_end.strftime("%H:%M %d/%m/%y")}.'
        backend.add_new_booktime(chosen_book, USER)
        bot.send_message(message.chat.id, s)
        booking(message)


def print_conf_rooms_list(message):
    db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
    c = db.cursor()
    c.execute("SELECT * FROM booking_objects WHERE kind='conference_room'")
    rooms = []

    for i in c.fetchall():
        new_object = backend.BookingObject(i[0], i[1], i[2], i[3], i[4], i[5], backend.str_to_datelist(i[6]), backend.str_to_datelist(i[7]), i[8].split(";"))
        rooms.append(new_object)

    db.close()

    bot.send_photo(message.chat.id, open('img/1st_floor.jpg', 'rb'))
    bot.send_photo(message.chat.id, open('img/2nd_floor.jpg', 'rb'))
    bot.send_photo(message.chat.id, open('img/3rd_floor.jpg', 'rb'))

    # печатаем список переговорок
    num = 1
    r_dict = {}
    s = ''
    for i in range(1, 4):
        s += (f'\n{i}-й этаж:\n')
        for room in rooms:
            if room.floor == i:
                s += (f'{num}. {room.name}\n')
                r_dict[num] = room
                num += 1

    s += '\n Введите номер переговорки:'
    bot.send_message(message.chat.id, s) # вместо print

    # получаем номер переговорки
    bot.register_next_step_handler(message, choose_conf_room_number, rooms, r_dict)


def choose_conf_room_number(message, rooms, r_dict):
    try:
        room_index = int(message.text)
    except:
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_conf_room_number, rooms, r_dict)
        return

    if (room_index < 1 or room_index > len(rooms)):
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_conf_room_number, rooms, r_dict)
    else:
        chosen_room = r_dict[room_index]
        bot.send_message(message.chat.id, 'Выбранная переговорка: ' + chosen_room.name)

        if chosen_room.name == 'Orion':
            bot.send_photo(message.chat.id, open('img/Orion.jpeg', 'rb'))
        elif chosen_room.name == 'Erehwon':
            bot.send_photo(message.chat.id, open('img/Erehwon.jpeg', 'rb'))
        elif chosen_room.name == 'Liberty':
            bot.send_photo(message.chat.id, open('img/Liberty.jpeg', 'rb'))
        elif chosen_room.name == 'Cassiopeia':
            bot.send_photo(message.chat.id, open('img/Cassiopeia.jpeg', 'rb'))
        elif chosen_room.name == 'Oasis':
            bot.send_photo(message.chat.id, open('img/Oasis.jpeg', 'rb'))
        elif chosen_room.name == 'Quazar':
            bot.send_photo(message.chat.id, open('img/Quazar.jpeg', 'rb'))
        elif chosen_room.name == 'Pulsar':
            bot.send_photo(message.chat.id, open('img/Pulsar.jpeg', 'rb'))

        s = "Выберите дату:\n"
        today = datetime.datetime.today()
        for i in range(1, 8):
            s += '\n' + (f'{i}. {today.strftime("%d/%m")}')
            today += datetime.timedelta(days=1)
        
        bot.send_message(message.chat.id, s)

        # получаем номер выбранной даты
        bot.register_next_step_handler(message, choose_conf_date_number, chosen_room)


def choose_conf_date_number(message, chosen_room):
    try:
        date_index = int(message.text)
    except:
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_conf_date_number, chosen_room)
        return

    if (date_index < 1 or date_index > 7):
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, choose_conf_date_number, chosen_room)
    else:
        # выбранная дата
        chosen_date = datetime.date.today() + datetime.timedelta(days=date_index-1)
        bot.send_message(message.chat.id, 'Выбранная дата: ' + str(chosen_date))

        s = ''

        # выводим забронированные в этот день слоты
        if chosen_room.booking_begin:
            flag = 1
            for beg, end, nick in zip(chosen_room.booking_begin, chosen_room.booking_end, chosen_room.booking_nicks):
                    if beg.day == chosen_date.day and beg.month == chosen_date.month:
                        if flag == 1:
                            s += '\n Переговорка забронирована в следующее время:\n'
                            flag = 0
                        s += ('c ' + beg.strftime("%H:%M") + ' до ' + end.strftime("%H:%M") + ' участником ' + nick + '\n')

        s += "\nВыберите время для бронирования:\n"

        # формируем словарь для часов
        hours = {}
        num = 1
        for i in range(9, 23):
            hours[num] = i
            num += 1

        # удаляем из словаря часов те, которые забронированы
        if chosen_room.booking_begin:
            for booktime in chosen_room.booking_begin:
                if (booktime.day == chosen_date.day and booktime.month == chosen_date.month):
                    del hours[booktime.hour - 8]

        # выводим доступные для бронирования в указанную дату слоты
        num = 1
        true_hours = {} # словарь для правильного рассчёта выбранных часов
        for h in hours.items():
            s += (f'\n{num}. {h[1]}:00 - {h[1]+1}:00')
            true_hours[num] = h[1]
            num += 1

        bot.send_message(message.chat.id, s)
        
        # получаем номер выбранного времени
        bot.register_next_step_handler(message, set_conf_chosen_time, chosen_date, chosen_room, true_hours)


def set_conf_chosen_time(message, chosen_date, chosen_room, hours):
    try:
        time_index = int(message.text)
    except:
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, set_chosen_time, chosen_date, hours)
        return

    if (time_index < 1 or time_index > len(hours)):
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, set_chosen_time, chosen_date, hours)
    else:
        # осталось добавить выбранную дату в список забронированных
        bot.send_message(message.chat.id, f'Выбранное время: {str(hours[time_index])}:00 - {str(hours[time_index]+1)}:00')
    
        new_beg_date = datetime.datetime(chosen_date.year, chosen_date.month, chosen_date.day, hours[time_index], 0)
        if not chosen_room.booking_begin:
            chosen_room.booking_begin = []
        chosen_room.booking_begin.append(new_beg_date)

        new_end_date = new_beg_date + datetime.timedelta(hours = 1)
        if not chosen_room.booking_end:
            chosen_room.booking_end = []
        chosen_room.booking_end.append(new_end_date)

        if not chosen_room.booking_nicks:
            chosen_room.booking_nicks = []
        chosen_room.booking_nicks.append(USER.login)

        # добавляем новое время бронирования в базу данных 
        backend.add_new_booktime(chosen_room, USER)
        bot.send_message(message.chat.id, 'Вы успешно зарегались :)')
        booking(message)
      

def show_my_booking(message):
    db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
    c = db.cursor()

    s = ''
    i = 0
    for row_id, beg, end in zip(USER.booking_rowid, (USER.booking_begin), (USER.booking_end)):
        c.execute("SELECT name FROM booking_objects WHERE rowid=?",\
            (row_id,))
        s += f'{i+1}. {c.fetchone()[0]} с {beg.strftime("%H:%M %d/%m/%y")} по {end.strftime("%H:%M %d/%m/%y")}\n'
        i += 1

    i -= 1
    db.close()

    s += '\nВведите номер брони, чтобы её отменить, или "0", чтобы вернуться на предыдущий экран.\n'

    bot.send_message(message.chat.id, s)
    bot.register_next_step_handler(message, cancel_my_booking, i)


def cancel_my_booking(message, i):
    try:
        booking_index = int(message.text)
    except:
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, cancel_my_booking, i)
        return

    if (booking_index < 0 or booking_index > i+1):
        bot.send_message(message.chat.id, 'Неправильный номер, попробуйте ещё раз.')
        bot.register_next_step_handler(message, cancel_my_booking, i)
    elif (booking_index == 0):
        booking(message)
    else:
        booking_index -= 1
        db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
        c = db.cursor()

        c.execute("SELECT booking_begin, booking_end, booking_nicks FROM booking_objects WHERE rowid=?", (USER.booking_rowid[booking_index],))
        book_info = c.fetchone()
        beg_bookings = book_info[0].split(';')
        end_bookings = book_info[1].split(';')
        nicks_bookings = book_info[2].split(';')

        n = 0
        for beg, end, nick in zip(beg_bookings, end_bookings, nicks_bookings):
            if beg == str(USER.booking_begin[booking_index]) and end == str(USER.booking_end[booking_index]) and nick == USER.login:
                break
            else:
                n += 1

        del beg_bookings[n], end_bookings[n], nicks_bookings[n]

        c.execute("UPDATE booking_objects SET booking_begin=?, booking_end=?, booking_nicks=? WHERE rowid = ?", \
        (backend.list_to_str(beg_bookings), backend.list_to_str(end_bookings), backend.list_to_str(nicks_bookings), USER.booking_rowid[booking_index]))
        db.commit()

        del USER.booking_rowid[booking_index]
        del USER.booking_begin[booking_index]
        del USER.booking_end[booking_index]

        c.execute("UPDATE users SET booking_rowid=?, booking_begin=?, booking_end=? WHERE name = ?", \
        (backend.list_to_str(USER.booking_rowid), backend.list_to_str(USER.booking_begin), backend.list_to_str(USER.booking_end), USER.name))
        db.commit()
        db.close()

        bot.send_message(message.chat.id, "Бронь успешно отменена!")
        booking(message)


@bot.message_handler(commands=['adm'])
def adm(message):
    if (USER):
        if (USER.role == 'adm'):
            mk = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            mk.add(types.KeyboardButton("Показать список всех объектов"), types.KeyboardButton("Показать список всех пользователей"))
            msg = bot.send_message(message.chat.id, 'Выберите:', reply_markup=mk)
            bot.register_next_step_handler(msg, distributor)
        else:
            bot.send_message(message.chat.id, 'Данная команда доступна только для АДМ.')
    elif (USER == 0):
        bot.send_message(message.chat.id, 'Чтобы воспользоваться командами, необходимо пройти аутентификацию. Введите /start или /du.')


def distributor(message):
    if (message.text == 'Показать список всех пользователей'):
        show_users(message)
    elif (message.text == 'Показать список всех объектов'):
        show_objects(message)


def show_users(message):
    db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
    c = db.cursor()
    c.execute("SELECT * FROM users")
    users = []

    for i in c.fetchall():
        new_object = backend.User(i[0], i[1], i[2], i[3], i[4])
        users.append(new_object)
    
    users.sort(key = lambda x: x.login)

    db.close()

    num = 1
    s = ''
    for user in users:
        s += (f"\n{num}. {user.login}")
        num += 1
    
    bot.send_message(message.chat.id, s)


def show_objects(message):
    db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
    c = db.cursor()
    c.execute("SELECT * FROM booking_objects")
    objects = []

    for i in c.fetchall():
        new_object = backend.BookingObject(i[0], i[1], i[2], i[3], i[4], i[5], backend.str_to_datelist(i[6]), backend.str_to_datelist(i[7]), i[8].split(";"), i[9])
        objects.append(new_object)

    objects.sort(key = lambda x: x.name) 

    db.close()

    num = 1
    s = ''
    for obj in objects:
        s += (f"\n{num}. {obj.name}, {obj.description}")
        num += 1
        if (num % 50 == 0) or (num == len(objects)):
            bot.send_message(message.chat.id, s)
            s = ''


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '\
/new - забронировать новый объект;\n\
/adm - консоль администратора;\n\
/another_bot - другие боты Школы 21;\n\
/du - создать тестового пользователя.')


@bot.message_handler(commands=['another_bot'])
def collab(message):
    # markup_inline = types.InlineKeyboardMarkup().add
    but_pas = types.InlineKeyboardButton('Пригласить гостя', callback_data = 'Passbot')
    but_vot = types.InlineKeyboardButton('Проголосовать', callback_data = 'Votebot')
    but_check = types.InlineKeyboardButton('Мероприятие', callback_data = 'Checkinbot')
    markup_inline = types.InlineKeyboardMarkup().add(but_pas).add(but_check).add(but_vot)
    bot.send_message(message.chat.id,'Другие боты Школы 21:', reply_markup=markup_inline)


@bot.callback_query_handler(func = lambda call: call.data.startswith('Passbot') \
    or call.data.startswith('Votebot') or call.data.startswith('Checkinbot'))
def chose_user(call):
    if (call.data == 'Passbot'):
        keyboard = types.InlineKeyboardMarkup()
        key= types.InlineKeyboardButton('@pass_ftonita_bot', url='https://t.me/pass_ftonita_bot')
        keyboard.add(key)
        bot.send_message(call.message.chat.id,'С помощью этого бота вы можете заказать пропуск для гостей Школы,\n\
Немного правил: \n+ Не больше двух приглашенных персон;\n+ Продожительность прибывания не больше часа;\n+ Не хулиганить.', reply_markup=keyboard)
    
    if (call.data == 'Votebot'):
        keyboard = types.InlineKeyboardMarkup()
        key= types.InlineKeyboardButton('@s21_vote_bot', url='https://t.me/s21_vote_bot')
        keyboard.add(key)
        bot.send_message(call.message.chat.id, 'Бот для голосования. Возможно, ваш голос будет решающим.', reply_markup=keyboard)
    
    if (call.data == 'Checkinbot'):
        keyboard = types.InlineKeyboardMarkup()
        key= types.InlineKeyboardButton('@CheckinBot_bot', url='https://t.me/CheckinBot_bot')
        keyboard.add(key)
        bot.send_message(call.message.chat.id, 'То, что нужно, чтобы получить отметку о посещении мероприятия.', reply_markup=keyboard)


bot.polling(none_stop=True)
