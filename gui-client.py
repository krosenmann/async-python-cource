#!/usr/bin/env python3

import asyncio
import concurrent.futures
import socket
import threading
from tkinter import *
from tkinter import font
from tkinter import ttk, messagebox

from client import recieve, send, ws_connect, sign_in, room_list


class GUI:

    def __init__(self):

        # Достаем цикл событий для asyncio, все сопрограммы будем выполнять в нем
        self.aloop = asyncio.get_event_loop()
        
        # Окно чата, пока скрыто
        self.root = Tk()
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        
        # Окно Логина
        self.login = Toplevel()
        # Установим заголовок окна
        self.login.title("Login")
        self.login.resizable(width = False,
                             height = False)
        self.login.configure(width = 400,
                             height = 300)
        # Добавим надпись
        self.pls = Label(self.login,
                         text = "Please login to continue",
                         justify = CENTER,
                         font = "Helvetica 14 bold")
        
        self.pls.place(relheight = 0.15,
                       relx = 0.2,
                       rely = 0.07)

        # Поле ввода пароля с надписью слева
        self.label_name = Label(self.login,
                                text = "Имя пользователя: ")

        self.label_name.place(relheight = 0.1,
                              relx = 0.1,
                              rely = 0.2)
        
        self.entry_name = Entry(self.login)
        
        self.entry_name.place(relwidth = 0.4,
                              relheight = 0.1,
                              relx = 0.45,
                              rely = 0.2)

        # Поле ввода пароля с надписью слева
        self.label_password = Label(self.login,
                                    text = "Пароль: ")
        self.label_password.place(relheight = 0.1,
                                  relx = 0.1,
                                  rely = 0.3)

        self.entry_password = Entry(self.login)
        self.entry_password.place(relwidth = 0.4,
                                  relheight = 0.1,
                                  relx = 0.45,
                                  rely = 0.3)
        
        # Поместить курсор в поле ввода логина
        self.entry_name.focus()
        
        # Создаем кнопку "Войти" и привязываем действие (команду)
        # Команда - это просто функция без аргументов.
        self.go = Button(self.login,
                         text = "Войти",
                         command = lambda: self.go_ahead(self.entry_name.get(), # Передаем имя пользователя и пароль из формы.
                                                         self.entry_password.get())) # Передача происходит не прямо сейчас, а только когда кнопку "Войти" нажмут.

        self.go.place(relx = 0.4,
                      rely = 0.55)
        # Запускаем цикл событий приложений
        self.root.mainloop()

    # Команда, которая выполняется по нажатию кнопки Login
    def go_ahead(self, name, password):
        cookie = self.authorize(name, password)
        self.login.destroy()    # Закрываем окно с логином
        self.layout(name)       # Запускаем отрисовку и построение окна с чатом.
        # Пока дополнительный манипуляций не делаем. 

    def authorize(self, name, password):
        def _auth(loop):
            return loop.run_until_complete(sign_in(name, password))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            fut = executor.submit(_auth, self.aloop)
            try:
                self.cookie = fut.result()
            except Exception as exc:
                messagebox.showerror("Ошибка", exc.message)
                raise exc       # Это возбуждение все равно нужно, т.к. мы
                                # хотим, чтобы пользователь мог
                                # повторить ввод логина и пароля.
                                # + Это traceback будет полезен при отладке.
        return self.cookie

    # основное окно чата
    def layout(self,name):
        self.name = name
        # Показать окно чата
        self.root.deiconify()
        self.root.title("FANCY CHAD")
        self.root.resizable(width = False, # Запрещаем менять размер окна мышкой и по длине и по ширине
                            height = False)
        # Устанавливаем размеры окна 
        self.root.configure(width = 470,
                            height = 550,
                            )
        # Пишем имя пользователя в верху
        self.label_head = Label(self.root,
                                text = self.name,
                                pady = 5)
        self.label_head.place(relwidth = 1)

        # Виджет текста, куда будут выводиться сообщения
        self.text_cons = Text(self.root,
                             width = 20,
                             height = 2,
                             font = "Helvetica 14",
                             padx = 5,
                             pady = 5)

        self.text_cons.place(relheight = 0.745,
                            relwidth = 1,
                            rely = 0.08)

        
        # Теперь место для виджета с вводом текста и кнопки отправить
        self.label_bottom = Label(self.root,
                                 height = 80)
        
        self.label_bottom.place(relwidth = 1,
                               rely = 0.825)
        
        # Виджет ввода текста
        self.entry_msg = Entry(self.label_bottom,
                              font = "Helvetica 13")
        self.entry_msg.place(relwidth = 0.74,
                            relheight = 0.06,
                            rely = 0.008,
                            relx = 0.011)
        # Установим курсор в поле ввода
        self.entry_msg.focus()
        
        # Создаем кнопку "Отправить" В качестве команды будет метод
        # ``send_button``, а в качестве аргумента пусть берет
        # сообщение из поля ввода.
        self.buttonMsg = Button(self.label_bottom,
                                text = "Send",
                                font = "Helvetica 10 bold",
                                width = 20,
                                command = lambda : self.send_button(self.entry_msg.get()))
        
        self.buttonMsg.place(relx = 0.77,
                             rely = 0.008,
                             relheight = 0.06,
                             relwidth = 0.22)
        
        self.text_cons.config(cursor = "arrow")
        
        # Создадим скроллбар в виджете просмотра сообщений
        scrollbar = Scrollbar(self.text_cons)
        # И расположим этот скорллбар справа
        scrollbar.place(relheight = 1,
                        relx = 0.974)
        # И привяжем команду для прокрутки содержимого виджета
        scrollbar.config(command = self.text_cons.yview)
        # И наконец, запретим редактирование (этот виджет нужен только для просмотра)
        self.text_cons.config(state = DISABLED)
        
    # А это команда для отправки сообщения. Пока она только удаляет сообщение из поля ввода.
    # Если этого не сделать, содержимое ввода будет оставаться неизменным, а это нам ни к чему
    def send_button(self, msg):
        self.msg=msg
        self.entry_msg.delete(0, END)

if __name__ == '__main__':
    GUI()
