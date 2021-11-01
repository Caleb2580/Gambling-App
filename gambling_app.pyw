from PyQt5.QtCore import QSize, QRect, QPropertyAnimation, QTimeLine, QTimer, QThread
from PyQt5.QtGui import QIcon, QPixmap, QTransform, QFont, QCursor
import functools
from time import sleep
import random
from random import randint
import threading

from PyQt5.QtWidgets import QSlider, QTableWidgetItem, QGraphicsOpacityEffect
import requests

import mainwindow
from mainwindow import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

import time
import os
import json
import socket


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.setupUi(self)

        self.pre_setup()

        self.username = ''
        self.balance = 0.0
        self.logged_in = False

        # Crash stuff
        self.crash_data = {'check': True}
        self.next_time_crash = 0
        self.crash_multiplier = 1.0
        self.crash_bet = 0
        self.cashed_out = False
        self.crash_rounds = []

        self.url = 'http://104.237.133.98:8000/'
        # self.url = 'http://127.0.0.1:8000/'

    def crash_button_pressed(self):
        self.hide_everything()
        self.crash_frame.show()

    def login_pressed(self):
        self.login_error_label.hide()
        login_data = {
            'username': self.username_input.text(),
            'computer_name': str(socket.gethostname()),
        }

        r = requests.post(self.url + 'api/login/', data=login_data)

        r = json.loads(r.text)

        print(r)

        if 'success' in r and r['success']:
            print('hi')
            self.login_error_label.hide()
            print('Logged in as', r['username'])
            self.logged_in = True
            self.balance = r['balance']
            self.username = r['username']
            self.header_name.setText(self.username + ' | $' + "{:.2f}".format(self.balance))
            self.header_frame.show()
            self.start_balance_timer()
        else:
            self.login_error_label.show()

        self.login_frame.hide()

    def update_balance(self):
        balance_data = {
            'computer_name': str(socket.gethostname()),
        }
        r = json.loads(requests.post(self.url + 'api/balance/', data=balance_data).text)
        if r['success']:
            self.balance = r['balance']
        self.header_name.setText(self.username + ' | $' + "{:.2f}".format(self.balance))

    def crash_bet_button_pressed(self):
        # if not self.crash_data['running'] and not self.crash_data['check']:
        if time.time() < self.crash_data['start_time'] and self.crash_bet == 0:
            try:
                if float(self.crash_bet_amount.text()) > 0:
                    crash_bet_data = {
                        'bet': round(float(self.crash_bet_amount.text()), 2),
                        'computer_name': str(socket.gethostname()),
                    }
                    r = json.loads(requests.post(self.url + 'api/crash_bet/', data=crash_bet_data).text)
                    if r['success']:
                        self.crash_bet_label.setText("{:.2f}".format(round(float(self.crash_bet_amount.text()), 2)))
                        self.crash_bet = round(float(self.crash_bet_amount.text()), 2)
                        self.crash_bet_amount.setText("{:.2f}".format(round(float(self.crash_bet_amount.text()), 2)))
                        self.crash_bet_amount.hide()
            except:
                pass
        elif time.time() > self.crash_data['start_time'] and self.crash_multiplier < self.crash_data['multiplier'] and not self.cashed_out:
            print(self.crash_multiplier)
            cashed_out_mult = self.crash_multiplier
            cashed_out_win = round(self.crash_multiplier * self.crash_bet, 2)
            cashed_out_data = {
                'multiplier': cashed_out_mult,
                'computer_name': str(socket.gethostname())
            }
            r = json.loads(requests.post(self.url + 'api/crash_cashout/', data=cashed_out_data).text)
            if r['success']:
                self.crash_bet_button.setStyleSheet('background-color: rgb(0, 100, 0);\n'
                                                    'font-size: 13px;')
                self.crash_bet_button.setText('Cashed out \n' + str(cashed_out_win) + f'\n({cashed_out_mult}x)')
                self.cashed_out = True

        else:
            self.start_crash_error_timer()

    def start_balance_timer(self):
        self.balance_timer = QTimer()
        self.balance_timer.timeout.connect(self.update_balance)
        self.balance_timer.setInterval(2000)
        self.balance_timer.start()

    def update_crash(self):
        # print(self.crash_data['check'])
        if self.crash_data['check']:
            r = json.loads(requests.get(self.url + 'api/crash/').text)
            print(r)
            if 'error' in r:
                self.crash_amount.setText('Error')
            else:
                if r['done']:
                    self.crash_data['check'] = True
                else:
                    if r['running']:
                        self.crash_data = {
                            'check': False,
                            'running': True,
                            'start_time': r['start_time'],
                            'multiplier': r['multiplier'],
                        }
                        time_to_makeup = time.time() - r['start_time']
                        time_made_up = 0
                        self.crash_multiplier = 1.0
                        while time_made_up < time_to_makeup:
                            self.crash_multiplier += .01
                            time_made_up += .02 / self.crash_multiplier * 10 + .0165
                    else:
                        self.crash_data = {
                            'check': False,
                            'running': False,
                            'start_time': r['start_time'],
                            'multiplier': r['multiplier'],
                        }
                        self.crash_bet_label.setText("")
                        self.crash_multiplier = 1
                        self.crash_bet = 0
                        self.cashed_out = False
                        self.crash_bet_amount.show()
                    # print(self.crash_data)

    def start_crash_timer(self):
        self.crash_timer = QTimer()
        self.crash_timer.timeout.connect(self.update_crash)
        self.crash_timer.setInterval(1000)
        self.crash_timer.start()

    def update_crash_players(self):
        r = json.loads(requests.get(self.url + 'api/crash_players/').text)
        if r['success'] and r['label'] != '':
            self.crash_players_label.setText(r['label'])
        else:
            self.crash_players_label.setText('')

    def start_crash_players_timer(self):
        self.crash_players_timer = QTimer()
        self.crash_players_timer.timeout.connect(self.update_crash_players)
        self.crash_players_timer.setInterval(4000)
        self.crash_players_timer.start(1000)

    def update_gui_crash(self):
        if not self.crash_data['check']:
            self.crash_amount.setStyleSheet('color: rgb(255, 200, 0);')
            if self.crash_data['running']:
                if time.time() >= self.next_time_crash:
                    self.crash_multiplier += .01
                    self.crash_multiplier = round(self.crash_multiplier, 2)
                    amount_to_sleep = .02 / self.crash_multiplier * 10
                    if not self.cashed_out and self.crash_bet > 0:
                        self.crash_bet_button.setText('Cashout \n' + str(round(self.crash_bet * self.crash_multiplier, 2)))
                    self.next_time_crash = time.time() + amount_to_sleep
                if self.crash_multiplier >= self.crash_data['multiplier']:
                    self.crash_amount.setText("{:.2f}".format(self.crash_data['multiplier']) + 'x')
                    self.crash_amount.setStyleSheet('color: rgb(200, 0, 0);')
                    self.crash_data['check'] = True
                    self.crash_rounds.append(self.crash_multiplier)
                    self.update_history()
                    # self.crash_multiplier = 1.00
                    # self.crash_bet = 0.0
                else:
                    self.crash_amount.setText("{:.2f}".format(self.crash_multiplier) + 'x')
                # self.crash_amount.setText(str(self.crash_data['multiplier']) + 'x')
            else:
                time_left = int(round(self.crash_data['start_time'] - time.time(), 0))
                self.crash_amount.setText('Starting in ' + str(time_left))
                if self.crash_data['start_time'] - time.time() <= 0:
                    self.crash_data['running'] = True
                    if self.crash_bet > 0:
                        self.crash_bet_button.setText('Cashout \n' + str(self.crash_bet))
                        self.crash_bet_button.setStyleSheet('background-color: rgb(0, 150, 0);\n'
                                                            'font-size: 13px;')
                else:
                    self.crash_bet_button.setText('Bet')
                    self.crash_bet_button.setStyleSheet('background-color: rgb(60, 60, 60);\n'
                                                        'font-size: 25px;')
        else:
            # self.crash_amount.setText('Getting data')
            pass

    def start_gui_crash_timer(self):
        self.gui_crash_timer = QTimer()
        self.gui_crash_timer.timeout.connect(self.update_gui_crash)
        self.gui_crash_timer.setInterval(25)
        self.gui_crash_timer.start()

    def crash_error_hide(self):
        self.crash_bet_message.hide()
        self.crash_error_timer.stop()

    def start_crash_error_timer(self):
        self.crash_bet_message.show()
        self.crash_error_timer.stop()
        self.crash_error_timer.start(2500)

    def update_history(self):
        i = 1
        for multiplier in reversed(self.crash_rounds):
            if i == 1:
                if multiplier >= 2:
                    self.crash_history_1.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_1.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_1.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_1.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_1.setText("{:.2f}".format(multiplier) + 'x')
            elif i == 2:
                if multiplier >= 2:
                    self.crash_history_2.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_2.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_2.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_2.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_2.setText("{:.2f}".format(multiplier) + 'x')
            elif i == 3:
                if multiplier >= 2:
                    self.crash_history_3.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_3.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_3.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_3.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_3.setText("{:.2f}".format(multiplier) + 'x')
            elif i == 4:
                if multiplier >= 2:
                    self.crash_history_4.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_4.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_4.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_4.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_4.setText("{:.2f}".format(multiplier) + 'x')
            elif i == 5:
                if multiplier >= 2:
                    self.crash_history_5.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_5.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_5.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_5.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_5.setText("{:.2f}".format(multiplier) + 'x')
            else:
                break
            i += 1

    def pre_setup(self):
        self.setFont(QFont('Roboto'))
        self.login_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.crash_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.crash_bet_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.crash_amount.setText('1.00x')
        self.header_frame.hide()
        self.crash_bet_message.hide()
        self.crash_history_1.setText('')
        self.crash_history_2.setText('')
        self.crash_history_3.setText('')
        self.crash_history_4.setText('')
        self.crash_history_5.setText('')

        self.crash_error_timer = QTimer()
        self.crash_error_timer.timeout.connect(self.crash_error_hide)
        self.crash_error_timer.setInterval(4000)

        # Timers
        self.start_crash_timer()
        self.start_gui_crash_timer()
        self.start_crash_players_timer()

        # Hide everything
        self.hide_everything()

        # Show Login
        self.show_login()

        # Buttons
        self.login_button.clicked.connect(self.login_pressed)
        self.crash_button.clicked.connect(self.crash_button_pressed)
        self.crash_bet_button.clicked.connect(self.crash_bet_button_pressed)

    def show_login(self):
        self.login_error_label.hide()
        self.login_frame.show()

    def hide_everything(self):
        self.login_frame.hide()
        self.crash_frame.hide()
        # self.login_label.hide()
        # self.username_input.hide()
        # self.login_button.hide()
        # self.login_error_label.hide()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    with open('ui/style.css', 'r+') as style:
        app.setStyleSheet(style.read())
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())




































