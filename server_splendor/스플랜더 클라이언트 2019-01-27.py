import numpy
import random
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import datetime
import os
import sys
from functools import *
import traceback
import json
import socket
from threading import Thread

from RESOURCES_STR import *
from RESOURCES_IMAGE import *

sys.excepthook = traceback.print_exception
RESOURCES_IMAGE_PATH = 'resources/images/'

HOST = 'localhost'
PORT = 9000


class Emitter(QObject):
    int_signal = pyqtSignal(int)
    str_signal = pyqtSignal(str)
    dict_signal = pyqtSignal(dict)
    list_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.parameter_dic = {}

    def parameter_control(self, *args):
        for i in range(len(args)):
            self.parameter_dic[i] = None

        for i, val in enumerate(args):
            self.parameter_dic[i] = val

    def emit(self, sth):
        if type(sth) == int:
            self.int_signal.emit(sth)
        elif type(sth) == str:
            self.str_signal.emit(sth)
        elif type(sth) == dict:
            self.dict_signal.emit(sth)
        elif type(sth) == list:
            self.list_signal.emit(sth)

    def int_emit(self, sth):
        self.int_signal.emit(sth)

    def str_emit(self, sth):
        self.str_signal.emit(sth)

    def dict_emit(self, sth):
        self.dict_signal.emit(sth)

    def list_emit(self, sth):
        self.list_signal.emit(sth)

class ChatServer(QThread):
    # 용도에 따른 emitter를 따로 만들어줘야 할 것 같음
    reinput_emitter = Emitter()
    wait_emitter = Emitter()
    noti_emitter = Emitter()
    celestiality_emitter = Emitter()
    turn_over_emitter = Emitter()
    end_warning_emitter = Emitter()
    end_noti_emitter = Emitter()

    resources_view_emitter = Emitter()
    buy_card_view_emitter = Emitter()
    reservation_view_emitter = Emitter()
    celestiality_view_emitter = Emitter()
    points_view_emitter = Emitter()

    def __init__(self):
        super().__init__()

    def rcvMsg(self, sock):
        while True:
            try:
                data = sock.recv(1024)
                # if not data:
                #     break
                decoded = data.decode()
                converted = json.loads(decoded)
                print("막 리시브해서 변환되었을 때", converted)

                # 알림용
                if converted["지시"] == "재입력":
                    text = converted["내용"]
                    self.reinput_emitter.str_emit(text)

                elif converted["지시"] == "대기":
                    text = "당신의 차례가 아닙니다"
                    self.wait_emitter.str_emit(text)

                # 게임 시작 전
                elif converted["지시"] == "대기실 입장":
                    controller.wait_for_the_game(converted["유저목록"])
                    controller.user_enroll(converted["유저목록"])
                    controller.num_list_calculator()
                    controller.wait_room.view_modifier(converted["유저목록"])
                elif converted["지시"] == "신규유저 입장":
                    controller.user_enroll(converted["유저목록"])
                    controller.wait_room.view_modifier(converted["유저목록"])
                elif converted["지시"] == "게임시작":
                    controller.start_the_game()
                    controller.game_widget.initializer(converted["은행"], controller.player_list, 0)

                    self.reinput_emitter.str_signal.connect(controller.reinput_noti_box.show_up)
                    self.turn_over_emitter.str_signal.connect(controller.turn_over_noti_box.show_up)
                    self.wait_emitter.str_signal.connect(controller.wait_box.show_up)
                    self.celestiality_emitter.list_signal.connect(controller.celestiality_selection_box.show_up)
                    self.end_warning_emitter.str_signal.connect(controller.end_warning_box.show_up)
                    self.end_noti_emitter.list_signal.connect(controller.winner_notification_widget.set_content)

                    self.resources_view_emitter.list_signal.connect(controller.game_widget.resources_view_update)
                    self.buy_card_view_emitter.list_signal.connect(controller.game_widget.buy_card_view_modification)
                    self.reservation_view_emitter.list_signal.connect(controller.game_widget.reservation_view_modification)
                    self.celestiality_view_emitter.list_signal.connect(controller.game_widget.celestial_view_modification)
                    self.points_view_emitter.list_signal.connect(controller.game_widget.points_view_modification)

                elif converted["지시"] == "천상계 강림":
                    # controller.game_widget.resources_view_update(converted["자원 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.buy_card_view_modification(converted["바닥카드 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.reservation_view_modification(converted["예약카드 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.celestial_view_modification(converted["천상계 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.points_view_modification(converted["포인트 뷰"], controller.my_original_num, controller.num_list)

                    # self.resources_view_emitter.list_emit([converted["자원 뷰"], controller.my_original_num, controller.num_list])
                    # self.buy_card_view_emitter.list_emit([converted["바닥카드 뷰"], controller.my_original_num, controller.num_list])
                    # self.reservation_view_emitter.list_emit([converted["예약카드 뷰"], controller.my_original_num, controller.num_list])
                    # self.celestiality_view_emitter.list_emit([converted["천상계 뷰"], controller.my_original_num, controller.num_list])
                    # self.points_view_emitter.list_emit([converted["포인트 뷰"], controller.my_original_num, controller.num_list])

                    id_list = converted["가능카드"]
                    self.celestiality_emitter.list_emit(id_list)

                elif converted["지시"] == "턴 넘김":
                    # controller.game_widget.resources_view_update(converted["자원 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.buy_card_view_modification(converted["바닥카드 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.reservatiton_view_modification(converted["예약카드 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.celestial_view_modification(converted["천상계 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.points_view_modification(converted["포인트 뷰"], controller.my_original_num, controller.num_list)

                    self.resources_view_emitter.list_emit([converted["자원 뷰"], controller.my_original_num, controller.num_list])
                    self.buy_card_view_emitter.list_emit([converted["바닥카드 뷰"], controller.my_original_num, controller.num_list])
                    self.reservation_view_emitter.list_emit([converted["예약카드 뷰"], controller.my_original_num, controller.num_list])
                    self.celestiality_view_emitter.list_emit([converted["천상계 뷰"], controller.my_original_num, controller.num_list])
                    self.points_view_emitter.list_emit([converted["포인트 뷰"], controller.my_original_num, controller.num_list])

                    text = "이번 턴은 " + converted["순서"] + " 님의 차례입니다"
                    self.turn_over_emitter.str_emit(text)

                elif converted["지시"] == "이번 턴에 종료":
                    # controller.game_widget.resources_view_update(converted["자원 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.buy_card_view_modification(converted["바닥카드 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.reservation_view_modification(converted["예약카드 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.celestial_view_modification(converted["천상계 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.points_view_modification(converted["포인트 뷰"], controller.my_original_num, controller.num_list)

                    self.resources_view_emitter.list_emit([converted["자원 뷰"], controller.my_original_num, controller.num_list])
                    self.buy_card_view_emitter.list_emit([converted["바닥카드 뷰"], controller.my_original_num, controller.num_list])
                    self.reservation_view_emitter.list_emit([converted["예약카드 뷰"], controller.my_original_num, controller.num_list])
                    self.celestiality_view_emitter.list_emit([converted["천상계 뷰"], controller.my_original_num, controller.num_list])
                    self.points_view_emitter.list_emit([converted["포인트 뷰"], controller.my_original_num, controller.num_list])

                    text = converted["메세지"]
                    self.end_warning_emitter.str_emit(text)

                elif converted["지시"] == "즉시 종료":
                    # controller.game_widget.resources_view_update(converted["자원 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.buy_card_view_modification(converted["바닥카드 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.reservation_view_modification(converted["예약카드 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.celestial_view_modification(converted["천상계 뷰"], controller.my_original_num, controller.num_list)
                    # controller.game_widget.points_view_modification(converted["포인트 뷰"], controller.my_original_num, controller.num_list)
                    print("즉시 종료로 오나?")

                    self.resources_view_emitter.list_emit([converted["자원 뷰"], controller.my_original_num, controller.num_list])
                    self.buy_card_view_emitter.list_emit([converted["바닥카드 뷰"], controller.my_original_num, controller.num_list])
                    self.reservation_view_emitter.list_emit([converted["예약카드 뷰"], controller.my_original_num, controller.num_list])
                    self.celestiality_view_emitter.list_emit([converted["천상계 뷰"], controller.my_original_num, controller.num_list])
                    self.points_view_emitter.list_emit([converted["포인트 뷰"], controller.my_original_num, controller.num_list])

                    user_list = converted["유저목록"]
                    points = converted["포인트"]
                    card_num = converted["카드개수"]
                    send_list = [user_list, points, card_num]
                    self.end_noti_emitter.list_emit(send_list)

            except Exception as e:
                print("에러터졌나?", e)

    def runChat(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        t = Thread(target=self.rcvMsg, args=(self.sock,))
        t.daemon = True
        t.start()

    def send_message(self, dictionary_type):
        converted = json.dumps(dictionary_type, indent=2)
        self.sock.send(converted.encode())

    # def send_box_selection(self, dictionary_type, box_instance):
    #     converted = json.dumps(dictionary_type, indent=2)
    #     self.sock.send(converted)


class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.menu_setting()

        self.show()

    def menu_setting(self):
        self.menubar = self.menuBar()
        self.main_menu = self.menubar.addMenu("메뉴")
        self.quit = QAction("나가기", self)
        self.main_menu.addAction(self.quit)


class EntranceWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout()

        self.layout_design()
        self.widget_design()

        self.setLayout(self.main_layout)
        # self.setFixedHeight(400)

    def layout_design(self):
        self.greet_layout = QHBoxLayout()
        self.pic_layout = QHBoxLayout()
        self.id_input_layout = QHBoxLayout()
        self.next_page_layout = QHBoxLayout()

        self.greet_layout.setAlignment(Qt.AlignCenter)
        self.pic_layout.setAlignment(Qt.AlignCenter)
        self.id_input_layout.setAlignment(Qt.AlignCenter)
        self.next_page_layout.setAlignment(Qt.AlignCenter)

        self.main_layout.addLayout(self.greet_layout)
        self.main_layout.addLayout(self.pic_layout)
        self.main_layout.addLayout(self.id_input_layout)
        self.main_layout.addLayout(self.next_page_layout)

    def widget_design(self):
        self.greet = QLabel("반갑습니다")
        self.pic = QLabel(" ")
        self.player_name_label = QLabel("플레이어 ID를 입력하세요.")
        self.player_input_line = QLineEdit()
        self.next_page = QPushButton("입장합니다")

        self.pic.setPixmap(QPixmap(RESOURCES_IMAGE_PATH + "splendor-background.jpg"))
        self.pic.update()

        self.greet_layout.addWidget(self.greet)
        self.pic_layout.addWidget(self.pic)
        self.id_input_layout.addWidget(self.player_name_label)
        self.id_input_layout.addWidget(self.player_input_line)
        self.next_page_layout.addWidget(self.next_page)

        self.next_page.setShortcut("Return")


class WaitingRoom(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QFormLayout()

        self.setWindowTitle("대기실")

        self.informative_word = QLabel("방장이 시작을 누를 때까지 대기하십시오")
        self.player1_widget = QLabel()
        self.player2_widget = QLabel()
        self.player3_widget = QLabel()
        self.player4_widget = QLabel()
        self.start_button = QPushButton("게임을 시작합니다")
        self.start_button.setEnabled(False)
        # 디버깅단계
        # self.start_button.setEnabled(True)
        # 디버깅단계

        self.start_button.setShortcut("Return")

        self.main_layout.addRow(self.informative_word)
        self.main_layout.addRow(self.player1_widget)
        self.main_layout.addRow(self.player2_widget)
        self.main_layout.addRow(self.player3_widget)
        self.main_layout.addRow(self.player4_widget)
        self.main_layout.addRow(self.start_button)

        self.setLayout(self.main_layout)

    def view_modifier(self, dic_type):
        print('뷰 모디파이어 진입')
        player_name_list = []
        for i in dic_type:
            player_name_list.append(dic_type[str(i)])

        if len(player_name_list) == 1:
            self.player1_widget.setText("플레이어1(방장) : " + player_name_list[0])
            self.player1_widget.update()
            self.player2_widget.setText("")
            self.player2_widget.update()
            self.player3_widget.setText("")
            self.player3_widget.update()
            self.player4_widget.setText("")
            self.player4_widget.update()
        elif len(player_name_list) == 2:
            self.player1_widget.setText("플레이어1(방장) : " + player_name_list[0])
            self.player1_widget.update()
            self.player2_widget.setText("플레이어2 : " + player_name_list[1])
            self.player2_widget.update()
            self.player3_widget.setText("")
            self.player3_widget.update()
            self.player4_widget.setText("")
            self.player4_widget.update()
        elif len(player_name_list) == 3:
            self.player1_widget.setText("플레이어1(방장) : " + player_name_list[0])
            self.player1_widget.update()
            self.player2_widget.setText("플레이어2 : " + player_name_list[1])
            self.player2_widget.update()
            self.player3_widget.setText("플레이어3 : " + player_name_list[2])
            self.player3_widget.update()
            self.player4_widget.setText("")
            self.player4_widget.update()
        elif len(player_name_list) == 4:
            self.player1_widget.setText("플레이어1(방장) : " + player_name_list[0])
            self.player1_widget.update()
            self.player2_widget.setText("플레이어2 : " + player_name_list[1])
            self.player2_widget.update()
            self.player3_widget.setText("플레이어3 : " + player_name_list[2])
            self.player3_widget.update()
            self.player4_widget.setText("플레이어4 : " + player_name_list[3])
            self.player4_widget.update()


class Notification(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("알림")
        self.layout = QFormLayout()
        self.info = QLabel()
        self.button = QPushButton("확인")
        self.layout.addRow(self.info)
        self.layout.addRow(self.button)
        self.setLayout(self.layout)

    @pyqtSlot(str)
    def show_up(self, text=""):
        self.info.setText(text)
        self.info.update()
        self.show()
        # self.choice = QMessageBox.question(self, '알림', text, QMessageBox.Yes)


# GUI단의 player 객체가 필요..

class GameWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QGridLayout()
        self.player_layout_design()
        self.player_widget_design()
        self.bank_layout_design()
        self.bank_widget_design()

        self.setLayout(self.main_layout)
        self.setFixedHeight(980)

    def player_layout_design(self):
        # 플레이어 자원, 카드, 천상계 카드 레이아웃
        self.player1_layout = QHBoxLayout()
        self.player2_layout = QHBoxLayout()
        self.player3_layout = QHBoxLayout()
        self.player4_layout = QHBoxLayout()

        self.player1_sublayout = QVBoxLayout()
        self.player2_sublayout = QVBoxLayout()
        self.player3_sublayout = QVBoxLayout()
        self.player4_sublayout = QVBoxLayout()

        self.player1_rsc_card_layout = QVBoxLayout()
        self.player2_rsc_card_layout = QVBoxLayout()
        self.player3_rsc_card_layout = QVBoxLayout()
        self.player4_rsc_card_layout = QVBoxLayout()

        self.player1_rsc_image_layout = QHBoxLayout()
        self.player2_rsc_image_layout = QHBoxLayout()
        self.player3_rsc_image_layout = QHBoxLayout()
        self.player4_rsc_image_layout = QHBoxLayout()

        self.player1_rsc_num_layout = QHBoxLayout()
        self.player2_rsc_num_layout = QHBoxLayout()
        self.player3_rsc_num_layout = QHBoxLayout()
        self.player4_rsc_num_layout = QHBoxLayout()

        self.player1_normal_cards_image_layout = QHBoxLayout()
        self.player2_normal_cards_image_layout = QHBoxLayout()
        self.player3_normal_cards_image_layout = QHBoxLayout()
        self.player4_normal_cards_image_layout = QHBoxLayout()

        self.player1_normal_cards_num_layout = QHBoxLayout()
        self.player2_normal_cards_num_layout = QHBoxLayout()
        self.player3_normal_cards_num_layout = QHBoxLayout()
        self.player4_normal_cards_num_layout = QHBoxLayout()

        self.player1_celestial_cards_layout = QVBoxLayout()
        self.player2_celestial_cards_layout = QVBoxLayout()
        self.player3_celestial_cards_layout = QVBoxLayout()
        self.player4_celestial_cards_layout = QVBoxLayout()

        # 천상계
        self.player1_layout.addLayout(self.player1_celestial_cards_layout)
        self.player2_layout.addLayout(self.player2_celestial_cards_layout)
        self.player3_layout.addLayout(self.player3_celestial_cards_layout)
        self.player4_layout.addLayout(self.player4_celestial_cards_layout)

        self.player1_rsc_card_layout.addLayout(self.player1_rsc_image_layout)
        self.player2_rsc_card_layout.addLayout(self.player2_rsc_image_layout)
        self.player3_rsc_card_layout.addLayout(self.player3_rsc_image_layout)
        self.player4_rsc_card_layout.addLayout(self.player4_rsc_image_layout)

        self.player1_rsc_card_layout.addLayout(self.player1_rsc_num_layout)
        self.player2_rsc_card_layout.addLayout(self.player2_rsc_num_layout)
        self.player3_rsc_card_layout.addLayout(self.player3_rsc_num_layout)
        self.player4_rsc_card_layout.addLayout(self.player4_rsc_num_layout)

        self.player1_rsc_card_layout.addLayout(self.player1_normal_cards_image_layout)
        self.player2_rsc_card_layout.addLayout(self.player2_normal_cards_image_layout)
        self.player3_rsc_card_layout.addLayout(self.player3_normal_cards_image_layout)
        self.player4_rsc_card_layout.addLayout(self.player4_normal_cards_image_layout)

        self.player1_rsc_card_layout.addLayout(self.player1_normal_cards_num_layout)
        self.player2_rsc_card_layout.addLayout(self.player2_normal_cards_num_layout)
        self.player3_rsc_card_layout.addLayout(self.player3_normal_cards_num_layout)
        self.player4_rsc_card_layout.addLayout(self.player4_normal_cards_num_layout)

        self.main_layout.addLayout(self.player1_layout, 2, 1)
        self.main_layout.addLayout(self.player2_layout, 1, 2)
        self.main_layout.addLayout(self.player3_layout, 0, 1)
        self.main_layout.addLayout(self.player4_layout, 1, 0)
        self.main_layout.addLayout(self.player1_sublayout, 2, 2)
        self.main_layout.addLayout(self.player2_sublayout, 0, 2)
        self.main_layout.addLayout(self.player3_sublayout, 0, 0)
        self.main_layout.addLayout(self.player4_sublayout, 2, 0)

        self.player1_layout.addLayout(self.player1_rsc_card_layout)
        self.player2_layout.addLayout(self.player2_rsc_card_layout)
        self.player3_layout.addLayout(self.player3_rsc_card_layout)
        self.player4_layout.addLayout(self.player4_rsc_card_layout)

        self.player1_layout.addLayout(self.player1_celestial_cards_layout)
        self.player2_layout.addLayout(self.player2_celestial_cards_layout)
        self.player3_layout.addLayout(self.player3_celestial_cards_layout)
        self.player4_layout.addLayout(self.player4_celestial_cards_layout)

        # 플레이어 이름, 점수, 예약카드 레이아웃
        self.player1_name_layout = QHBoxLayout()
        self.player1_point_layout = QHBoxLayout()
        self.player1_reservation_card_layout = QHBoxLayout()
        self.player2_name_layout = QHBoxLayout()
        self.player2_point_layout = QHBoxLayout()
        self.player2_reservation_card_layout = QHBoxLayout()
        self.player3_name_layout = QHBoxLayout()
        self.player3_point_layout = QHBoxLayout()
        self.player3_reservation_card_layout = QHBoxLayout()
        self.player4_name_layout = QHBoxLayout()
        self.player4_point_layout = QHBoxLayout()
        self.player4_reservation_card_layout = QHBoxLayout()

        self.player1_sublayout.addLayout(self.player1_name_layout)
        self.player1_sublayout.addLayout(self.player1_point_layout)
        self.player1_sublayout.addLayout(self.player1_reservation_card_layout)
        self.player2_sublayout.addLayout(self.player2_name_layout)
        self.player2_sublayout.addLayout(self.player2_point_layout)
        self.player2_sublayout.addLayout(self.player2_reservation_card_layout)
        self.player3_sublayout.addLayout(self.player3_name_layout)
        self.player3_sublayout.addLayout(self.player3_point_layout)
        self.player3_sublayout.addLayout(self.player3_reservation_card_layout)
        self.player4_sublayout.addLayout(self.player4_name_layout)
        self.player4_sublayout.addLayout(self.player4_point_layout)
        self.player4_sublayout.addLayout(self.player4_reservation_card_layout)

        # 레이아웃 정렬
        self.player1_layout.setAlignment(Qt.AlignCenter)
        self.player2_layout.setAlignment(Qt.AlignCenter)
        self.player3_layout.setAlignment(Qt.AlignCenter)
        self.player4_layout.setAlignment(Qt.AlignCenter)

        self.player1_celestial_cards_layout.setAlignment(Qt.AlignCenter)
        self.player1_reservation_card_layout.setAlignment(Qt.AlignCenter)

        self.player2_celestial_cards_layout.setAlignment(Qt.AlignCenter)
        self.player2_reservation_card_layout.setAlignment(Qt.AlignCenter)

        self.player3_celestial_cards_layout.setAlignment(Qt.AlignCenter)
        self.player3_reservation_card_layout.setAlignment(Qt.AlignCenter)

        self.player4_celestial_cards_layout.setAlignment(Qt.AlignCenter)
        self.player4_reservation_card_layout.setAlignment(Qt.AlignCenter)

    def player_widget_design(self):
        self.player1_rsc_image_slot = {}
        self.player1_rsc_num_slot = {}
        self.player1_normal_cards_image_slot = {}
        self.player1_normal_cards_num_slot = {}
        self.player1_celestial_cards_slot = {}

        self.player2_rsc_image_slot = {}
        self.player2_rsc_num_slot = {}
        self.player2_normal_cards_image_slot = {}
        self.player2_normal_cards_num_slot = {}
        self.player2_celestial_cards_slot = {}

        self.player3_rsc_image_slot = {}
        self.player3_rsc_num_slot = {}
        self.player3_normal_cards_image_slot = {}
        self.player3_normal_cards_num_slot = {}
        self.player3_celestial_cards_slot = {}

        self.player4_rsc_image_slot = {}
        self.player4_rsc_num_slot = {}
        self.player4_normal_cards_image_slot = {}
        self.player4_normal_cards_num_slot = {}
        self.player4_celestial_cards_slot = {}

        for i in range(6):
            self.player1_rsc_image_slot[i] = QLabel(" ")
            self.player2_rsc_image_slot[i] = QLabel(" ")
            self.player3_rsc_image_slot[i] = QLabel(" ")
            self.player4_rsc_image_slot[i] = QLabel(" ")

            self.player1_rsc_image_layout.addWidget(self.player1_rsc_image_slot[i])
            self.player2_rsc_image_layout.addWidget(self.player2_rsc_image_slot[i])
            self.player3_rsc_image_layout.addWidget(self.player3_rsc_image_slot[i])
            self.player4_rsc_image_layout.addWidget(self.player4_rsc_image_slot[i])

            self.player1_rsc_num_slot[i] = QLabel()
            self.player2_rsc_num_slot[i] = QLabel()
            self.player3_rsc_num_slot[i] = QLabel()
            self.player4_rsc_num_slot[i] = QLabel()
            self.player1_rsc_num_layout.addWidget(self.player1_rsc_num_slot[i])
            self.player2_rsc_num_layout.addWidget(self.player2_rsc_num_slot[i])
            self.player3_rsc_num_layout.addWidget(self.player3_rsc_num_slot[i])
            self.player4_rsc_num_layout.addWidget(self.player4_rsc_num_slot[i])

            self.player1_normal_cards_image_slot[i] = QLabel(" ")
            self.player2_normal_cards_image_slot[i] = QLabel(" ")
            self.player3_normal_cards_image_slot[i] = QLabel(" ")
            self.player4_normal_cards_image_slot[i] = QLabel(" ")
            self.player1_normal_cards_image_layout.addWidget(self.player1_normal_cards_image_slot[i])
            self.player2_normal_cards_image_layout.addWidget(self.player2_normal_cards_image_slot[i])
            self.player3_normal_cards_image_layout.addWidget(self.player3_normal_cards_image_slot[i])
            self.player4_normal_cards_image_layout.addWidget(self.player4_normal_cards_image_slot[i])

        for i in range(5):
            self.player1_normal_cards_num_slot[i] = QLabel()
            self.player2_normal_cards_num_slot[i] = QLabel()
            self.player3_normal_cards_num_slot[i] = QLabel()
            self.player4_normal_cards_num_slot[i] = QLabel()
            self.player1_normal_cards_num_layout.addWidget(self.player1_normal_cards_num_slot[i])
            self.player2_normal_cards_num_layout.addWidget(self.player2_normal_cards_num_slot[i])
            self.player3_normal_cards_num_layout.addWidget(self.player3_normal_cards_num_slot[i])
            self.player4_normal_cards_num_layout.addWidget(self.player4_normal_cards_num_slot[i])

        for i, val in enumerate(
                ["dia-token.png", "eme-token.jpg", "cho-token.png", "rby-token.png", "spr-token.jpg", "gld-token.png"]):
            self.player1_rsc_image_slot[i].setPixmap(QPixmap(RESOURCES_IMAGE_PATH + val).scaled(50, 50))
            self.player2_rsc_image_slot[i].setPixmap(QPixmap(RESOURCES_IMAGE_PATH + val).scaled(50, 50))
            self.player3_rsc_image_slot[i].setPixmap(QPixmap(RESOURCES_IMAGE_PATH + val).scaled(50, 50))
            self.player4_rsc_image_slot[i].setPixmap(QPixmap(RESOURCES_IMAGE_PATH + val).scaled(50, 50))
        for i, val in enumerate(["dia.png", "eme.png", "cho.png", "rby.png", "spr.png"]):
            self.player1_normal_cards_image_slot[i].setPixmap(QPixmap(RESOURCES_IMAGE_PATH + val).scaled(50, 50))
            self.player2_normal_cards_image_slot[i].setPixmap(QPixmap(RESOURCES_IMAGE_PATH + val).scaled(50, 50))
            self.player3_normal_cards_image_slot[i].setPixmap(QPixmap(RESOURCES_IMAGE_PATH + val).scaled(50, 50))
            self.player4_normal_cards_image_slot[i].setPixmap(QPixmap(RESOURCES_IMAGE_PATH + val).scaled(50, 50))

        for i in range(5):
            self.player1_celestial_cards_slot[i] = QLabel()
            self.player2_celestial_cards_slot[i] = QLabel()
            self.player3_celestial_cards_slot[i] = QLabel()
            self.player4_celestial_cards_slot[i] = QLabel()
            self.player1_celestial_cards_layout.addWidget(self.player1_celestial_cards_slot[i])
            self.player2_celestial_cards_layout.addWidget(self.player2_celestial_cards_slot[i])
            self.player3_celestial_cards_layout.addWidget(self.player3_celestial_cards_slot[i])
            self.player4_celestial_cards_layout.addWidget(self.player4_celestial_cards_slot[i])

        # 서브레이아웃 위젯들 설정
        self.player1_name_label = QLabel("플레이어 이름 : ")
        self.player1_point_label = QLabel()
        self.player2_name_label = QLabel("플레이어 이름 : ")
        self.player2_point_label = QLabel()
        self.player3_name_label = QLabel("플레이어 이름 : ")
        self.player3_point_label = QLabel()
        self.player4_name_label = QLabel("플레이어 이름 : ")
        self.player4_point_label = QLabel()

        self.player1_name_layout.addWidget(self.player1_name_label)
        self.player2_name_layout.addWidget(self.player2_name_label)
        self.player3_name_layout.addWidget(self.player3_name_label)
        self.player4_name_layout.addWidget(self.player4_name_label)
        self.player1_point_layout.addWidget(self.player1_point_label)
        self.player2_point_layout.addWidget(self.player2_point_label)
        self.player3_point_layout.addWidget(self.player3_point_label)
        self.player4_point_layout.addWidget(self.player4_point_label)

        # 예약카드 슬롯
        self.player1_reservation_card_slot = {}
        for i in range(3):
            self.player1_reservation_card_slot[i] = QPushButton()
            self.player1_reservation_card_slot[i].setFixedSize(QSize(130, 130))
            self.player1_reservation_card_slot[i].setStyleSheet("border: none")
            self.player1_reservation_card_layout.addWidget(self.player1_reservation_card_slot[i])
        self.player2_reservation_card_slot = {}
        for i in range(3):
            self.player2_reservation_card_slot[i] = QPushButton()
            self.player2_reservation_card_slot[i].setFixedSize(QSize(130, 130))
            self.player2_reservation_card_slot[i].setStyleSheet("border: none")
            self.player2_reservation_card_layout.addWidget(self.player2_reservation_card_slot[i])
        self.player3_reservation_card_slot = {}
        for i in range(3):
            self.player3_reservation_card_slot[i] = QPushButton()
            self.player3_reservation_card_slot[i].setFixedSize(QSize(130, 130))
            self.player3_reservation_card_slot[i].setStyleSheet("border: none")
            self.player3_reservation_card_layout.addWidget(self.player3_reservation_card_slot[i])
        self.player4_reservation_card_slot = {}
        for i in range(3):
            self.player4_reservation_card_slot[i] = QPushButton()
            self.player4_reservation_card_slot[i].setFixedSize(QSize(130, 130))
            self.player4_reservation_card_slot[i].setStyleSheet("border: none")
            self.player4_reservation_card_layout.addWidget(self.player4_reservation_card_slot[i])

    def bank_layout_design(self):
        self.bank_layout = QVBoxLayout()

        self.bank_rsc_layout = QHBoxLayout()
        self.bank_rsc_layout.setAlignment(Qt.AlignCenter)

        self.bank_celestial_layout = QHBoxLayout()
        self.bank_celestial_layout.setAlignment(Qt.AlignCenter)

        self.bank_normal_card_layout = QVBoxLayout()

        self.bank_normal_card_lv1_layout = QHBoxLayout()
        self.bank_normal_card_lv2_layout = QHBoxLayout()
        self.bank_normal_card_lv3_layout = QHBoxLayout()
        self.bank_normal_card_layout.addLayout(self.bank_normal_card_lv3_layout)
        self.bank_normal_card_layout.addLayout(self.bank_normal_card_lv2_layout)
        self.bank_normal_card_layout.addLayout(self.bank_normal_card_lv1_layout)

        self.dia_layout = QVBoxLayout()
        self.eme_layout = QVBoxLayout()
        self.cho_layout = QVBoxLayout()
        self.rby_layout = QVBoxLayout()
        self.spr_layout = QVBoxLayout()
        self.gld_layout = QVBoxLayout()

        self.bank_rsc_layout.addLayout(self.dia_layout)
        self.bank_rsc_layout.addLayout(self.eme_layout)
        self.bank_rsc_layout.addLayout(self.cho_layout)
        self.bank_rsc_layout.addLayout(self.rby_layout)
        self.bank_rsc_layout.addLayout(self.spr_layout)
        self.bank_rsc_layout.addLayout(self.gld_layout)

        self.bank_layout.addLayout(self.bank_rsc_layout)
        self.bank_layout.addLayout(self.bank_celestial_layout)
        self.bank_layout.addLayout(self.bank_normal_card_layout)
        self.main_layout.addLayout(self.bank_layout, 1, 1)

        self.bank_normal_card_lv1_layout.setAlignment(Qt.AlignCenter)
        self.bank_normal_card_lv2_layout.setAlignment(Qt.AlignCenter)
        self.bank_normal_card_lv3_layout.setAlignment(Qt.AlignCenter)
        self.bank_normal_card_layout.setAlignment(Qt.AlignCenter)

    def bank_widget_design(self):
        '''rsc layout part'''
        self.dia_graphic = QPushButton(" ")
        self.dia_number = QLabel()
        self.eme_graphic = QPushButton(" ")
        self.eme_number = QLabel()
        self.cho_graphic = QPushButton(" ")
        self.cho_number = QLabel()
        self.rby_graphic = QPushButton(" ")
        self.rby_number = QLabel()
        self.spr_graphic = QPushButton(" ")
        self.spr_number = QLabel()
        self.gld_graphic = QPushButton(" ")
        self.gld_number = QLabel()

        self.dia_graphic.setIcon(QIcon(RESOURCES_IMAGE_PATH + "dia-token.png"))
        self.dia_graphic.setIconSize(QSize(50, 50))
        self.dia_graphic.setStyleSheet("border: none")
        self.eme_graphic.setIcon(QIcon(RESOURCES_IMAGE_PATH + "eme-token.jpg"))
        self.eme_graphic.setIconSize(QSize(50, 50))
        self.eme_graphic.setStyleSheet("border: none")
        self.cho_graphic.setIcon(QIcon(RESOURCES_IMAGE_PATH + "cho-token.png"))
        self.cho_graphic.setIconSize(QSize(50, 50))
        self.cho_graphic.setStyleSheet("border: none")
        self.rby_graphic.setIcon(QIcon(RESOURCES_IMAGE_PATH + "rby-token.png"))
        self.rby_graphic.setIconSize(QSize(50, 50))
        self.rby_graphic.setStyleSheet("border: none")
        self.spr_graphic.setIcon(QIcon(RESOURCES_IMAGE_PATH + "spr-token.jpg"))
        self.spr_graphic.setIconSize(QSize(50, 50))
        self.spr_graphic.setStyleSheet("border: none")
        self.gld_graphic.setIcon(QIcon(RESOURCES_IMAGE_PATH + "gld-token.png"))
        self.gld_graphic.setIconSize(QSize(50, 50))
        self.gld_graphic.setStyleSheet("border: none")

        self.dia_layout.addWidget(self.dia_graphic)
        self.dia_layout.addWidget(self.dia_number)
        self.eme_layout.addWidget(self.eme_graphic)
        self.eme_layout.addWidget(self.eme_number)
        self.cho_layout.addWidget(self.cho_graphic)
        self.cho_layout.addWidget(self.cho_number)
        self.rby_layout.addWidget(self.rby_graphic)
        self.rby_layout.addWidget(self.rby_number)
        self.spr_layout.addWidget(self.spr_graphic)
        self.spr_layout.addWidget(self.spr_number)
        self.gld_layout.addWidget(self.gld_graphic)
        self.gld_layout.addWidget(self.gld_number)

        '''celestial card part'''
        self.celestial_slot = {}

        for i in range(5):
            self.celestial_slot[i] = QLabel()
            self.celestial_slot[i].setMaximumSize(150, 150)
        for i in range(5):
            self.bank_celestial_layout.addWidget(self.celestial_slot[i])

        '''normal card part'''
        self.lv1_hidden = QLabel()
        self.lv1_hidden.setPixmap(
            QPixmap(RESOURCES_IMAGE_PATH + "lv1.png").scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.lv2_hidden = QLabel()
        self.lv2_hidden.setPixmap(
            QPixmap(RESOURCES_IMAGE_PATH + "lv2.png").scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.lv3_hidden = QLabel()
        self.lv3_hidden.setPixmap(
            QPixmap(RESOURCES_IMAGE_PATH + "lv3.png").scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.bank_normal_card_lv1_layout.addWidget(self.lv1_hidden)
        self.bank_normal_card_lv2_layout.addWidget(self.lv2_hidden)
        self.bank_normal_card_lv3_layout.addWidget(self.lv3_hidden)

        self.lv1_slot = {}
        self.lv2_slot = {}
        self.lv3_slot = {}

        for i in range(4):
            self.lv1_slot[i] = QPushButton()
            self.lv1_slot[i].setMaximumSize(150, 150)
            self.lv1_slot[i].setStyleSheet("border: none")
        for i in range(4):
            self.lv2_slot[i] = QPushButton()
            self.lv2_slot[i].setMaximumSize(150, 150)
            self.lv2_slot[i].setStyleSheet("border: none")
        for i in range(4):
            self.lv3_slot[i] = QPushButton()
            self.lv3_slot[i].setMaximumSize(150, 150)
            self.lv3_slot[i].setStyleSheet("border: none")
        for i in range(4):
            self.bank_normal_card_lv1_layout.addWidget(self.lv1_slot[i])
            self.bank_normal_card_lv2_layout.addWidget(self.lv2_slot[i])
            self.bank_normal_card_lv3_layout.addWidget(self.lv3_slot[i])

    def initializer(self, dic_bank, dic_player_list, turn):
        player_num = len(dic_player_list)

        # 천상계, 1,2,3단계 카드 이미지 삽입
        for i in range(4):
            self.lv1_slot[i].setIcon(QIcon())
            self.lv2_slot[i].setIcon(QIcon())
            self.lv3_slot[i].setIcon(QIcon())

        for i, id in enumerate(dic_bank["lv1"]):
            self.lv1_slot[i].setIcon(
                QIcon(RESOURCES_IMAGE_PATH + id + str(".jpeg")))
            self.lv1_slot[i].setIconSize(QSize(150, 150))
        for i, id in enumerate(dic_bank["lv2"]):
            self.lv2_slot[i].setIcon(
                QIcon(RESOURCES_IMAGE_PATH + id + str(".jpeg")))
            self.lv2_slot[i].setIconSize(QSize(150, 150))
        for i, id in enumerate(dic_bank["lv3"]):
            self.lv3_slot[i].setIcon(
                QIcon(RESOURCES_IMAGE_PATH + id + str(".jpeg")))
            self.lv3_slot[i].setIconSize(QSize(150, 150))

        # bank 천상계 슬롯
        for i in range(player_num + 1):
            self.celestial_slot[i].setPixmap(QPixmap())
            self.celestial_slot[i].update()
        for i, id in enumerate(dic_bank["celestial"]):
            self.celestial_slot[i].setPixmap(
                QPixmap(RESOURCES_IMAGE_PATH + id + str(".jpeg")).
                    scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        for i in range(5):
            self.celestial_slot[i].update()
        for i in range(4):
            self.lv3_slot[i].update()
            self.lv2_slot[i].update()
            self.lv1_slot[i].update()

        print("예약카드슬롯 부분")
        # 예약카드슬롯 활성화/비활성화
        if turn == 0:
            for i in range(3):
                self.player1_reservation_card_slot[i].setEnabled(True)
                self.player2_reservation_card_slot[i].setEnabled(False)
                self.player3_reservation_card_slot[i].setEnabled(False)
                self.player4_reservation_card_slot[i].setEnabled(False)
        elif turn == 1:
            for i in range(3):
                self.player1_reservation_card_slot[i].setEnabled(False)
                self.player2_reservation_card_slot[i].setEnabled(True)
                self.player3_reservation_card_slot[i].setEnabled(False)
                self.player4_reservation_card_slot[i].setEnabled(False)
        elif turn == 2:
            for i in range(3):
                self.player1_reservation_card_slot[i].setEnabled(False)
                self.player2_reservation_card_slot[i].setEnabled(False)
                self.player3_reservation_card_slot[i].setEnabled(True)
                self.player4_reservation_card_slot[i].setEnabled(False)
        elif turn == 3:
            for i in range(3):
                self.player1_reservation_card_slot[i].setEnabled(False)
                self.player2_reservation_card_slot[i].setEnabled(False)
                self.player3_reservation_card_slot[i].setEnabled(False)
                self.player4_reservation_card_slot[i].setEnabled(True)

        print("플레이어 이름, 점수 부분")
        # 플레이어 이름, 점수 등 초기화
        self.player1_name_label.setText("플레이어 이름 : " + dic_player_list['0'])
        self.player1_point_label.setText("플레이어 점수 :" + str(0))
        self.player1_name_label.update()
        self.player1_point_label.update()

        self.player2_name_label.setText("플레이어 이름 : " + dic_player_list['1'])
        self.player2_point_label.setText("플레이어 점수 :" + str(0))
        self.player2_name_label.update()
        self.player2_point_label.update()

        if player_num == 3:
            self.player3_name_label.setText("플레이어 이름 : " + dic_player_list['2'])
            self.player3_point_label.setText("플레이어 점수 :" + str(0))
            self.player3_name_label.update()
            self.player3_point_label.update()

        if player_num == 4:
            self.player3_name_label.setText("플레이어 이름 : " + dic_player_list['2'])
            self.player3_point_label.setText("플레이어 점수 :" + str(0))
            self.player3_name_label.update()
            self.player3_point_label.update()
            self.player4_name_label.setText("플레이어 이름 : " + dic_player_list['3'])
            self.player4_point_label.setText("플레이어 점수 :" + str(0))
            self.player4_name_label.update()
            self.player4_point_label.update()

        print("자원카드, 보너스카드 부분")
        # 자원, 보너스카드 부분 초기화
        for i in range(6):
            self.player1_rsc_num_slot[i].setText(str(0))
            self.player1_rsc_num_slot[i].update()
        for i in range(6):
            self.player2_rsc_num_slot[i].setText(str(0))
            self.player2_rsc_num_slot[i].update()
        if 2 in dic_player_list:
            for i in range(6):
                self.player3_rsc_num_slot[i].setText(str(0))
                self.player3_rsc_num_slot[i].update()
        if 3 in dic_player_list:
            for i in range(6):
                self.player4_rsc_num_slot[i].setText(str(0))
                self.player4_rsc_num_slot[i].update()

        print("뱅크자원 부분")
        # bank rsc 업데이트
        print("뱅크자원 넘기기", dic_bank["rsc"][0])
        self.dia_number.setText(str(dic_bank["rsc"][0]))
        self.eme_number.setText(str(dic_bank["rsc"][1]))
        self.cho_number.setText(str(dic_bank["rsc"][2]))
        self.rby_number.setText(str(dic_bank["rsc"][3]))
        self.spr_number.setText(str(dic_bank["rsc"][4]))
        self.gld_number.setText(str(dic_bank["rsc"][5]))
        self.dia_number.update()
        self.eme_number.update()
        self.cho_number.update()
        self.rby_number.update()
        self.spr_number.update()
        self.gld_number.update()

        print("보너스카드 부분")
        # 보너스카드 설정
        for i in range(5):
            self.player1_normal_cards_num_slot[i].setText(str(0))
            self.player1_normal_cards_num_slot[i].update()
        for i in range(5):
            self.player2_normal_cards_num_slot[i].setText(str(0))
            self.player2_normal_cards_num_slot[i].update()
        if '2' in dic_player_list:
            for i in range(5):
                self.player3_normal_cards_num_slot[i].setText(str(0))
                self.player3_normal_cards_num_slot[i].update()
        if '3' in dic_player_list:
            for i in range(5):
                self.player4_normal_cards_num_slot[i].setText(str(0))
                self.player4_normal_cards_num_slot[i].update()

    def resources_view_update(self, all_list):
        # 자원 뷰 전달 [[플레이어 자원 인트 리스트],, ... 마지막 [뱅크 자원 인트 리스트]]
        print("자원 뷰 넘어가나?")
        rsc_list = all_list[0]
        my_num = all_list[1]
        num_list = all_list[2]

        for i, rsc in enumerate(rsc_list[my_num]):
            self.player1_rsc_num_slot[i].setText(str(rsc))
            self.player1_rsc_num_slot[i].update()
        for i, rsc in enumerate(rsc_list[num_list[0]]):
            self.player2_rsc_num_slot[i].setText(str(rsc))
            self.player2_rsc_num_slot[i].update()
        if len(rsc_list) > 3:
            for i, rsc in enumerate(rsc_list[num_list[1]]):
                self.player3_rsc_num_slot[i].setText(str(rsc))
                self.player3_rsc_num_slot[i].update()
        if len(rsc_list) > 4:
            for i, rsc in enumerate(rsc_list[num_list[2]]):
                self.player4_rsc_num_slot[i].setText(str(rsc))
                self.player4_rsc_num_slot[i].update()

        print("뱅크 rcs 업데이트 넘어가나?")
        # bank rsc 업데이트
        self.dia_number.setText(str(rsc_list[-1][0]))
        self.eme_number.setText(str(rsc_list[-1][1]))
        self.cho_number.setText(str(rsc_list[-1][2]))
        self.rby_number.setText(str(rsc_list[-1][3]))
        self.spr_number.setText(str(rsc_list[-1][4]))
        self.gld_number.setText(str(rsc_list[-1][5]))
        self.dia_number.update()
        self.eme_number.update()
        self.cho_number.update()
        self.rby_number.update()
        self.spr_number.update()
        self.gld_number.update()

    def buy_card_view_modification(self, all_list):
        print("바닥뷰 모디인가?")
        list_of_all = all_list[0]
        my_num = all_list[1]
        num_list = all_list[2]

        player_card_list = list_of_all[0]
        bank_card_list = list_of_all[1]

        print("은행뷰 넘어가나?")
        # 은행 뷰
        for i, pic_name in enumerate(bank_card_list[0]):
            if pic_name != None:
                self.lv1_slot[i].setIcon(QIcon(RESOURCES_IMAGE_PATH + pic_name + str(".jpeg")))
                self.lv1_slot[i].update()
            else:
                self.lv1_slot[i].setIcon(QIcon())
                self.lv1_slot[i].update()
        for i, pic_name in enumerate(bank_card_list[1]):
            if pic_name != None:
                self.lv2_slot[i].setIcon(QIcon(RESOURCES_IMAGE_PATH + pic_name + str(".jpeg")))
                self.lv2_slot[i].update()
            else:
                self.lv2_slot[i].setIcon(QIcon())
                self.lv2_slot[i].update()
        for i, pic_name in enumerate(bank_card_list[2]):
            if pic_name != None:
                self.lv3_slot[i].setIcon(QIcon(RESOURCES_IMAGE_PATH + pic_name + str(".jpeg")))
                self.lv3_slot[i].update()
            else:
                self.lv3_slot[i].setIcon(QIcon())
                self.lv3_slot[i].update()

        print("플레이어 뷰 넘어가나?")
        # 플레이어 뷰 - 보너스카드 업데이트
        bonuslist1 = player_card_list[my_num]
        for i, val in enumerate(bonuslist1):
            self.player1_normal_cards_num_slot[i].setText(str(val))
            self.player1_normal_cards_num_slot[i].update()
        bonuslist2 = player_card_list[num_list[0]]
        for i, val in enumerate(bonuslist2):
            self.player2_normal_cards_num_slot[i].setText(str(val))
            self.player2_normal_cards_num_slot[i].update()
        if len(player_card_list) > 2:
            bonuslist3 = player_card_list[num_list[1]]
            for i, val in enumerate(bonuslist3):
                self.player3_normal_cards_num_slot[i].setText(str(val))
                self.player3_normal_cards_num_slot[i].update()
        if len(player_card_list) > 3:
            bonuslist4 = player_card_list[num_list[2]]
            for i, val in enumerate(bonuslist4):
                self.player4_normal_cards_num_slot[i].setText(str(val))
                self.player4_normal_cards_num_slot[i].update()

    def reservation_view_modification(self, all_list):
        # 예약카드 뷰 정보 전달 [플레이어별 예약카드번호 인트 리스트 [], [], ...]
        reservation_list = all_list[0]
        my_num = all_list[1]
        num_list = all_list[2]

        print("예약뷰 모디인가?")
        for i in range(3):
            self.player1_reservation_card_slot[i].setIcon(QIcon())
            self.player2_reservation_card_slot[i].setIcon(QIcon())
            self.player3_reservation_card_slot[i].setIcon(QIcon())
            self.player4_reservation_card_slot[i].setIcon(QIcon())
            self.player1_reservation_card_slot[i].setEnabled(False)
            self.player1_reservation_card_slot[i].update()
            self.player2_reservation_card_slot[i].update()
            self.player3_reservation_card_slot[i].update()
            self.player4_reservation_card_slot[i].update()

        for i, pic_name in enumerate(reservation_list[my_num]):
            if pic_name is not None:
                self.player1_reservation_card_slot[i].setIcon(QIcon(RESOURCES_IMAGE_PATH + pic_name + str(".jpeg")))
                self.player1_reservation_card_slot[i].setIconSize(QSize(130, 130))
                self.player1_reservation_card_slot[i].setEnabled(True)
                self.player1_reservation_card_slot[i].update()
            else:
                self.player1_reservation_card_slot[i].setIcon(QIcon())
                self.player1_reservation_card_slot[i].setIconSize(QSize(130, 130))
                self.player1_reservation_card_slot[i].update()
        for i, pic_name in enumerate(reservation_list[num_list[0]]):
            if pic_name is not None:
                self.player2_reservation_card_slot[i].setIcon(
                    QIcon(RESOURCES_IMAGE_PATH + pic_name + str(".jpeg")))
                self.player2_reservation_card_slot[i].setIconSize(QSize(130, 130))
                self.player2_reservation_card_slot[i].update()
            else:
                self.player2_reservation_card_slot[i].setIcon(QIcon())
                self.player2_reservation_card_slot[i].setIconSize(QSize(130, 130))
                self.player2_reservation_card_slot[i].update()
        if len(reservation_list) >= 3:
            for i, pic_name in enumerate(reservation_list[num_list[1]]):
                if pic_name is not None:
                    self.player3_reservation_card_slot[i].setIcon(
                    QIcon(RESOURCES_IMAGE_PATH + pic_name + str(".jpeg")))
                    self.player3_reservation_card_slot[i].setIconSize(QSize(130, 130))
                    self.player3_reservation_card_slot[i].update()
                else:
                    self.player3_reservation_card_slot[i].setIcon(QIcon())
                    self.player3_reservation_card_slot[i].setIconSize(QSize(130, 130))
                    self.player3_reservation_card_slot[i].update()
        if len(reservation_list) >= 4:
            for i, pic_name in enumerate(reservation_list[num_list[2]]):
                if pic_name is not None:
                    self.player4_reservation_card_slot[i].setIcon(
                        QIcon(RESOURCES_IMAGE_PATH + pic_name + str(".jpeg")))
                    self.player4_reservation_card_slot[i].setIconSize(QSize(130, 130))
                    self.player4_reservation_card_slot[i].update()
                else:
                    self.player4_reservation_card_slot[i].setIcon(QIcon())
                    self.player4_reservation_card_slot[i].setIconSize(QSize(130, 130))
                    self.player4_reservation_card_slot[i].update()

    def celestial_view_modification(self, all_list):
        print("천상뷰 모디인가?")
        # 천상계 뷰 전달 [[플레이어 천상계 인트 카드번호 리스트], ... 마지막 [뱅크 천상계 인트 카드번호 리스트]]
        celestial_list = all_list[0]
        my_num = all_list[1]
        num_list = all_list[2]

        for index in range(5):
            self.celestial_slot[(index)].setPixmap(QPixmap())
            self.celestial_slot[(index)].update()

        for i, pic_name in enumerate(celestial_list[-1]):
            self.celestial_slot[i].setPixmap(QPixmap(RESOURCES_IMAGE_PATH + pic_name + str(".jpeg")).scaled(50, 50))

        if len(celestial_list[my_num]) >= 1:
            self.player1_celestial_cards_slot[(0)].setPixmap(
                QPixmap(RESOURCES_IMAGE_PATH + celestial_list[my_num][0] + str(".jpeg")).scaled(50, 50))
            self.player1_celestial_cards_slot[(0)].update()
            if len(celestial_list[my_num]) >= 2:
                self.player1_celestial_cards_slot[(1)].setPixmap(
                    QPixmap(RESOURCES_IMAGE_PATH + celestial_list[my_num][1] + str(".jpeg")).scaled(50, 50))
                self.player1_celestial_cards_slot[(1)].update()
                if len(celestial_list[my_num]) >= 3:
                    self.player1_celestial_cards_slot[(2)].setPixmap(
                        QPixmap(RESOURCES_IMAGE_PATH + celestial_list[my_num][2] + str(".jpeg")).scaled(50, 50))
                    self.player1_celestial_cards_slot[(2)].update()
                    if len(celestial_list[my_num]) >= 4:
                        self.player1_celestial_cards_slot[(3)].setPixmap(
                            QPixmap(RESOURCES_IMAGE_PATH + celestial_list[my_num][3] + str(".jpeg")).scaled(50, 50))
                        self.player1_celestial_cards_slot[(3)].update()
                        if len(celestial_list[my_num]) == 5:
                            self.player1_celestial_cards_slot[(4)].setPixmap(
                                QPixmap(RESOURCES_IMAGE_PATH + celestial_list[my_num][4] + str(".jpeg")).scaled(50, 50))
                            self.player1_celestial_cards_slot[(4)].update()

        if len(celestial_list[num_list[0]]) >= 1:
            self.player2_celestial_cards_slot[(0)].setPixmap(
                QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[0]][0] + str(".jpeg")).scaled(50, 50))
            self.player2_celestial_cards_slot[(0)].update()
            if len(celestial_list[num_list[0]]) >= 2:
                self.player2_celestial_cards_slot[(1)].setPixmap(
                    QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[0]][1] + str(".jpeg")).scaled(50, 50))
                self.player2_celestial_cards_slot[(1)].update()
                if len(celestial_list[num_list[0]]) >= 3:
                    self.player2_celestial_cards_slot[(2)].setPixmap(
                        QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[0]][2] + str(".jpeg")).scaled(50, 50))
                    self.player2_celestial_cards_slot[(2)].update()
                    if len(celestial_list[num_list[0]]) >= 4:
                        self.player2_celestial_cards_slot[(3)].setPixmap(
                            QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[0]][3] + str(".jpeg")).scaled(50, 50))
                        self.player2_celestial_cards_slot[(3)].update()
                        if len(celestial_list[num_list[0]]) == 5:
                            self.player2_celestial_cards_slot[(4)].setPixmap(
                                QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[0]][4] + str(".jpeg")).scaled(50, 50))
                            self.player2_celestial_cards_slot[(4)].update()

        if len(celestial_list) > 3:
            if len(celestial_list[num_list[1]]) >= 1:
                self.player3_celestial_cards_slot[(0)].setPixmap(
                    QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[1]][0] + str(".jpeg")).scaled(50, 50))
                self.player3_celestial_cards_slot[(0)].update()
                if len(celestial_list[num_list[1]]) >= 2:
                    self.player3_celestial_cards_slot[(1)].setPixmap(
                        QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[1]][1] + str(".jpeg")).scaled(50, 50))
                    self.player3_celestial_cards_slot[(1)].update()
                    if len(celestial_list[num_list[1]]) >= 3:
                        self.player3_celestial_cards_slot[(2)].setPixmap(
                            QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[1]][2] + str(".jpeg")).scaled(50, 50))
                        self.player3_celestial_cards_slot[(2)].update()
                        if len(celestial_list[num_list[1]]) >= 4:
                            self.player3_celestial_cards_slot[(3)].setPixmap(
                                QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[1]][3] + str(".jpeg")).scaled(50, 50))
                            self.player3_celestial_cards_slot[(3)].update()
                            if len(celestial_list[num_list[1]]) == 5:
                                self.player3_celestial_cards_slot[(4)].setPixmap(
                                    QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[1]][4] + str(".jpeg")).scaled(50, 50))
                                self.player3_celestial_cards_slot[(4)].update()

        if len(celestial_list) > 4:
            if len(celestial_list[num_list[2]]) == 1:
                self.player4_celestial_cards_slot[(0)].setPixmap(
                    QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[2]][0] + str(".jpeg")).scaled(50, 50))
                self.player4_celestial_cards_slot[(0)].update()
                if len(celestial_list[num_list[2]]) >= 2:
                    self.player4_celestial_cards_slot[(1)].setPixmap(
                        QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[2]][1] + str(".jpeg")).scaled(50, 50))
                    self.player4_celestial_cards_slot[(1)].update()
                    if len(celestial_list[num_list[2]]) >= 3:
                        self.player4_celestial_cards_slot[(2)].setPixmap(
                            QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[2]][2] + str(".jpeg")).scaled(50, 50))
                        self.player4_celestial_cards_slot[(2)].update()
                        if len(celestial_list[num_list[2]]) >= 4:
                            self.player4_celestial_cards_slot[(3)].setPixmap(
                                QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[2]][3] + str(".jpeg")).scaled(50, 50))
                            self.player4_celestial_cards_slot[(3)].update()
                            if len(celestial_list[num_list[2]]) == 5:
                                self.player4_celestial_cards_slot[(4)].setPixmap(
                                    QPixmap(RESOURCES_IMAGE_PATH + celestial_list[num_list[2]][4] + str(".jpeg")).scaled(50, 50))
                                self.player4_celestial_cards_slot[(4)].update()

    def points_view_modification(self, all_list):
        points_list = all_list[0]
        my_num = all_list[1]
        num_list = all_list[2]

        print("포인트뷰 모디인가?")
        self.player1_point_label.setText(str(points_list[my_num]))
        self.player1_point_label.update()
        self.player2_point_label.setText(str(points_list[num_list[0]]))
        self.player2_point_label.update()
        if len(points_list) > 2:
            self.player3_point_label.setText(str(points_list[num_list[1]]))
            self.player3_point_label.update()
        if len(points_list) > 3:
            self.player4_point_label.setText(str(points_list[num_list[2]]))
            self.player4_point_label.update()


class YesNoBox(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("선택")

    def choice(self, text=""):
        self.choice = QMessageBox.question(self, '선택', text, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return self.choice


class WinnerNotificationBox(QDialog):
    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout()

        self.title = QHBoxLayout()
        self.player1 = QHBoxLayout()
        self.player2 = QHBoxLayout()
        self.player3 = QHBoxLayout()
        self.player4 = QHBoxLayout()
        self.info = QHBoxLayout()
        self.quit = QHBoxLayout()

        self.main_layout.addLayout(self.title)
        self.main_layout.addLayout(self.player1)
        self.main_layout.addLayout(self.player2)
        self.main_layout.addLayout(self.player3)
        self.main_layout.addLayout(self.player4)
        self.main_layout.addLayout(self.info)
        self.main_layout.addLayout(self.quit)

        self.name_widget = {}
        self.points_widget = {}
        self.card_num_widget = {}

        self.info_content = QLabel("")
        self.info.addWidget(self.info_content)

        self.quit_button = QPushButton("게임을 종료합니다")
        self.quit.addWidget(self.quit_button)

        self.setLayout(self.main_layout)

    @pyqtSlot(list)
    def set_content(self, list_from):
        player_list = list_from[0]
        points = list_from[1]
        card_num = list_from[2]

        for i in range(len(player_list)):
            self.name_widget[i] = QLabel()
            self.points_widget[i] = QLabel()
            self.card_num_widget[i] = QLabel()

        for i in range(len(player_list)):
            self.main_layout.itemAt(i + 1).addWidget(self.name_widget[i])
            self.main_layout.itemAt(i + 1).addWidget(self.points_widget[i])
            self.main_layout.itemAt(i + 1).addWidget(self.card_num_widget[i])

        for i in range(len(player_list)):
            print("플레이어 리스트", self.name_widget, player_list)
            self.name_widget[i].setText(player_list[str(i)] + " : ")
            self.points_widget[i].setText("점수 : " + str(points[i]))
            self.card_num_widget[i].setText("천상계 제외 소유 카드 갯수 : " + str(card_num[i]))
            self.name_widget[i].update()
            self.points_widget[i].update()
            self.card_num_widget[i].update()

        # text = self.winner(player_list, points, card_num)

        highest = max(points)
        winner_keys = []
        for i in range(len(points)):
            if points[i] >= highest:
                winner_keys.append(i)

        print("1번 부분")
        if len(winner_keys) > 1:
            smallest_key = 0
            for i in winner_keys:
                if card_num[smallest_key] >= card_num[i]:
                    smallest_key = i
            final_winner_keys = []
            smallest = card_num[smallest_key]
            print("2번 부분")
            for i in winner_keys:
                if smallest >= card_num[i]:
                    final_winner_keys.append(i)
            print("3번 부분")
            if len(final_winner_keys) > 1:
                final_text = "점수와 보유 카드 숫자가 동률이므로 "
                print("4번 부분")
                for i in final_winner_keys:
                    print("5번 부분")
                    final_text += str(player_list[str(i)] + ", ")
                    print("6번 부분")
                final_text += "님이 공동 우승하셨습니다"
                text = final_text
                print("7번 부분")
            else:
                print("8번 부분")
                text = "점수는 동일하나 보유 카드 숫자가 더 적으므로 우승자는 " + str(player_list[str(final_winner_keys[0])]) + "님 입니다"
        else:
            text = "우승자는" + str(player_list[str(winner_keys[0])]) + "님 입니다"

        print("셋콘텐트 전")
        self.info_content.setText(text)
        self.info_content.update()

        print("윈도우모달리티")
        self.setWindowModality(Qt.ApplicationModal)
        self.exec_()


class CelestialitySelectionBox(QDialog):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        self.title = QLabel("축하합니다. 천상계가 강림하였습니다! 실수는 용납되지 않으니 신중히 선택하십시오")
        self.layout.addWidget(self.title)
        self.title.setAlignment(Qt.AlignCenter)

        self.pic_layout = QHBoxLayout()
        self.layout.addLayout(self.pic_layout)

        self.setWindowTitle("천상계 강림")

        self.setLayout(self.layout)

        self.id_list = None
        self.pic_widget = {}
        for i in range(5):
            self.pic_widget[i] = QPushButton()
            self.pic_layout.addWidget(self.pic_widget[i])

    @pyqtSlot(list)
    def show_up(self, id_list):
        # 초기화
        self.id_list = id_list
        for i in range(5):
            self.pic_widget[i].setIcon(QIcon())
            self.pic_widget[i].setEnabled(False)
            self.pic_widget[i].update()

        if len(id_list) > 1:
            self.informative_word = QLabel("아쉽지만 한번에 한 명의 천상계만을 선택할 수 있습니다. 원하는 카드를 선택하십시오")
            self.informative_word.update()
            self.layout.addWidget(self.informative_word)
            self.informative_word.setAlignment(Qt.AlignCenter)
        else:
            self.informative_word = QLabel("카드를 선택하고 턴을 넘기십시오")
            self.informative_word.update()
            self.layout.addWidget(self.informative_word)
            self.informative_word.setAlignment(Qt.AlignCenter)

        for i, id in enumerate(id_list):
            self.pic_widget[i].setIcon(QIcon(RESOURCES_IMAGE_PATH + id + str(".jpeg")))
            self.pic_widget[i].setEnabled(True)
            self.pic_widget[i].setStyleSheet("border: none")
            self.pic_widget[i].setIconSize(QSize(300, 300))
            self.pic_widget[i].update()

        self.setWindowModality(Qt.ApplicationModal)
        self.exec_()

    # def closeEvent(self, event):
    #     if self.close_variable == 1:
    #         event.accept()
    #         self.close_variable = 0
    #     elif self.close_variable  == 0:
    #         event.ignore()
    #
    # def close_variable_handler(self):
    #     self.close_variable = 1


class ResourcesSelectionBox(QDialog):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()

        self.layout_design()
        self.widget_design()

        self.setLayout(self.main_layout)

        # self.show()
        # self.setWindowModality(Qt.ApplicationModal)
        # self.exec_()

    def layout_design(self):
        self.title_layout = QHBoxLayout()
        self.selection_layout = QHBoxLayout()
        self.choice_layout = QHBoxLayout()
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addLayout(self.selection_layout)
        self.main_layout.addLayout(self.choice_layout)

        self.dia_selection_layout = QVBoxLayout()
        self.eme_selection_layout = QVBoxLayout()
        self.cho_selection_layout = QVBoxLayout()
        self.rby_selection_layout = QVBoxLayout()
        self.spr_selection_layout = QVBoxLayout()
        self.gld_selection_layout = QVBoxLayout()
        self.dia_selection_layout.setAlignment(Qt.AlignCenter)
        self.eme_selection_layout.setAlignment(Qt.AlignCenter)
        self.cho_selection_layout.setAlignment(Qt.AlignCenter)
        self.rby_selection_layout.setAlignment(Qt.AlignCenter)
        self.spr_selection_layout.setAlignment(Qt.AlignCenter)
        self.gld_selection_layout.setAlignment(Qt.AlignCenter)

        self.selection_layout.addLayout(self.dia_selection_layout)
        self.selection_layout.addLayout(self.eme_selection_layout)
        self.selection_layout.addLayout(self.cho_selection_layout)
        self.selection_layout.addLayout(self.rby_selection_layout)
        self.selection_layout.addLayout(self.spr_selection_layout)
        self.selection_layout.addLayout(self.gld_selection_layout)

    def widget_design(self):
        self.title = QLabel("낼 자원/받을 자원을 선택하세요. 황금자원을 얻으려면 카드 예약이 필요합니다")
        self.title_layout.addWidget(self.title)

        self.dia_selection_label = QLabel()
        self.dia_selection_box = QSpinBox()
        self.eme_selection_label = QLabel()
        self.eme_selection_box = QSpinBox()
        self.cho_selection_label = QLabel()
        self.cho_selection_box = QSpinBox()
        self.rby_selection_label = QLabel()
        self.rby_selection_box = QSpinBox()
        self.spr_selection_label = QLabel()
        self.spr_selection_box = QSpinBox()
        self.gld_selection_label = QLabel()
        self.gld_selection_box = QSpinBox()

        self.dia_selection_label.setPixmap(
            QPixmap(RESOURCES_IMAGE_PATH + "dia-token.png").scaled(100, 100, Qt.KeepAspectRatio,
                                                                   Qt.SmoothTransformation))
        self.eme_selection_label.setPixmap(
            QPixmap(RESOURCES_IMAGE_PATH + "eme-token.jpg").scaled(100, 100, Qt.KeepAspectRatio,
                                                                   Qt.SmoothTransformation))
        self.cho_selection_label.setPixmap(
            QPixmap(RESOURCES_IMAGE_PATH + "cho-token.png").scaled(100, 100, Qt.KeepAspectRatio,
                                                                   Qt.SmoothTransformation))
        self.rby_selection_label.setPixmap(
            QPixmap(RESOURCES_IMAGE_PATH + "rby-token.png").scaled(100, 100, Qt.KeepAspectRatio,
                                                                   Qt.SmoothTransformation))
        self.spr_selection_label.setPixmap(
            QPixmap(RESOURCES_IMAGE_PATH + "spr-token.jpg").scaled(100, 100, Qt.KeepAspectRatio,
                                                                   Qt.SmoothTransformation))
        self.gld_selection_label.setPixmap(
            QPixmap(RESOURCES_IMAGE_PATH + "gld-token.png").scaled(100, 100, Qt.KeepAspectRatio,
                                                                   Qt.SmoothTransformation))

        self.dia_selection_box.setMinimum(0)
        self.eme_selection_box.setMinimum(0)
        self.cho_selection_box.setMinimum(0)
        self.rby_selection_box.setMinimum(0)
        self.spr_selection_box.setMinimum(0)
        self.gld_selection_box.setMinimum(0)

        self.dia_selection_layout.addWidget(self.dia_selection_label)
        self.dia_selection_layout.addWidget(self.dia_selection_box)
        self.eme_selection_layout.addWidget(self.eme_selection_label)
        self.eme_selection_layout.addWidget(self.eme_selection_box)
        self.cho_selection_layout.addWidget(self.cho_selection_label)
        self.cho_selection_layout.addWidget(self.cho_selection_box)
        self.rby_selection_layout.addWidget(self.rby_selection_label)
        self.rby_selection_layout.addWidget(self.rby_selection_box)
        self.spr_selection_layout.addWidget(self.spr_selection_label)
        self.spr_selection_layout.addWidget(self.spr_selection_box)
        self.gld_selection_layout.addWidget(self.gld_selection_label)
        self.gld_selection_layout.addWidget(self.gld_selection_box)

        self.selection_fix_button = QPushButton("선택")
        self.cancel_button = QPushButton("나가기")
        self.choice_layout.addWidget(self.selection_fix_button)
        self.choice_layout.addWidget(self.cancel_button)

        self.cancel_button.clicked.connect(self.close)

    def selection(self):
        return [self.dia_selection_box.value(), self.eme_selection_box.value(), self.cho_selection_box.value(),
                self.rby_selection_box.value(), self.spr_selection_box.value(), self.gld_selection_box.value()]

    def initialize(self):
        self.dia_selection_box.setValue(0)
        self.eme_selection_box.setValue(0)
        self.cho_selection_box.setValue(0)
        self.rby_selection_box.setValue(0)
        self.spr_selection_box.setValue(0)
        self.gld_selection_box.setValue(0)


class CardSelectionBox(QDialog):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()

        self.title_layout = QHBoxLayout()
        self.choice_layout = QHBoxLayout()
        self.quit_layout = QHBoxLayout()

        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addLayout(self.choice_layout)
        self.main_layout.addLayout(self.quit_layout)

        self.title = QLabel("카드를 구매하시겠습니까 예약하시겠습니까?")

        self.buy_card_button = QPushButton("구매하기")

        self.reservation_card = QPushButton("예약하기")
        reservation_icon = QIcon(RESOURCES_IMAGE_PATH + "gld.png")
        self.reservation_card.setIcon(reservation_icon)

        self.quit = QPushButton("자원 선택으로 돌아가기")

        self.title_layout.addWidget(self.title)
        self.choice_layout.addWidget(self.buy_card_button)
        self.choice_layout.addWidget(self.reservation_card)
        self.quit_layout.addWidget(self.quit)

        self.setLayout(self.main_layout)
        self.quit.clicked.connect(self.close)
        # self.setWindowModality(Qt.ApplicationModal)
        # self.exec_()


class Controller:
    def __init__(self):
        self.player_list = {}
        self.player_num_trans = []
        # 실험
        self.variable = 0
        ####
        self.main_widget = MainWidget()
        self.entrance = EntranceWidget()
        self.wait_room = WaitingRoom()
        self.game_widget = GameWidget()
        self.winner_notification_widget = WinnerNotificationBox()

        self.yes_no_box = YesNoBox()

        self.reinput_noti_box = Notification()
        self.wait_box = Notification()
        self.noti_box = Notification()
        self.turn_over_noti_box = Notification()
        self.end_warning_box = Notification()

        self.celestiality_selection_box = CelestialitySelectionBox()

        self.resources_selection_box = ResourcesSelectionBox()

        self.buy_card_resources_box = ResourcesSelectionBox()
        self.card_selection_box = CardSelectionBox()

        self.buy_reservation_resources_box = ResourcesSelectionBox()
        self.reservation_selection_box = CardSelectionBox()

        self.main_widget.central_widget.addWidget(self.entrance)
        self.main_widget.central_widget.addWidget(self.wait_room)
        self.main_widget.central_widget.addWidget(self.game_widget)

        self.user_login()

        self.reinput_noti_box.button.clicked.connect(self.reinput_noti_box.hide)
        self.wait_box.button.clicked.connect(self.wait_box.hide)
        self.noti_box.button.clicked.connect(self.noti_box.hide)
        self.turn_over_noti_box.button.clicked.connect(self.turn_over_noti_box.hide)
        self.end_warning_box.button.clicked.connect(self.end_warning_box.hide)

        self.entrance.next_page.clicked.connect(self.user_name_check)
        self.wait_room.start_button.clicked.connect(self.send_for_start)
        self.winner_notification_widget.quit_button.clicked.connect(self.game_over)

        # 자원선택박스 팝업
        self.game_widget.dia_graphic.clicked.connect(self.resources_selection)
        self.game_widget.eme_graphic.clicked.connect(self.resources_selection)
        self.game_widget.cho_graphic.clicked.connect(self.resources_selection)
        self.game_widget.rby_graphic.clicked.connect(self.resources_selection)
        self.game_widget.spr_graphic.clicked.connect(self.resources_selection)
        self.game_widget.gld_graphic.clicked.connect(self.resources_selection)

        # 바닥카드선택 팝업 부분
        for i in range(4):
            self.game_widget.lv1_slot[i].clicked.connect(partial(self.card_selection, i, 1))
            self.game_widget.lv2_slot[i].clicked.connect(partial(self.card_selection, i, 2))
            self.game_widget.lv3_slot[i].clicked.connect(partial(self.card_selection, i, 3))

        # 예약카드슬롯 팝업 부분
        for i in range(3):
            self.game_widget.player1_reservation_card_slot[i].clicked.connect(
                partial(self.reservation_card_selection, i, 0))

        # 자원확정 선택
        self.resources_selection_box.selection_fix_button.clicked.connect(self.resources_selection_midpoint)

        # 카드선택 후 구매/예약박스에서 카드예약 선택
        self.card_selection_box.reservation_card.clicked.connect(self.reserve_card_midpoint)
        # 카드선택 후 구매/예약박스에서 카드구매 선택
        self.card_selection_box.buy_card_button.clicked.connect(self.buy_card_resources_box_show_up)
        # 카드선택 후 구매/예약박스에서 카드구매 선택 후 자원선택박스에서 자원최종선택
        self.buy_card_resources_box.selection_fix_button.clicked.connect(self.buy_card_midpoint)

        # 예약카드선택 후 구매/예약박스에서 카드구매 선택
        self.reservation_selection_box.buy_card_button.clicked.connect(self.buy_reservation_resources_box_show_up)
        # 예약카드선택 후 구매/예약박스에서 카드구매 선택 후 자원선택박스에서 자원최종선택
        self.buy_reservation_resources_box.selection_fix_button.clicked.connect(self.reservation_card_buy_midpoint)

        # 천상계 선택
        for i in range(5):
            self.celestiality_selection_box.pic_widget[i].clicked.connect(partial(self.celestiality_selection_midpoint, i))

    def user_login(self):
        # self.entrance.show()
        # self.main_widget.menubar.hide()
        self.main_widget.central_widget.setCurrentWidget(self.entrance)
        # self.entrance.show()

    def user_name_check(self):
        input_text = self.entrance.player_input_line.text()
        input_text = input_text.strip().replace(" ", "")
        if len(input_text) >= 10:
            self.notification_box.show_up("ID는 10자 미만이어야 합니다")
        else:
            dic = {"요청": "유저등록", "이름": input_text}
            chat.send_message(dic)

    def num_list_calculator(self):
        self.my_original_num = len(self.original_dic) - 1
        self.num_list = [0, 1, 2, 3]
        self.num_list.remove(self.my_original_num)
        print(self.my_original_num, self.num_list)

    def user_enroll(self, dic_type):
        self.original_dic = dic_type

        if dic_type['0'] == self.my_name and len(dic_type) >= 2:
            self.wait_room.start_button.setEnabled(True)

        original_list = []
        for i in self.player_list:
            original_list.append(self.player_list[str(i)])

        for i in dic_type:
            num = len(self.player_list)
            if dic_type[i] in original_list:
                continue
            self.player_list[str(num)] = dic_type[i]

    def wait_for_the_game(self, dic_type):
        self.my_name = self.entrance.player_input_line.text().strip().replace(" ", "")
        self.player_list['0'] = self.my_name
        # self.entrance.hide()
        # self.wait_room.show()
        self.main_widget.central_widget.setCurrentWidget(self.wait_room)
        self.wait_room.view_modifier(dic_type)

    def send_for_start(self):
        dic = {"요청": "시작"}
        chat.send_message(dic)

    def start_the_game(self):
        self.main_widget.central_widget.setCurrentWidget(self.game_widget)

    def card_selection(self, slot_num, card_level):
        self.card_selection_box.reservation_card.setEnabled(True)
        self.card_selection_box.show()
        self.slot_num = slot_num
        self.card_level = card_level
        # self.card_selection_box.buy_card_button.clicked.connect(partial(self.buy_card_midpoint, slot_num, card_level))
        # self.card_selection_box.reservation_card.clicked.connect(
        #     partial(self.reserve_card_midpoint, slot_num, card_level))

    def buy_card_resources_box_show_up(self):
        self.buy_card_resources_box.show()

    def buy_reservation_resources_box_show_up(self):
        self.buy_reservation_resources_box.show()

    def buy_card_midpoint(self):
        self.card_selection_box.hide()
        self.buy_card_resources_box.hide()
        dic = {"요청": "카드구매", "보낸이": self.my_name, "슬롯번호": self.slot_num, "카드레벨": self.card_level, "자원선택": self.buy_card_resources_box.selection()}
        chat.send_message(dic)

    def reserve_card_midpoint(self):
        self.card_selection_box.hide()
        dic = {"요청": "카드예약", "보낸이": self.my_name, "슬롯번호": self.slot_num, "카드레벨": self.card_level}
        chat.send_message(dic)

    def reservation_card_selection(self, reservation_slot_num, reservation_card_level):
        print("예약카드 슬롯을 클릭함")
        self.slot_num = reservation_slot_num
        self.card_level = reservation_card_level
        self.reservation_selection_box.reservation_card.setEnabled(False)
        self.reservation_selection_box.show()
        # self.card_selection_box.buy_card_button.clicked.connect(
        #     partial(self.reservation_card_buy_midpoint, reservation_slot_num, player_index))

    def reservation_card_buy_midpoint(self):
        self.reservation_selection_box.hide()
        self.buy_reservation_resources_box.hide()
        dic = {"요청": "예약카드구매", "보낸이": self.my_name, "예약카드슬롯번호": self.slot_num, "예약카드레벨": self.card_level, "자원선택": self.buy_reservation_resources_box.selection()}
        chat.send_message(dic)

    def resources_selection(self):
        self.resources_selection_box.show()
        # self.resources_selection_box.selection_fix_button.clicked.connect(
        #     partial(self.resources_selection_midpoint, self.resources_selection_box))

    def resources_selection_midpoint(self):
        self.resources_selection_box.hide()
        dic = {"요청": "자원채취", "보낸이": self.my_name, "자원선택": self.resources_selection_box.selection()}
        chat.send_message(dic)

    # @pyqtSlot(list)
    # def celestiality_selection(self, id_list):
    #     self.celestiality_selection_box.show_up(id_list)
        # for i, id in enumerate(id_list):
        #     self.pic_widget[i].clicked.connect(partial(self.celestiality_selection_midpoint, id, self))

    def celestiality_selection_midpoint(self, card_order):
        self.celestiality_selection_box.close()
        dic = {"요청": "천상계 선택", "보낸이": self.my_name, "선택카드": self.celestiality_selection_box.id_list[card_order]}
        chat.send_message(dic)

    def game_over(self):
        self.game_widget.close()
        self.main_widget.close()
        self.winner_notification_widget.close()

    def notification(self, text):
        self.notification_box.show_up(text)
        # self.notification_box.show()


class Observer:
    def __init__(self):
        super().__init__()
        self.observing_sth = []
        self.variable = None

    def enroll_sth(self, sth):
        self.observing_sth.append(sth)

    def remove_sth(self, sth):
        self.observing_sth.remove(sth)

    def notify(self):
        for sth in self.observing_sth:
            sth.variable = self.variable


app = QApplication(sys.argv)

controller = Controller()

chat = ChatServer()
thread = Thread(target=chat.runChat)
thread.start()

observer = Observer()

observer.enroll_sth(controller)

sys.exit(app.exec_())


