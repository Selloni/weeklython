import datetime, sqlite3

class User:
	'''Описывает пользователя'''

	def __init__(self, r, l, m, c, n):
		self.role = r
		self.login = l # нужна проверка логина на правильность ввода (без кириллицы и т п)
		self.mail = m
		self.campus = c
		self.name = n
		self.booking_rowid = []
		self.booking_begin = []
		self.booking_end = []

	def print_info(self):
		print(f'role: {self.role}')
		print(f'login: {self.login}')
		print(f'mail: {self.mail}')
		print(f'campus: {self.campus}')
		print(f'name: {self.name}')


class BookingObject:
	'''Описывает объект бронирования'''
	
	def __init__(self, k, n , d, c, f, p, b_b, b_e, b_n, q=0):
		self.kind = k
		self.name = n
		self.description = d
		self.campus = c
		self.floor = f
		self.pic = p
		self.booking_begin = b_b
		self.booking_end = b_e
		self.booking_nicks = b_n
		self.quantity = q

	def print_info(self):
		print(f' kind: {self.kind}\n name: {self.name}\n description: {self.description}\n campus: {self.campus}\n\
 floor: {self.floor}\n pic: {self.pic}\n booking_begin: {self.booking_begin}\n\
 booking_end: {self.booking_end}\n booking_nicks: {self.booking_nicks}')


# функция записывает объекты в строку, вставляя между ними ';' 
def list_to_str(smth):
	res = ";".join(str(item) for item in smth)
	return res


# функция извлекает список дат из строки
def str_to_datelist(string):
	if string != '':
		str_list = string.split(";")
		res = []
		for date in str_list:
			date = date[:19]
			res.append(datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S"))
		return res


def str_to_strlist(string):
	return string.split(";")


def add_obj_to_db(c, obj):
	c.execute("INSERT INTO booking_objects (kind, name, description, campus, floor, pic, booking_begin, booking_end, booking_nicks) \
	VALUES (?, ?, ?, ?, ?)", \
	(obj.kind, obj.name, obj.description, obj.campus, obj.floor, obj.pic, \
	list_to_str(obj.booking_begin), list_to_str(obj.booking_end), list_to_str(obj.booking_nicks)))

def add_user_to_db(c, user):
	c.execute("INSERT INTO users (role, login, mail, campus, name) \
	VALUES (?, ?, ?, ?, ?)", \
	(user.role, user.login, user.mail, user.campus, user.name))


def get_object_from_db(c, object_kind, object_name):
	c.execute("SELECT * FROM booking_objects WHERE kind=? and name=?", (object_kind, object_name))
	i = c.fetchall()[0]
	new_object = BookingObject(i[0], i[1], i[2], i[3], i[4], i[5], str_to_datelist(i[6]), str_to_datelist(i[7]), i[8].split(";"))
	return new_object	


def print_all_objects(c):
    c.execute("SELECT * FROM booking_objects")
    print(c.fetchall())


def add_new_booktime(smth, user):
    db = sqlite3.connect('s21_bookbot.db', check_same_thread=False)
    c = db.cursor()

    nicks = list_to_str(smth.booking_nicks)
    if nicks and nicks[0] == ';':
        nicks = nicks[1:]

    c.execute("UPDATE booking_objects SET booking_begin=?, booking_end=?, booking_nicks=? WHERE name=?", \
    (list_to_str(smth.booking_begin), list_to_str(smth.booking_end), \
    nicks, smth.name))
    db.commit()

    user.booking_begin.append(smth.booking_begin[-1])
    user.booking_end.append(smth.booking_end[-1])

    c.execute("SELECT rowid FROM booking_objects WHERE name=?", (smth.name,))
    row_id = c.fetchone()[0]
    user.booking_rowid.append(row_id)
    c.execute("UPDATE users SET booking_rowid=?, booking_begin=?, booking_end=? WHERE name = ?", \
    	(list_to_str(user.booking_rowid), list_to_str(user.booking_begin), list_to_str(user.booking_end), user.name))
    db.commit()

    db.close()