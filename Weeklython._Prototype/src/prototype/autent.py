import random
import smtplib
from email.mime.text import MIMEText # для темы сообщения

def get_login(group, login): # приходит переменная которая хранит (адм учасник абитуриент)
    if (group == 'adm'):
        mail = login + '@21-school.ru'  # получаем почту adm
    else:
        mail = login + '@student.21-school.ru' # получаем почту пира
    random_num = random.randint(1001, 9998) # генерируем цифры
    print(send_message(mail, random_num))
    return random_num


def send_message(mail, random_num):
    sender = "booking.school.21@gmail.com"
    password = "xccjdamwmevuzgjt" # если будет время спрятать пароль используя переменное окружение
    server = smtplib.SMTP("smtp.gmail.com", 587) # передали сервер и по дифолту порт
    server.starttls() # шифрованый обмен по тлс
    # логинимся и отправляем
    random_num = str(random_num)
    try:
        server.login(sender, password) # отправитель
        letter = 'Ваш код для авторизации: ' + str(random_num) + '. Держите его в секрете!-_-)'
        msg = MIMEText(letter) # для темы сообщения
        msg["Subject"] = "Супер секретный код" # для темы сообщения
        server.sendmail(sender, mail, msg.as_string()) # отправитель получатель сообщение (можно просто massege, что бы без темы
        print(random_num)
        # обратботка ошибок
    except Exception as _ex:
        print(random_num)
        return f"{_ex}\n что-то не так, попробуйте снова (╯ರ ~ ರ)╯︵ ┻━┻"


def check_pass(random_num, pass_num):
    pass_num
    if (pass_num == random_num):
        print('Отлично, вы зарегистрированы ⊂(・﹏・⊂)')
    else:
        print('Код не верный, попробуй снова (╯ರ ~ ರ)╯︵ ┻━┻')


def main():
    group = 'stud'
    print(get_login(group)) # структура в которой хранится группа


if __name__ == "__main__":
    main()

