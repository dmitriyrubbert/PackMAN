#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Отче наш, сущий на небесах! да святится имя Твое; да приидет Царствие Твое; 
# да будет воля Твоя и на земле, как на небе; хлеб наш насущный дай нам на сей день; 
# и прости нам долги наши, как и мы прощаем должникам нашим; и не введи нас в искушение, 
# но избавь нас от лукавого. Ибо Твое есть Царство и сила и слава во веки. Аминь.

import hashlib
import logging
import cPickle
import csv
import time
import re
import copy
import sys
import sys

from Tkinter import *
import tkMessageBox
import ttk
from threading import Thread
from random import choice
from grab import Grab
from grab.spider import Spider, Task
from grab.spider import Spider, Task
from weblib.logs import default_logging

# Дописать автоинсталяцию модулей
# + sudo aptitude install python-pymongo

class IORedirector(object):
    '''A general class for redirecting I/O to this Text widget.'''
    def __init__(self,text_area):
        self.text_area = text_area

class StdoutRedirector(IORedirector):
    '''A class for redirecting stdout to this Text widget.'''
    def write(self, str):
        try:
            str = re.sub("\r|\t", '', str)
            self.text_area['state'] = 'normal'
            self.text_area.see(END)
            self.text_area.insert(END, str)
            self.text_area['state'] = 'disabled'
            self.parent.update()
        except Exception, e:
            pass
        
class ChatSpiderGUI(object):
    """ Графическая оболочка на Tkinter для class ChatSpider """
    config_keys = ['debug']

    def __init__(self, **kwargs):
        super(ChatSpiderGUI, self).__init__()

        self.user_id = ''
        self.authorized = False
        self.activated = False
        self.RUN = False
        self.DEBUG = False
        # Номер отправляемого сообщения (если не рандом)
        self.current_messege = 0
        # Отвечает за работу поиска
        self.sRUN = False
        # Таймер
        self.runtime = 0
        # Очшее число отправленных писем
        self.total = 0
        # Счетчик текушего отправляемого сообщения в 3-м режиме
        self.count = 0

        if kwargs:
            for key in kwargs:
                if key not in self.config_keys:
                    print('Unknown option: %s' % key)
                    sys.exit(0)

                if 'debug' in kwargs:
                    self.DEBUG = kwargs['debug']
                    default_logging(grab_log='./log/grab.log', network_log='./log/network.log')

            # Отладка
            if self.DEBUG:
                for name, value in kwargs.items():
                    print (u'*** DEBUG:(%s = %s) ***') % (name, value)

        # Прочитаем файл с шаблонами и разобьем по символу "%" в список
        try:
            with open('./config/template.csv', 'rb') as csvfile:
                self.template = csvfile.read()
                self.template = self.template.split("%")

                for x in range(len(self.template)):
                    self.template[x] = re.sub("^\r\n|\r|^\n|\n$", '', self.template[x])
        except IOError as e:
            print(u'*** Не удалось открыть файл с шаблонами ***\n*** Это критическая ошибка, ВЫХОД ***')
            self.dialog_error('Ошибка!', 'Не удалось открыть файл с шаблонами.\nЭто критическая ошибка!')
            sys.exit(0)

        # Прочитаем файл с сохраненным ранее поиском мужиков
        # !!! https://docs.python.org/2/library/pickle.html
        # http://onorua.livejournal.com/27421.html
        try:
            with open('./data/online.obj', 'r') as f:
                self.online = cPickle.load(f)
        except IOError as e:
            print(u'*** Не удалось открыть сохраненный список мужчин ***')
            self.online = []
            # self.dialog_error('Ошибка!', 'Не удалось открыть сохраненный список мужчин.\nЭто критическая ошибка!')
            # sys.exit(0)

        # Проверка авторизации     
        if self.check_authorization():
            print (u'*** Авторизация прошла успешно ***')
            pass
        else:
            print (u'*** Выход из программы ***')
            sys.exit(0)

        # Проверка ключа программы
        if self.check_activations():
            print (u'*** Активация прошла успешно ***')
        else:
            print (u'*** Выход из программы ***')
            sys.exit(0)

        # Главное окно программы
        self.init_ui()
        self.quit()

    def print_logo(self):
        print "  ____       _     _ _ _"
        print " / ___| ___ | | __| | (_)_ __  _   ___  __"
        print "| |  _ / _ \| |/ _` | | | '_ \| | | \ \/ /"
        print "| |_| | (_) | | (_| | | | | | | |_| |>  <"
        print " \____|\___/|_|\__,_|_|_|_| |_|\__,_/_/\_\\"
        print "\n"

        # print " _          _     _                         __       _                "
        # print "| |__  _ __(_) __| | __ _  ___        ___  / _|     | | _____   _____ "
        # print "| '_ \| '__| |/ _` |/ _` |/ _ \_____ / _ \| |_ _____| |/ _ \ \ / / _ \\"
        # print "| |_) | |  | | (_| | (_| |  __/_____| (_) |  _|_____| | (_) \ V /  __/"
        # print "|_.__/|_|  |_|\__,_|\__, |\___|      \___/|_|       |_|\___/ \_/ \___|"
        # print "                    |___/                                             "

    def check_authorization(self, event=''):
        # Проверяем кукисы, если они плоохие логинимся
        # затем проверяем ключики
        def enent_show_hide(event=''):
            if self.show_pass.get() == True:
                self.pass_entry['show']=''
            else:
                self.pass_entry['show']='*'

        def event_return(event=''):
            self.check_authorization(self.login)

        if event != '':
            print (u'Проверка авторизации')
            # Если кукисы подгрузились продолжим
            self.user_id = self.login.get()
            self.user_password = self.password.get()

            # Нужно записать состояние галки и логин пароль в файл
            passlog = {'login':self.user_id, 'password':self.user_password, 'key':self.remember.get()}
            try:
                with open('./data/data.obj', 'w') as f:
                    cPickle.dump(passlog, f)
            except IOError as e:
                print(u'*** Не удалось сохранить учетные данные ***')
                pass

            # Если установлено запомнить меня
            if self.remember.get():

                # Попробовать загрузить кукисы
                if self.authorization():
                    # Усли гуд, вернуть тру
                    self.root_auth.destroy()
                    # Значение флага - авторизован, вернем тру для выхода из цикла
                    self.authorized = True
                    return True
                # Или снять галку с запомнить
                else:
                    # Сообщение об ошибке загрузки кукисов или пасс
                    tkMessageBox.showwarning(u'Ошибка авторизации!', u'Не могу загрузать кукисы\n Использую введенный логин и пароль.')


            if self.authorization(self.user_id, self.user_password):
                # Закрыть окно авторизации
                self.root_auth.destroy()
                # Значение флага - авторизован, вернем тру для выхода из цикла
                self.authorized = True
                return True

            # Если ни загрузка кукисов, ни авторизацыя не удалась, ошибка
            print (u'ERROR, Ошибка авторизации !')
            # Значение флага - ошибка
            self.authorized = False
            tkMessageBox.showwarning(u'Ошибка авторизации !', u'Проверьте свой логин и пароль,\nзатем повторите ввод.')
            # Вернем фолс, для красоты, вдруг еще где-то понадобится проверка
            return False

        else:
            # # !!! Проверка авторизации
            # Окно ввода ID/PASS
            # Построение окна запроса логина и пароля
            self.root_auth = Tk()
            self.root_auth.resizable(False, False)
            self.root_auth.title("Авторизация")
            self.root_auth.protocol("WM_DELETE_WINDOW", self.root_auth.destroy)
            # self.root_auth.configure(background='black')
            # self.root_auth.iconbitmap(default='./data/pacman.ico')
            # Текст лэйблов
            ttk.Label(self.root_auth, text='Логин:').grid(column=0, row=0, padx=5, pady=5, sticky=(N, W))
            ttk.Label(self.root_auth, text='Пароль:').grid(column=0, row=1, padx=5, pady=5, sticky=(N, W))
            # Поле ввода логина
            self.login = StringVar()
            id_entry = ttk.Entry(self.root_auth, width=25, textvariable=self.login)
            id_entry.grid(column=1, row=0, padx=5, pady=5, columnspan=2, sticky=(E, W))
            # Поле ввода пароля
            self.password = StringVar()
            self.pass_entry = ttk.Entry(self.root_auth, width=25, textvariable=self.password, show='*')
            self.pass_entry.grid(column=1, row=1, padx=5, pady=5, columnspan=2, sticky=(E, W))
            # Кнопки
            ttk.Button(self.root_auth, text="Выход", command=self.root_auth.destroy).grid(column=2, row=2, padx=5, pady=5, sticky=(E))
            button = ttk.Button(self.root_auth, text="Логин", command=lambda: self.check_authorization(self.login))
            button.grid(column=3, row=2, padx=5, pady=5, sticky=(E))
            # Кнопки запомнить и показать пароль
            self.remember = BooleanVar()
            self.remember.set(False)
            ttk.Checkbutton(self.root_auth, text='Запомнить меня', command='', variable=self.remember, onvalue=True, offvalue=False).grid(column=3, row=0, padx=5, pady=0, sticky=(W))
            self.show_pass = BooleanVar()
            ttk.Checkbutton(self.root_auth, text='Показать пароль', command=enent_show_hide, variable=self.show_pass, onvalue=True, offvalue=False).grid(column=3, row=1, padx=5, pady=0, sticky=(W))
            # Фокус на первое поле ввода
            button.focus()
            # Глючит на юниксах
            self.root_auth.bind('<Return>', event_return)


            # Отладка
            if self.DEBUG:
                print (u'*** DEBUG:(форма логина) ***')
                def loginWritten(*args):
                    print (u"loginWritten", self.login.get())
                def passwordWritten(*args):
                    print (u"passwordWritten", self.password.get())
                self.login.trace("w", loginWritten)
                self.password.trace("w", passwordWritten)

                # Удалить после тестирования
                # id_entry.insert(0, 'aliso4kausa1@gmail.com')
                # self.pass_entry.insert(0, 'alis25och8ka')
                # !!! только на время отладки, чтобы видеть границы виджетов
                # root_auth.configure(background='black')


            # Вспоминаем пароль
            # Прочитаем состояние прошлой сэсии
            try:
                with open('./data/data.obj', 'r') as f:
                    passlog = cPickle.load(f)

                # Если в предыдущий раз галочка стояла, вставим логин пароль
                if passlog['key'] == True and passlog['login'] != '' and passlog['password'] != '':
                    id_entry.insert(0, passlog['login'])
                    self.pass_entry.insert(0, passlog['password'])
                    self.remember.set(True)
            except IOError as e:
                print(u'*** Не удалось открыть сохраненные учетные данные  ***')
                pass

            self.root_auth.mainloop()

            # Если проверка успешна, вернем истину
            if self.authorized:
                return True
            # Или вернем ложь
            return False

    def init_ui(self):

        def redirect():
            sys.stdout = StdoutRedirector(self.text_box)

        def event_combo_selected():
            selected = self.mode.get()
            if selected == 1:
                self.statusbar['text'] = 'Все письма отправляются в\nпроизвольнмом порядке'
                self.interval_enabled.set(False)
            elif selected == 2:
                self.statusbar['text'] = 'Отправляется только то письмо,\nкоторое выбранное ниже'
                self.interval_enabled.set(False)
            elif selected == 3:
                self.statusbar['text'] = 'Отправиться перевое письмо затем\nчерез заданный интервал, последующие'
                self.interval_enabled.set(True)

        def event_cb_blacklist_selected():
            if self.blacklist_enabled.get():
                self.statusbar['text'] = 'Контактам из черного списка\nотправка осуществляться не будет'
            else:
                self.statusbar['text'] = 'Черный список отключен'

        def event_cb_timeaut_selected():
            if self.mode.get() == 3:
                if self.interval_enabled.get():
                    self.statusbar['text'] = 'Будет активирован интервал между\nмассовыми рассылками писем'
                else:
                    self.statusbar['text'] = 'Интервал отключен'

        def event_cb_sleep_selected():
            if self.sleep_enabled.get():
                self.statusbar['text'] = 'Будет активирован таймаут между\nрассылкой каждого письма'
            else:
               self.statusbar['text'] = 'Таймаут между письмами отключить нельзя'

        def event_debug_mode(event=''):
            if self.DEBUG:
                self.DEBUG = False
                self.statusbar['text'] = '*** Режим отладки отключен ***'
            else:
                self.DEBUG = True
                default_logging(grab_log='./log/grab.log', network_log='./log/network.log')
                self.statusbar['text'] = '*** Активирован режим отладки ***'

        # Главное окно
        self.parent = Tk()
        # self.parent.iconbitmap(default='./data/pacman.ico')
        self.parent.resizable(False, False)
        self.parent.title('Pack-MAN')
        self.parent.protocol("WM_DELETE_WINDOW", self.quit)

        # Панель статистики
        stats = ttk.Labelframe(self.parent, text='   СТАТИСТИКА   ', width=250, height=190).grid(column=0, row=0, padx=5, pady=5, sticky='NSWE')
        ttk.Label(stats, text='ОТПРАВЛЕНО:', font="Verdana 10 bold").place(x = 14, y = 35)
        self.Sent_lbl = ttk.Label(stats, text='0000', font="Verdana 10 bold")
        self.Sent_lbl.place(x = 155, y = 35)
        ttk.Label(stats, text='СКОРОСТЬ:', font="Verdana 10 bold").place(x = 14, y = 65)
        self.Speed_lbl = ttk.Label(stats, text='0000', font="Verdana 10 bold")
        self.Speed_lbl.place(x = 155, y = 65)
        ttk.Label(stats, text='ОСТАЛОСЬ \nВРЕМЕНИ:', font="Verdana 10 bold").place(x = 14, y = 125)
        self.TimeLast_lbl = ttk.Label(stats, text='00:00:00', font="Verdana 20 bold")
        self.TimeLast_lbl.place(x = 100, y = 125)

        # Панель настроек
        conf = ttk.Labelframe(self.parent, text='   РЕЖИМ РАБОТЫ   ', width=250, height=170).grid(column=1, row=0, padx=5, pady=5, sticky='NSWE')

        self.mode = IntVar()
        r = Radiobutton(self.parent, text='СЛУЧАЙНО', variable=self.mode, command=event_combo_selected, value=1)
        r.place(x=280, y=25)
        # r.select()
        Radiobutton(self.parent, text='ОДНО ПИСЬМО', variable=self.mode, command=event_combo_selected, value=2).place(x=280, y=45)
        # Выбор единичного письма
        self.messege = StringVar()
        self.messege.set(self.template[0])
        messege_box = ttk.Combobox(conf, width=24, textvariable=self.messege)
        messege_box['values'] = self.template
        messege_box.place(x=305, y =65)
        b = Radiobutton(self.parent, text='ПО ПОРЯДКУ', variable=self.mode, command=event_combo_selected, value=3)
        b.place(x=280, y=90)
        b.select()
        # Включить черныйсписок
        self.blacklist_enabled = BooleanVar()
        ttk.Checkbutton(conf, text='ЧЕРНЫЙ СПИСОК', command=event_cb_blacklist_selected, variable=self.blacklist_enabled, onvalue=True, offvalue=False).place(x=282, y =115)
        # Установим кнопку в Тру
        self.blacklist_enabled.set(True)

        # Включить таймаут
        self.interval_enabled = BooleanVar()
        self.interval_enabled.set(True)
        ttk.Checkbutton(conf, text='ИНТЕРВАЛ (МИН.)', command=event_cb_timeaut_selected, variable=self.interval_enabled, onvalue=True, offvalue=False).place(x=282, y =140)
        self.interval = IntVar()
        self.interval.set(1)
        timeaut_box = ttk.Combobox(conf, width=6, textvariable=self.interval)
        timeaut_box['values'] = range(5, 65, 5)
        timeaut_box.place(x=440, y =140)

        # Включить слип
        self.sleep_enabled = BooleanVar()
        self.sleep_enabled.set(True)
        ttk.Checkbutton(conf, text='ТАЙМАУТ (СЕК.)', command=event_cb_sleep_selected, variable=self.sleep_enabled, onvalue=True, offvalue=False).place(x=282, y =165)
        self.sleep = DoubleVar()
        self.sleep.set(1)
        timeaut_box = ttk.Combobox(conf, width=6, textvariable=self.sleep)
        timeaut_box['values'] = range(5, 65, 5)
        timeaut_box.place(x=440, y =165)

        # Журнал работы
        self.text_box = Text(self.parent, wrap='word', height = 11, width=50)
        self.text_box.grid(column=0, row=1, padx=5, pady=0, columnspan=2, sticky='NSWE')
        scroll = ttk.Scrollbar(self.parent, orient=VERTICAL, command=self.text_box.yview)
        scroll.grid(column=1, row=1, padx=5, pady=0, sticky='NSE')
        self.text_box['yscrollcommand'] = scroll.set

        # кнопка поиск
        self.search_btn = ttk.Button(self.parent, text='ПОИСК', command=self.search)
        self.search_btn.grid(column=1, row=2, padx=25, pady=3, sticky='SW')

        # кнопка старт/стоп
        self.Run_btn = ttk.Button(self.parent, text='СТАРТ', command=self.start)
        self.Run_btn.grid(column=1, row=2, padx=25, pady=3, sticky='SE')

        self.statusbar = Label(self.parent, text='Здесь отображаются подсказки ...', height=2, width=30, anchor='center')
        self.statusbar.grid(column=0, row=2, padx=5, pady=3, sticky='NSWE')

        # Фокус на Пуск
        self.Run_btn.focus()
        self.parent.bind('<Return>', self.start)
        messege_box.bind('<<ComboboxSelected>>', self.set_messege)
        self.parent.bind('<Control-backslash>', event_debug_mode)

        Thread(target=redirect).start()

        self.print_logo()
        self.parent.mainloop()

    def set_messege(self, event):
            i = self.messege.get()
            self.current_messege = self.template.index(i)
            # Отладка
            if self.DEBUG:
                print (u'*** DEBUG:(%s) ***') % self.current_messege

    def start(self, event=''):

        def seconds_to_hms(seconds):
            return time.strftime('%H:%M:%S', time.gmtime(seconds))

        def tick():

            if self.RUN:
                # Время задержки м/у сообщениями
                sleep = int(self.sleep.get())
                # Запустить себя в цикле
                self.parent.after(1000, tick)
                # Получитт текущее число отправленных
                total = self.bot.get_total()
                # SPEED  TIME
                # speed = total / (time.clock() - self.start_time)
                speed = sleep  # Число сообщений
                # сколько займет рассылка списка в секундах
                runtime = len(self.online) * sleep * 3
                # Поправка на ветер
                runtime += 150
                endtime = self.start_time + runtime

                # Если мод3
                if self.mode.get() == 3:
                    if self.interval_enabled.get():
                        interval = self.interval.get() * 60 # в сек
                    else:
                        interval = 60
                    # Сложить текущее число отправленных и до этого
                    total = self.total + self.bot.get_total()

                    # timeaut = interval * (len(self.template) - self.count) * 60
                    #5*4=20m или 300 * 4 = 1200
                    fulltimeauttime = interval * len(self.template) -1 # время задержек между рассылками
                    # 176/12=14 или 176 * 5 = 880
                    # время задержек слипов между письмами # плюс Х2 на имитацию рандомной отправки
                    fullsleeptime = len(self.online) * sleep * 3
                    # 14+20 = 34м или 880+ 1200 = 2080 /60 = 34м
                    fulltime = fulltimeauttime + fullsleeptime # время слипов + время таймаутов в сек.
                    endtime = self.start_time + fulltime # начало + все время

                lasttime = endtime - time.clock()

                # Отладка
                if self.DEBUG:
                    print 'speed:', speed, 'total:', total, 'runtime:', runtime, 'self.start_time:', self.start_time, 'endtime:', endtime, 'lasttime:', lasttime
                    print 'self.total', self.total, 'self.bot.get_total()', self.bot.get_total()
                    # print 'lasttime', lasttime, 'endtime', endtime, 'time.clock()', time.clock()

                # время_работы = всего / скорость (150шт / 15шт.сек. = 10сек)
                # конец = время_начала + время_работы
                # осталось = конец - тек_время
                if speed: # на случай если я при отладке введу ноль
                    speed = 60 / speed # перевод в минуты

                self.Sent_lbl['text'] = str(total) + ' шт.'
                self.Speed_lbl['text'] = str(speed) + ' шт./мин.'
                # Чтобы не было 23:59:59
                if lasttime > 0:
                    self.TimeLast_lbl['text'] = seconds_to_hms(lasttime)
                
        def invite():
            # Запуск рассылки
            # На время отладки разрешим быстрый режим
            if self.DEBUG:
                sleep = self.sleep.get()
            else:
                if self.sleep.get() >= 1:
                    sleep = self.sleep.get()
                else:
                    self.sleep.set(5)
                    sleep = 5

            # Имитация случайной отправки
            if not self.DEBUG:
                sleep = sleep + choice(range(0, 3))
            
            mode = self.mode.get()
            if mode == 1:
                bot = ChatSpiderInvite(random=True, blacklist=self.blacklist_enabled.get(), sleep=sleep, debug=self.DEBUG)
                
            elif mode == 2:
                bot = ChatSpiderInvite(messege=self.current_messege, blacklist=self.blacklist_enabled.get(), sleep=sleep, debug=self.DEBUG)
                
            elif mode == 3:
                bot = ChatSpiderInvite(messege=self.count, blacklist=self.blacklist_enabled.get(), sleep=sleep, debug=self.DEBUG)
            ###################
            self.bot = bot
            bot.run()
            
            # Плавный останов
            # иначе бот убивается по кнопке и мы ничего от него больше не хотим
            if self.RUN:
                # До выхода получаем общее число отправленных и запоминаем
                self.total = self.total + bot.get_total()
                bot.quit()

                # По окончанию работы, если 3-й режим
                if self.mode.get() == 3:
                    # Повтор итерации для 3-го режима
                    self.count += 1
                    # -----------------------------------
                    # Пока не дошли до последнего сообщения
                    if self.count < len(self.template):
                        # Прверим и посчитаем интервал
                        if self.interval_enabled.get():
                            interval = self.interval.get()
                        else:
                            interval = 1
                        # Перевести в секунды
                        timeaut = interval * 1000 * 60
                        # Перевести в минутыдля принта
                        minutes = timeaut/60/1000
                        # self.text_area.delete(1.0, END)
                        print '\n'*6+'- - - - - - - - - - - - - - - - - - - -'
                        print ('*** Рассылка сообщения № %d, будет запущена через %d мин. ***\n') % (self.count, minutes)
                        print self.template[self.count][0:100]
                        print '- - - - - - - - - - - - - - - - - - - -'
                        # Перезапустим рассылку
                        self.job = self.parent.after(timeaut, hard_job)
                    # Если достигли последгнего сообщения
                    else:
                        print '\n- - - - - - - - - - - - - - - - - - - -\n| ГОТОВО\n- - - - - - - - - - - - - - - - - - - -'
                        self.Run_btn["text"] = "СТАРТ"
                        self.TimeLast_lbl['text'] = '00:00:00'
                        self.RUN = False
                        self.count = 0
                        # Удалить объект
                        del self.bot
                    # ------------------------------------
                else: # если другой режим, просто выход
                    print '\n- - - - - - - - - - - - - - - - - - - -\n| ГОТОВО\n- - - - - - - - - - - - - - - - - - - -'
                    self.Run_btn["text"] = "СТАРТ"
                    self.TimeLast_lbl['text'] = '00:00:00'
                    self.RUN = False
                    # Удалить объект
                    del self.bot

        def hard_job():
            # Запуск рабочего процесса
            self.job = self.parent.after(1000, tick)
            Thread(target=invite).start()

        # Вхождение 
        if self.RUN == False:
            # Проверка есть ли список мужчин
            if len(self.online) == 0:
                self.dialog_error('Внимание!', 'Cписок мужчин пуст.\nСначало сделайте поиск!')
            else:
                # Проверка работают ли фоновые задичи
                self.Run_btn["text"] = "/СТОП/"
                self.RUN = True
                # !!! Установить счетчик времени
                self.start_time = time.clock()

                # Сброс счетчиков до начала работы
                self.Sent_lbl['text'] = '0 шт.'
                self.Speed_lbl['text'] = '0 шт./мин.'
                self.TimeLast_lbl['text'] = '00:00:00'
                # Сбросить счетчик отправленных
                self.total = 0
                # Поехали
                hard_job()
            
        else:
            self.RUN = False
            self.bot.quit()
            # Удалить объект
            del self.bot
            self.Run_btn["text"] = "СТАРТ"
            self.parent.after_cancel(self.job)
        # Сначало нужно выполнить "ПОИСК"
        # tkMessageBox.showerror(u'Ошибка работы', u'Сначало нужно выполнить "ПОИСК"')

    def quit(self):
        # Выход из программы, остановка спайдера
        if self.RUN:
            self.bot.quit()
            # Удалить объект
            del self.bot
            self.parent.after_cancel(self.job)
            self.RUN = False
            self.Run_btn["text"] = "СТАРТ"

        if self.sRUN:
            self.search_bot.quit()
            self.sRUN = False
            self.search_btn["text"] = "ПОИСК"

        self.parent.destroy()
        sys.stdout = sys.__stdout__
        print 'Quit'
        sys.exit(0)

    def search(self):

        self.TimeLast_lbl['text'] = '00:00:00'
        self.Sent_lbl['text'] = '0000'
        self.Speed_lbl['text'] = '0000'

        def sbot():
            self.search_bot = ChatSpiderSearch(debug=self.DEBUG)
            self.search_bot.run()

            if self.sRUN:
                self.search_bot.sawe_result()
                self.search_bot.quit()
                self.search_btn["text"] = "ПОИСК"
                self.sRUN = False
                # Перечитать список мужиков
                try:
                    with open('./data/online.obj', 'r') as f:
                        self.online = cPickle.load(f)
                except IOError as e:
                    print(u'*** Не удалось открыть сохраненный список мужчин ***')
                    pass

        if self.sRUN == False:
            self.search_btn["text"] = "/СТОП/"
            self.sRUN = True
            Thread(target=sbot).start()
        else:
            self.search_btn["text"] = "ПОИСК"
            self.sRUN = False
            self.search_bot.quit()

    def activations(self):
        # ПРОЦЕСС АКТИВАЦИИ
        # Здесь делаем проверку лицензии
        # если файл активации есть и он верный, то продолжаем
        # (клиенту отправляется код активации ввиде PGP сообщеия, которое состоит из id и срока жизни ключа)
        # http://www.saltycrane.com/blog/2011/10/python-gnupg-gpg-example/
        # https://pythonhosted.org/python-gnupg/
        # Далее сохраним полученный ключь в файл
        # и перед каждым запуском будем открывать его и проверять ID и срок жизни
        self.root_activate = Tk()
        self.root_activate.title("Активация")
        self.root_activate.protocol("WM_DELETE_WINDOW", self.root_activate.destroy)
        # self.root_activate.iconbitmap(default='./data/pacman.ico')
        mainframe = ttk.Frame(self.root_activate, padding="3 3 12 12").grid(column=0, row=0, sticky=(N, W, E, S))
        # Поле ввода ключа
        self.key_box = Text(mainframe, font='Verdana 10', wrap='word', width=35, height=12)
        self.key_box.insert('1.0', 'Пожалуйста введите ключ активации и помогите бедному Кенни насобирать на домик у озера ...')
        self.key_box.grid(column=1, row=1, sticky=(W, E))
        # Картинка
        logo = PhotoImage(file="./data/kenny.gif")
        w1 = Label(mainframe, image=logo).grid(column=2, row=1, sticky=(N, E))
        # Кнопки
        ttk.Button(mainframe, text="Выход", command=self.root_activate.destroy).grid(column=1, row=2, padx=120, pady=5, columnspan=2, sticky=(S, E))
        ttk.Button(mainframe, text="Активировать", command=lambda:self.check_activations(self.key_box.get('1.0', 'end'))).grid(column=2, row=2, padx=5, pady=5, sticky=(S, E))
        # Фокус на ф-ю активации
        self.key_box.focus()
        self.root_activate.mainloop()

    def check_activations(self, event=''):
        # Проверка ключа активации
        # Из формы мыполучаем именно юникод, его и будем сверять
        print (u'*** Проверим лицензию ...***')
        # Подготовим строки для проверки
        enter_key = unicode(event)
        hash_key = unicode(hashlib.md5(self.user_id).hexdigest()+'\n')

        if event != '':
            # Если ф-я вызвана с параметрами (не из основной ф-и а из диалога)
            # тоесть чтение сохраненного ключа не удалась
            # Нужно взять из event ключь, проверить, записать в файл и что-то вернуть

            # Отладка
            if self.DEBUG:
                print (u'*** DEBUG:(enter_key) ***', enter_key)

            if enter_key == hash_key:
                print (u'Активировация прошла успешно :)')
                tkMessageBox.showinfo(u'Поздравляю !', u'Активировация прошла успешно.')
            else:
                print (u'Не правильный код активации !')
                tkMessageBox.showerror(u'Ошибка активации !', u'Не правильный код активации !')
                self.root_activate.destroy()
                # Вернем в вызывающую ф-ю отказ
                return False
                # Полный выход
                # sys.exit(0)

            # Отправку id и хостнейм на сервер
            datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            grab = Grab(timeout=50, connect_timeout=25, url='http://sysadmin.1cps.ru/packman/activate.php')
            grab.setup(post = {'user_name': self.user_id, 'key': enter_key, 'datetime': datetime})

            # Сохранить в файл
            try:
                with open('./data/keys.bin', 'w') as f:
                    self.keys_file.append(enter_key)
                    cPickle.dump(self.keys_file, f)
            except IOError as e:
                print(u'*** Не удалось сохранить файл лицензии ***')
                pass

            # # Отладка
            if self.DEBUG:
                grab.setup(log_file='./log/activations.html', verbose_logging='True', debug_post='True')
                logging.basicConfig(level=logging.DEBUG)

            grab.request()
            # Закрыть окно
            self.root_activate.destroy()
            # Вернем в вызывающую ф-ю True
            # особо в этом смысла нет, т,к это только гуя и там нет обработчиков
            return True
            # Полный выход
            # sys.exit(0)
        else:
            # Ф-я вызвана из главного цикла программы
            # подразумевается, что ключь должен быть сохранен, проверим его
            # если он не подходит, вызвать диалоговое окно ввода ключа, который
            # вызовет эту же ф-ю с параметром "ключь". Мы попадем в if выше.

            # Для начала откроем файл(сохраненный обьект)
            try:
                with open('./data/keys.bin', 'r') as k:
                    self.keys_file = cPickle.load(k)
            except IOError as e:
                print(u'*** Не удалось найти файл лицензии ***')
                self.keys_file = []
                self.activations()
                sys.exit(0)
            # Затем проверим все хранящиеся ключи
            for key in self.keys_file:
                # перебор ключей, при наличии и сверка с полученным

                # Отладка
                if self.DEBUG:
                    print(u'*** DEBUG:(hash_key, key) ***', hash_key, key, hash_key == key )

                if hash_key == key:
                    print(u'*** Все в порядке ***')
                    return True
             
            # Если ключь не найден, вернем False
            print(u'*** Не удалось найти совместимый ключ ***')
            self.activations()
            return False

    def authorization(self, login='', password=''):
        # Сеттер, задает ID / PASS
        # При запуске без параметров, грузит кукисы и проверяет авторозацию
        # если кукис отсутствует или битый, возвращает False.
        # При запуске с параметрами, грузаит кукисы, проверяет авторизацию и
        # если кукис отсутствует или битый, логинится по новой, возвращает True, в случае успеха.
        login = unicode(login)
        passwd = unicode(password)

        # Для начала нужно создать обьект граб
        # Пример создания и настройки граб обьекта:
        # g = Grab(timeout=5, connect_timeout=1, url='http://example.com')
        # grab.setup(url=.., cookies=..., post=....)
        # yield Task('some-name', grab=grab)
        grab = Grab(timeout=50, connect_timeout=25, url='https://www.bridge-of-love.com/login.html')

        # Отладка
        if self.DEBUG:
            grab.setup(log_file='./log/authorization.html', verbose_logging='True', debug_post='True')
            logging.basicConfig(level=logging.DEBUG)

            print (u'*** DEBUG:(set_auth) ***', login, passwd)

        # Затемзалогинится на сайте
        # Если указано "запомнить меня" и ф-я запущена без параметров
        if login == '' and password =='':
            try:
                print(u'*** Загружаю кукисы ***')
                grab.cookies.load_from_file('./data/cookies.json')
            except IOError as e:
                print(u'*** Не удалось загрузить кукисы ***')
        else:
            # Заполняем запрос полученными данными 
            post = {'user_name': login, 'password': passwd, 'remember': 'on', 'ret_url': ''}
            grab.setup(post=post)

        # Отправка формы // асинхронный запрос // но деваться не куда
        grab.request()

        # Проверка авторизации
        en = u'System message - Login successful!- Powered by Dating co.'
        ru = u'Системное сообщение - Вы вошли успешно!- Powered by Dating co.'
        already_en = u'System message - Login already!- Powered by Dating co.'
        already_ru = u'Системное сообщение - Вы уже в системе!- Powered by Dating co.'
        # Если ответ содержит один из ответов, продолжаем работу
        if grab.doc.text_search(en) or grab.doc.text_search(ru):
            print (u'*** '+ru+'*** ')
            pass
        elif grab.doc.text_search(already_en) or grab.doc.text_search(already_ru):
            print (u'*** '+already_ru+'*** ')
            pass
        else:
            print (u'*** ERROR, авторизация не удалась ***')
            return False
            sys.exit(0)

        # Сохраню кукисы
        print (u'*** Сохраняю кукисы ***')
        grab.cookies.save_to_file('./data/cookies.json')
        # Сохраним имя девушки
        try:
            self.username = grab.doc.select('//div[contains(@class, "f_l g_text")]//strong').text()
        except Exception, e:
            self.username = 'User'
            pass

        # Отчитаться об успешной авторизации
        return True

    def dialog_error(self,title, message):
        Tk().withdraw()
        tkMessageBox.showerror(title=title, message=message)

class ChatSpiderInvite(Spider):
    """ ChatSpiderSearch отвечает за функции отправки и ведение статистики """
    # Список страниц, с которых Spider начнёт работу
    initial_urls = ['https://www.bridge-of-love.com/']
    config_keys = ['messege', 'random', 'blacklist', 'debug', 'sleep']

    def __init__(self, **kwargs):
        super(ChatSpiderInvite, self).__init__()
        # Переменная отвечает разрешена ли работа в текущий момент
        self.RUN = True
        # Включить отладку?
        self.DEBUG = False
        # Задать "случайное письмо"
        self.template_random = False
        # Задать какое письмо отправлять
        self.current_messege = 0
        # Этот счётчик будем использовать для отправленных инвайтов
        self.result_counter = 0
        # Включить блэклист
        self.blacklist_enabled = False
        self.blacklist = []
        # Таймаут
        self.sleep = 0

        if kwargs:
            for key in kwargs:
                if key not in self.config_keys:
                    print('Unknown option: %s' % key)
                    sys.exit(0)
            if self.config_keys[0] in kwargs and self.config_keys[1] in kwargs:
                print(u'Нельзя использовать ключи messege и random вместе')
                sys.exit(0)

            if 'random' in kwargs:
                self.template_random = kwargs['random']

            if 'messege' in kwargs:
                self.current_messege = kwargs['messege']

            if 'debug' in kwargs:
                self.DEBUG = kwargs['debug']

            if 'blacklist' in kwargs:
                self.blacklist_enabled = kwargs['blacklist']

            if 'sleep' in kwargs:
                self.sleep = kwargs['sleep']

            # Отладка
            if self.DEBUG:
                for name, value in kwargs.items():
                    print (u'*** DEBUG:(%s = %s) ***') % (name, value)
                    print (u'*** DEBUG:(self.blacklist_enabled = %s) ***') % self.blacklist_enabled

    def create_grab_instance(self, **kwargs):
        # Настройки граба
        g = super(ChatSpiderInvite, self).create_grab_instance(**kwargs)
        g.setup(timeout=50, connect_timeout=25)
        try:
            g.cookies.load_from_file('./data/cookies.json')
        except Exception, e:
            print (u'*** ERROR! ***\n*** Критическая ошибка, не удалось загрузить кукисы ***')
            sys.exit()
        # Отладка
        if self.DEBUG:
            g.setup(log_file='./log/log.html', verbose_logging='True')
            # g.setup(log_dir='./log', debug_post='True')
            logging.basicConfig(level=logging.DEBUG)
        return g

    def prepare(self):
        # Подготовим файл для записи результатов
        # Функция prepare вызываетя один раз перед началом
        # работы парсера
        # Этот файл будем использовать для хранения шаблонных фраз
        # разделять шаблоныбудем по спецсимволу или по трем переносам строки
        # https://docs.python.org/2/library/csv.html

        # Прочитаем файл с шаблонами и разобьем по символу "%" в список
        try:
            with open('./config/template.csv', 'rb') as csvfile:
                self.template = csvfile.read()
                self.template = self.template.split("%")
                for x in range(len(self.template)):
                    self.template[x] = re.sub("^\r\n|\r|^\n|\n$", '', self.template[x])
        except IOError as e:
            print(u'*** Не удалось открыть файл с шаблонами ***')
            print(u'*** Это критическая ошибка, ВЫХОД ***')
            sys.exit(0)

        # Прочитаем блэклист и разобьем по символу "," в список
        try:
            if self.blacklist_enabled:
                with open('./config/blacklist.csv', 'rb') as csvfile:
                    l = csvfile.read()
                    self.blacklist = l.split(',')
                    for x in range(len(self.blacklist)):
                        self.blacklist[x] = re.sub("\D", '', self.blacklist[x])
                # Отладка
                if self.DEBUG:
                    print (u'*** DEBUG:(blacklist.csv) ***', len(self.blacklist))
                    print (u'*** DEBUG:(blacklist.csv) ***', self.blacklist)

        except IOError as e:
            print(u'*** Не удалось открыть блэклист ***')
            pass

        # Прочитаем файл с сохраненным ранее поиском мужиков
        # !!! https://docs.python.org/2/library/pickle.html
        # http://onorua.livejournal.com/27421.html
        try:
            with open('./data/online.obj', 'r') as f:
                self.online = cPickle.load(f)
                # !!! Преобразовать в словарь
        except IOError as e:
            print(u'*** Не удалось открыть сохраненный список мужчин ***')
            print(u'*** Это критическая ошибка, ВЫХОД ***')
            sys.exit(0)

        # Отладка
        if self.DEBUG:
            print (u'*** DEBUG:(template.csv) ***', len(self.template))
            print (u'*** DEBUG:(online.csv) ***', len(self.online))

        # Этот файл будем использовать для логирования отправленных инвайтов
        self.result_file = csv.writer(open('./config/result.csv', 'wb'))

    def task_initial(self, grab, task):
        # Если кнопка не нажата, переход сразу к рассылке
        print (u'*** Загружен список из %s-ти мужчин ***\n- - - - - - - - - - - - - - - - - - - -\n') % len(self.online)
        # Запускаем подготовку к рассылке
        # Переход на страницу чата, для получения HASH, IDS
        grab.setup(url='https://www.bridge-of-love.com/index.php?app=chat&user_id=0&send_invite=1#')
        yield Task('send', grab=grab)

    def task_send(self, grab, task):
        # Переход на страницу чата, для получения HASH, IDS
        # Генератор выполняющий процесс рассылки

        # Найти HASH сэссии
        _hash = grab.doc.rex_text("HASH: '(.*)',")
        # Найти IDS сэссии
        _ids = grab.doc.rex_text("IDS: '(.*)',")

        # Тут пока переменная RUN истина, из словаря выбираются все мужики, формируются задания и отдаются в очередь. Все.
        i = 0
        while self.RUN:
            # Нужно прочитать шаблон сообщения из словаря
            # Если активна кнопка "случайное письмо"

            if self.template_random:
                message = str(choice(self.template))
            # Если мы запросили слать определенное письмо
            else:
                if self.current_messege < len(self.template):
                    message = self.template[self.current_messege]
                else:
                    print(u'\n*** Выход за пределы списка ***\n')
                    print self.current_messege ,len(self.template)
                    sys.exit(0)

            # Извлечение пары ID:NAME
            try:
                item = self.online.popitem()
            except KeyError as e:
                # print(u'\n*** Список мужчин закончился ***\n')
                RUN = False
                sys.exit(0)

            # Проверка, еслив черном списке, то pass
            if item[0] in self.blacklist:
                try:
                    print ('*** Отправка сообщения для %s : %s "ОТМЕНЕНА" ***') % (item[0].encode('utf8'), item[1].encode('utf8'))
                except Exception, e:
                    pass
            else:
                # Вставим вместо макроса имя
                if message.find('$name') != -1:
                    message = message.replace('$name', item[1])

                # !!! Подготовка POST запроса
                url = 'https://www.bridge-of-love.com/index.php?app=ajax&act=send_message'
                post = {'chat_id':'', 'message':message, 'user_id':item[0],'hash':_hash,'ids':_ids}

                # Отладка
                if self.DEBUG:
                    # print (u'*** DEBUG:(post) ***', post)
                    grab.setup(url=url)
                else:
                    # POST !!! # grab.setup(url=url, post=post)
                    pass

                i += 1
                delay = self.sleep * i
                # Запуск обработчика выполняющего рассылку
                yield Task('invite', grab=grab, item=item, delay=delay)

    def task_invite(self, grab, task):
        # Эта функция, получает готовый обьект граб отправляет инвайт
        # и пишет в файл, кому отправила
        # print (u'*** Отправка сообщения № %d для %s  %s ***') % (self.current_messege, task.item[1].encode('utf8'), task.item[0].encode('utf8'))

        # try:
        #     print ('*** Отправка сообщения № %d для %s  %s ***') % (self.current_messege, task.item[1].encode('utf8'), task.item[0].encode('utf8'))
        # except Exception, e:
        #     pass
        # Также можно обработать ответ и что то проверить
        # Вот ответ в json: [{"type":9,"data":{"message":"Hello kitty","userid":221911,"timestamp":"17:28:16"},"time":1444573696}]
        # import json
        # r=grab.response.body
        # r=r[1:-1]
        # d=json.loads(r)
        # Ну ты понял ...

        # Теперь нужно сохранить результат.
        # print (u'\n*** Сохраним результаты рассылки ***\n')
        self.result_file.writerow([
            task.item[0].encode('utf8'),
            task.item[1].encode('utf8')
        ])
        # Не забудем увеличить счётчик отправленных инвайтов
        self.result_counter += 1

    def set_random(self, param):
        # Задать "случайное письмо"
        print(u'*** Опция "случайное письмо"" активна ***')
        self.template_random = bool(param)

    def get_total(self):
        # print(u'\n\n*** Всего отправлено %s приглашений ***\n\n') % self.result_counter
        return self.result_counter

    def get_count(self):
        # Вернуть планируемое количество отправляемых сообщений
        try:
            return len(self.online)
        except Exception, e:
            return 0

    def set_current_messege(self, args):
        # Задать какое письмо отправлять
        self.current_messege = int(args)

    def quit(self):
        # Использовать только для аварийной остановки по кнопке
        # !!! Не дожидается выполнения всех тасков
        print (u'*** Завершение работы ***')
        self.RUN = False
        self.work_allowed = False
        self.result_counter = 0

    def task_send_fallback(self, task):
        # Отловить ошибочные задания
        print 'task_send_fallback'

    def task_invite_fallback(self, task):
        # Отловить ошибочные задания
        print 'Вот блин, что то с сетью !?'

class ChatSpiderSearch(Spider):
    """ ChatSpiderSearch отвечает за функции поиска и отработки результатов """
    # Список страниц, с которых Spider начнёт работу
    # для каждого адреса в этом списке будет сгенерировано
    # задание с именем initial
    initial_urls = ['https://www.bridge-of-love.com/login.html']
    config_keys = ['debug']

    def __init__(self, **kwargs):
        super(ChatSpiderSearch, self).__init__()
        # Переменная отвечает разрешена ли работа в текущий момент
        self.RUN = True
        # Ищем ли мы новые страницы или дошли до последней
        self.parse_run = True
        # Включить отладку?
        self.DEBUG = False

        if kwargs:
            for key in kwargs:
                if key not in self.config_keys:
                    print('Unknown option: %s' % key)
                    sys.exit(0)

            if 'debug' in kwargs:
                self.DEBUG = kwargs['debug']

    def create_grab_instance(self, **kwargs):
        # Настройки граба
        g = super(ChatSpiderSearch, self).create_grab_instance(**kwargs)
        g.setup(timeout=50, connect_timeout=25)
        try:
            g.cookies.load_from_file('./data/cookies.json')
        except Exception, e:
            print (u'*** ERROR! ***\n*** Критическая ошибка, не удалось загрузить кукисы ***')
            sys.exit()
        # Отладка
        if self.DEBUG:
            g.setup(log_file='./log/log.html', verbose_logging='True')
            # g.setup(log_dir='./log', debug_post='True')
            logging.basicConfig(level=logging.DEBUG)
        return g

    def prepare(self):
        # Список куда сохраним найденных мужиков
        self.online = {}

    def task_initial(self, grab, task):
        # Это функция-обработчик для заданий с именем initial
        # т.е. для тех заданий, что были созданы для
        # адреов указанных в self.initial_urls

        # Проверка авторизации
        already_en = u'System message - Login already!- Powered by Dating co.'
        already_ru = u'Системное сообщение - Вы уже в системе!- Powered by Dating co.'

        # Если ответ содержит один из ответов, продолжаем работу
        if grab.doc.text_search(already_en) or grab.doc.text_search(already_ru):
            print (u'*** '+already_ru+'*** ')
            pass
        else:
            print (u'\n*** Вы не авторизованы ***\n')
            sys.exit(0)

        # Поехали, запуск двигателей ...
        print (u'\n*** Запускаю поиск мужчин онлайн ***\n')
        grab.setup(url='https://www.bridge-of-love.com/index.php?app=my_man&online=yes')
        yield Task('search', grab=grab)

    def task_search(self, grab, task):
        # Поиск остановитьможно, но смысла в ПАУЗЕ нет, т.к нам нужны только онлайн контакты
        print (u'*** Открываю старницу "Мужчины онлайн" ***')
        # Здесь делаем поиск количества страниц и переход на кадую
        # for link in grab.doc.select('//div[contains(@class, "page_nav f_l")]//a/@href')
        # Переход на каждую страницу и запуск выборки ID NAME
        # При достижении последней в списке страницы, выполнить +1 до тех пор
        # пока не откроется пустая страница <h2 class="no_member">Нет данных!</h2> / <h2 class="no_member">No members!</h2>

        # Найдем последнюю ссылку на последнюю страницу на этой странице
        max = 0
        for link in grab.doc.select('//div[contains(@class, "page_nav f_l")]//a/@href'):
            t = link.html()
            p = 'index.php?app=my_man&online=yes&page='
            if p in t:
                m = int(re.search('&page=(\d*)',t).group(1))
                if m > max:
                    max = m
        # Перейдем по ней и выясним, действительно ли она последняя
        url = 'https://www.bridge-of-love.com/index.php?app=my_man&online=yes&page=' + str(max)
        grab.setup(url=url)
        # Для этого запустим новый таск
        yield Task('last_page', grab=grab)

    def task_last_page(self, grab, task):
        # Выяснить, действительно ли она последняя
        max = 0
        for link in grab.doc.select('//div[contains(@class, "page_nav f_l")]//a/@href'):
            t = link.html()
            p = 'index.php?app=my_man&online=yes&page='
            if p in t:
                m = int(re.search('&page=(\d*)', t).group(1))
                if m > max:
                    max = m

        print (u'\n*** Найдено %d страниц ***\n') % max

        # Отладка
        if self.DEBUG:
            print (u'\n\n*** DEBUG:(last_page) ***', max)

        for x in range(max+1):
            # Готовим ссылку1
            url = 'https://www.bridge-of-love.com/index.php?app=my_man&online=yes&page=' + str(x)
            grab.setup(url=url)

            # Отладка
            if self.DEBUG:
                print (u'*** DEBUG:(url gen) ***', url)

            # Запуск задания на парсинг
            yield Task('parse', grab=grab, page=x)

    def task_parse(self, grab, task):
        """ Здесь будет осуществляться перебор страиц и запуск обработчика для  каждой """

        # !!! Поверка не является ли страница последней
        # пока не откроется пустая страница <h2 class="no_member">Нет данных!</h2> / <h2 class="no_member">No members!</h2>
        # grab.doc.select('//h2[contains(@class, "no_member")]')
        print (u'*** Обработка страницы № %d ***') % task.page

        # Если работаем, иначе прервать цикл
        if not self.RUN:
            sys.exit(0)

        if grab.doc.text_search(u'Нет данных!') or grab.doc.text_search(u'No members!'):
            print (u'\n*** Последняя страница поиска ***\n')
            # Остановить переход на след страницу и выйти из таска
            # !!! Может тут добавить паузу на выполнение всех тасков
            self.parse_run = False
            sys.exit(0)

        for elem in grab.doc.select('//ul[contains(@class, "matrix_list1")]//div[contains(@class, "user_info_right f_l")]'):
            # Извлекаем имя и id из полученной страници поиска
            id = elem.text().split(' ID')[1].split(' ')[1]
            name = elem.text().split(' ID')[0]
            # Сохранить полученые результаты в словарь
            self.online[id] = name

            # Отладка
            if self.DEBUG:
                print (u'*** DEBUG:(name, id) ***', name.encode('utf8'), id)

    def sawe_result(self):
        # Сохранить список мужчин в файл для дальнейшей работы
        # !!! Может тут добавить паузу на выполнение всех тасков
        print (u'\n*** Сохраняю список мужчин ***\n')

        # Отладка
        if self.DEBUG:
            self.online['0000000000'] = 'GOLD'
            print (u'*** DEBUG:(сохранить ID:0000000000, GOLD) ***', self.online['0000000000'])

        try:
            with open('./data/online.obj', 'w') as f:
                cPickle.dump(self.online, f)
        except IOError as e:
            print(u'*** Не удалось сохранить результаты ***')
            pass

    def set_debug(self, param):
        # Включить отладку?
        self.DEBUG = bool(param)

    def quit(self):
        # Использовать только для аварийной остановки по кнопке
        # !!! Не дожидается выполнения всех тасков
        print (u'*** Завершение работы ***')
        self.work_allowed = False
        self.RUN = False

    def task_search_fallback(self, task):
        # Отловить ошибочные задания
        print 'task_search_fallback'

    def task_last_page_fallback(self, task):
        # Отловить ошибочные задания
        print 'task_last_page_fallback'

    def task_parse_fallback(self, task):
        # Отловить ошибочные задания
        print 'Вот блин, что то с сетью !?'

if __name__ == '__main__':
    # Запуск ChatSpiderGUI
    gui = ChatSpiderGUI(debug=False)
    # bot = ChatSpiderInvite(random=True, blacklist=True, sleep=1, debug=True).run()