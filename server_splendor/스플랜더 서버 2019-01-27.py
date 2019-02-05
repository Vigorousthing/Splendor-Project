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
import socketserver
import threading

# from RESOURCES_STR import *
# from RESOURCES_IMAGE import *

import json
sys.excepthook = traceback.print_exception
RESOURCES_IMAGE_PATH = 'resources/images/'

HOST = ""
PORT = 9000
lock = threading.Lock()

class UserManager:  # 사용자관리 및 채팅 메세지 전송을 담당하는 클래스
    # ① 채팅 서버로 입장한 사용자의 등록
    # ② 채팅을 종료하는 사용자의 퇴장 관리
    # ③ 사용자가 입장하고 퇴장하는 관리
    # ④ 사용자가 입력한 메세지를 채팅 서버에 접속한 모두에게 전송

    def __init__(self):
        self.users = {}  # 사용자의 등록 정보를 담을 사전 {사용자 이름:(소켓,주소),...}
        self.users_for_send = {}
        self.userlist_for_send = {}
        # self.users_for_send["유저목록"] = self.userlist_for_send
        # self.users_for_send["지시"] = "유저 입장"

    def addUser(self, player_name, conn, addr):  # 사용자 ID를 self.users에 추가하는 함수
        if player_name in self.users:  # 이미 등록된 사용자라면
            return None

        # 새로운 사용자를 등록함
        lock.acquire()  # 스레드 동기화를 막기위한 락
        self.users[player_name] = (conn, addr)
        self.userlist_for_send[len(self.users)-1] = player_name
        lock.release()  # 업데이트 후 락 해제

        # self.sendMessageToAll(self.userlist_for_send)
        print('+++ 대화 참여자 수 [%d]' % len(self.users))

        return 1

    def removeUser(self, username):  # 사용자를 제거하는 함수
        if username not in self.users:
            return

        lock.acquire()
        del self.users[username]
        del self.userlist_for_send[(len(self.users))]
        lock.release()

        # self.sendMessageToAll(self.users_for_send)
        print('--- 대화 참여자 수 [%d]' % len(self.users))

    # def messageHandler(self, username, msg):  # 전송한 msg를 처리하는 부분
    #     if msg[0] != '/':  # 보낸 메세지의 첫문자가 '/'가 아니면
    #         self.sendMessageToAll('[%s] %s' % (username, msg))
    #         return

    def sendMessageToAll(self, dictionary_type):
        converted = json.dumps(dictionary_type)
        encoded = converted.encode()
        for conn, addr in self.users.values():
            conn.send(encoded)

    def sendMessageToSomeone(self, username, dictionary_type):
        converted = json.dumps(dictionary_type)
        encoded = converted.encode()
        for conn, addr in self.users.values():
            if (conn, addr) == self.users[username]:
                conn.send(encoded)
                break

    def sendMessageToOthers(self, username, dictionary_type):
        converted = json.dumps(dictionary_type)
        encoded = converted.encode()
        for conn, addr in self.users.values():
            if (conn, addr) == self.users[username]:
                print("송신에서 제외되는 유저", username)
                continue
            conn.send(encoded)

class MyTcpHandler(socketserver.BaseRequestHandler):
    USER_ENROLL = 1
    START_GAME = 2
    COLLECT_RESOURCES = 3
    userman = UserManager()

    def handle(self):
        print('[%s] 연결됨' % self.client_address[0])
        # try:
        while 1:
            msg = self.request.recv(1024)
            # lock.acquire()
            decoded = msg.decode()
            recv_converted = json.loads(decoded)
            print("막 리시브해서 변환되었을 때", recv_converted)
            if recv_converted["요청"] == "유저등록":
                player_name = recv_converted["이름"]
                if not self.registerUsername(player_name):
                    dic = {"지시": "재입력", "내용": "같은 ID가 있으니 다른 ID로 만드세요"}
                    jsonobj = json.dumps(dic)
                    encoded = jsonobj.encode()
                    self.userman.sendMessageToSomeone(recv_converted["이름"], encoded)
                dic = {"지시": "대기실 입장", "유저목록": self.userman.userlist_for_send}
                self.userman.sendMessageToSomeone(recv_converted["이름"], dic)
                for_all_dic = {"지시": "신규유저 입장", "유저목록": self.userman.userlist_for_send}
                self.userman.sendMessageToOthers(recv_converted["이름"], for_all_dic)

            elif recv_converted["요청"] == "시작":
                game_controller.start(self.userman.userlist_for_send)
                for_all_dic = {"지시": "게임시작", "은행": {"lv1": game_controller.bank.id_list_extract(game_controller.bank.lv1_card_revealed),
                                                          "lv2": game_controller.bank.id_list_extract(game_controller.bank.lv2_card_revealed),
                                                          "lv3": game_controller.bank.id_list_extract(game_controller.bank.lv3_card_revealed),
                                                          "celestial": game_controller.bank.id_list_extract(game_controller.bank.celestial_card_revealed),
                                                          "rsc": game_controller.bank.possessed_resources.list_extract()}}
                self.userman.sendMessageToAll(for_all_dic)
#---------------------------------------------------------------------------------------------------------------------------------------

            elif recv_converted["요청"] == "자원채취":
                selected_resources = game_controller.rsc_slt_from_client(recv_converted["자원선택"])
                player = game_controller.who_is_it(recv_converted["보낸이"])
                bank = game_controller.bank
                selection_result = game_controller.gameobserver.correct_selection(selected_resources, player, bank)

                # 먼저 사용자가 맞는 턴인지를 확인
                if recv_converted["보낸이"] != game_controller.player_list[game_controller.turn_of_game % game_controller.player_num].name:
                    dic = {"지시": "대기"}
                    self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)
                else:
                    #사용자가 턴 소유자일 경우 로직
                    # 자원선택결과가 올바를 경우
                    if selection_result is True:
                        game_controller.acquire_resources_confirm(selected_resources, player)

                        if game_controller.gameobserver.descent_of_celestiality(player, bank) is not False:

                            possible_cards_list = game_controller.gameobserver.descent_of_celestiality(player, bank)
                            dic = {"가능카드": possible_cards_list}
                            dic["지시"] = "천상계 강림"
                            self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)

                        else:
                            # 천상계가 강림하지 않은 경우
                            game_over_condition = game_controller.game_over_condition
                            player_list = game_controller.player_list
                            game_controller.after_turn()
                            turn = game_controller.turn_of_game

                            # 1) 게임이 바로 종료됨
                            if game_controller.gameobserver.game_over_check(game_over_condition, turn, player_list) == "end":
                                dic = {"지시": "바로 종료"}

                                result = self.view_list_extractor()
                                dic["자원 뷰"] = result[0]
                                dic["예약카드 뷰"] = result[1]
                                dic["바닥카드 뷰"] = result[2]
                                dic["천상계 뷰"] = result[3]
                                dic["포인트 뷰"] = result[4]

                                title_text = "게임 종료조건이 충족되었습니다"
                                points, card_num = game_controller.gameobserver.points_card_num_extractor(
                                    player_list)
                                dic["유저목록"] = self.userman.userlist_for_send
                                dic["포인트"] = points
                                dic["카드개수"] = card_num
                                self.userman.sendMessageToAll(dic)

                            # 2) 이번 턴에 종료
                            elif game_controller.gameobserver.game_over_check(game_over_condition, turn, player_list) == "end soon":
                                dic = {"지시": "이번 턴에 종료"}

                                result = self.view_list_extractor()
                                dic["자원 뷰"] = result[0]
                                dic["예약카드 뷰"] = result[1]
                                dic["바닥카드 뷰"] = result[2]
                                dic["천상계 뷰"] = result[3]
                                dic["포인트 뷰"] = result[4]

                                warning_text = recv_converted["보낸이"] + "님이 " + \
                                               "15점을 달성하여 이번 회에 게임이 종료됩니다. 승리를 넘겨주지 않으려면 서둘러야 합니다" \
                                               + "이번 턴은 " + game_controller.gameobserver.next_player(player_list,
                                                                                                     player) \
                                               + "의 차례입니다"
                                dic["메세지"] = warning_text
                                game_controller.game_over_condition = 1
                                self.userman.sendMessageToAll(dic)

                            # 3) 턴 넘김
                            elif game_controller.gameobserver.game_over_check(game_over_condition, turn, player_list) == "go on":
                                dic = {"지시": "턴 넘김", "순서": player_list[turn % game_controller.player_num].name}
                                result = self.view_list_extractor()
                                dic["자원 뷰"] = result[0]
                                dic["예약카드 뷰"] = result[1]
                                dic["바닥카드 뷰"] = result[2]
                                dic["천상계 뷰"] = result[3]
                                dic["포인트 뷰"] = result[4]

                                print("턴 : ", turn % game_controller.player_num)
                                self.userman.sendMessageToAll(dic)
                    #잘못된 자원선택을 했을 경우
                    else:
                        dic = {"지시": "재입력", "내용": selection_result}
                        self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)

            elif recv_converted["요청"] == "카드구매":
                slot_num = recv_converted["슬롯번호"]
                card_level = recv_converted["카드레벨"]
                player = game_controller.who_is_it(recv_converted["보낸이"])

                payment = recv_converted["자원선택"]
                payment = Resources(payment[0], payment[1], payment[2], payment[3], payment[4], payment[5])

                selected_card = game_controller.card_slt_from_client(card_level, slot_num)

                buy_card_check = game_controller.gameobserver.correct_payment(selected_card, player, payment)

                bank = game_controller.bank

                # 맞는 턴인지 확인
                if recv_converted["보낸이"] != game_controller.player_list[game_controller.turn_of_game % game_controller.player_num].name:
                    dic = {"지시": "대기"}
                    self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)
                else:
                    # 사용자가 턴 소유자일 경우 로직
                    # 카드선택결과가 올바를 경우
                    if buy_card_check is True:
                        game_controller.buy_card_confirm(selected_card, payment, player)

                        if game_controller.gameobserver.descent_of_celestiality(player, bank) is not False:
                            possible_cards_list = game_controller.gameobserver.descent_of_celestiality(player, bank)
                            dic = {"가능카드": possible_cards_list}
                            dic["지시"] = "천상계 강림"
                            self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)

                        else:
                            # 천상계가 강림하지 않은 경우
                            game_over_condition = game_controller.game_over_condition
                            player_list = game_controller.player_list
                            game_controller.after_turn()
                            turn = game_controller.turn_of_game

                            # 1) 게임이 바로 종료됨
                            if game_controller.gameobserver.game_over_check(game_over_condition, turn,
                                                                            player_list) == "end":
                                dic = {"지시": "바로 종료"}

                                result = self.view_list_extractor()
                                dic["자원 뷰"] = result[0]
                                dic["예약카드 뷰"] = result[1]
                                dic["바닥카드 뷰"] = result[2]
                                dic["천상계 뷰"] = result[3]
                                dic["포인트 뷰"] = result[4]

                                title_text = "게임 종료조건이 충족되었습니다"
                                points, card_num = game_controller.gameobserver.points_card_num_extractor(
                                    player_list)
                                dic["유저목록"] = self.userman.userlist_for_send
                                dic["포인트"] = points
                                dic["카드개수"] = card_num
                                self.userman.sendMessageToAll(dic)
                            # 2) 이번 턴에 종료
                            elif game_controller.gameobserver.game_over_check(game_over_condition, turn,
                                                                              player_list) == "end soon":
                                dic = {"지시": "이번 턴에 종료"}

                                result = self.view_list_extractor()
                                dic["자원 뷰"] = result[0]
                                dic["예약카드 뷰"] = result[1]
                                dic["바닥카드 뷰"] = result[2]
                                dic["천상계 뷰"] = result[3]
                                dic["포인트 뷰"] = result[4]

                                warning_text = recv_converted["보낸이"] + "님이 " + \
                                               "15점을 달성하여 이번 회에 게임이 종료됩니다. 승리를 넘겨주지 않으려면 서둘러야 합니다" \
                                               + "이번 턴은 " + game_controller.gameobserver.next_player(player_list,
                                                                                                     player) \
                                               + "의 차례입니다"
                                dic["메세지"] = warning_text
                                game_controller.game_over_condition = 1
                                self.userman.sendMessageToAll(dic)
                            # 3) 턴 넘김
                            elif game_controller.gameobserver.game_over_check(game_over_condition, turn, player_list) == "go on":
                                dic = {"지시": "턴 넘김", "순서": player_list[turn % game_controller.player_num].name}
                                result = self.view_list_extractor()
                                dic["자원 뷰"] = result[0]
                                dic["예약카드 뷰"] = result[1]
                                dic["바닥카드 뷰"] = result[2]
                                dic["천상계 뷰"] = result[3]
                                dic["포인트 뷰"] = result[4]

                                print("턴 : ", turn % game_controller.player_num)
                                self.userman.sendMessageToAll(dic)
                    # 잘못된 카드선택을 했을 경우
                    else:
                        dic = {"지시": "재입력", "내용": buy_card_check}
                        self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)

            elif recv_converted["요청"] == "예약카드구매":
                slot_num = recv_converted["예약카드슬롯번호"]
                card_level = recv_converted["예약카드레벨"]
                player = game_controller.who_is_it(recv_converted["보낸이"])
                payment = recv_converted["자원선택"]
                payment = Resources(payment[0], payment[1], payment[2], payment[3], payment[4], payment[5])

                selected_card = game_controller.card_slt_from_client(card_level, slot_num)

                buy_card_check = game_controller.gameobserver.correct_payment(selected_card, player, payment)

                bank = game_controller.bank

                # 올바른 턴인지 검사
                if recv_converted["보낸이"] != game_controller.player_list[game_controller.turn_of_game % game_controller.player_num].name:
                    dic = {"지시": "대기"}
                    self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)
                else:
                    # 올바른 턴일 경우
                    # 구매조건 충족시
                    if len(player.reserved_cards) < slot_num + 1:
                        dic = {"지시": "재입력", "내용": "없는 카드를 선택하셨습니다"}
                        self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)
                    else:
                        if buy_card_check == True:
                            # 구매 로직처리
                            game_controller.buy_reservation_card_confirm(selected_card, payment, player)

                            # 천상계 강림 확인
                            if game_controller.gameobserver.descent_of_celestiality(player, bank) is not False:
                                possible_cards_list = game_controller.gameobserver.descent_of_celestiality(player, bank)
                                dic = {"가능카드": possible_cards_list}
                                dic["지시"] = "천상계 강림"
                                self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)

                            else:
                                # 천상계가 강림하지 않은 경우
                                game_over_condition = game_controller.game_over_condition
                                player_list = game_controller.player_list
                                game_controller.after_turn()
                                turn = game_controller.turn_of_game

                                # 1) 게임이 바로 종료됨
                                if game_controller.gameobserver.game_over_check(game_over_condition, turn,
                                                                                player_list) == "end":
                                    dic = {"지시": "바로 종료"}

                                    result = self.view_list_extractor()
                                    dic["자원 뷰"] = result[0]
                                    dic["예약카드 뷰"] = result[1]
                                    dic["바닥카드 뷰"] = result[2]
                                    dic["천상계 뷰"] = result[3]
                                    dic["포인트 뷰"] = result[4]

                                    title_text = "게임 종료조건이 충족되었습니다"
                                    points, card_num = game_controller.gameobserver.points_card_num_extractor(
                                        player_list)
                                    dic["유저목록"] = self.userman.userlist_for_send
                                    dic["포인트"] = points
                                    dic["카드개수"] = card_num
                                    self.userman.sendMessageToAll(dic)
                                # 2) 이번 턴에 종료
                                elif game_controller.gameobserver.game_over_check(game_over_condition, turn,
                                                                                  player_list) == "end soon":
                                    dic = {"지시": "이번 턴에 종료"}

                                    result = self.view_list_extractor()
                                    dic["자원 뷰"] = result[0]
                                    dic["예약카드 뷰"] = result[1]
                                    dic["바닥카드 뷰"] = result[2]
                                    dic["천상계 뷰"] = result[3]
                                    dic["포인트 뷰"] = result[4]

                                    warning_text = recv_converted["보낸이"] + "님이 " + \
                                                   "15점을 달성하여 이번 회에 게임이 종료됩니다. 승리를 넘겨주지 않으려면 서둘러야 합니다" \
                                                   + "이번 턴은 " + game_controller.gameobserver.next_player(player_list,
                                                                                                         player) \
                                                   + "의 차례입니다"
                                    dic["메세지"] = warning_text
                                    game_controller.game_over_condition = 1
                                    self.userman.sendMessageToAll(dic)
                                # 3) 턴 넘김
                                elif game_controller.gameobserver.game_over_check(game_over_condition, turn,
                                                                                  player_list) == "go on":
                                    dic = {"지시": "턴 넘김", "순서": player_list[turn % game_controller.player_num].name}
                                    result = self.view_list_extractor()
                                    dic["자원 뷰"] = result[0]
                                    dic["예약카드 뷰"] = result[1]
                                    dic["바닥카드 뷰"] = result[2]
                                    dic["천상계 뷰"] = result[3]
                                    dic["포인트 뷰"] = result[4]

                                    print("턴 : ", turn % game_controller.player_num)
                                    self.userman.sendMessageToAll(dic)

                        # 잘못된 구매선택을 했을 경우
                        else:
                            dic = {"지시": "재입력", "내용": buy_card_check}
                            self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)

            elif recv_converted["요청"] == "카드예약":
                slot_num = recv_converted["슬롯번호"]
                card_level = recv_converted["카드레벨"]
                player = game_controller.who_is_it(recv_converted["보낸이"])

                selected_card = game_controller.card_slt_from_client(card_level, slot_num)

                reservation_check = game_controller.gameobserver.correct_reservation(player)

                bank = game_controller.bank

                if recv_converted["보낸이"] != game_controller.player_list[game_controller.turn_of_game % game_controller.player_num].name:
                    dic = {"지시": "대기"}
                    self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)
                else:
                    # 맞는 턴일 경우 로직
                    if reservation_check == True:
                        game_controller.reservation_confirm(player, selected_card)

                        if game_controller.gameobserver.descent_of_celestiality(player, bank) is not False:

                            possible_cards_list = game_controller.gameobserver.descent_of_celestiality(player, bank)
                            dic = {"가능카드": possible_cards_list}
                            dic["지시"] = "천상계 강림"
                            self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)

                        else:
                            # 천상계가 강림하지 않은 경우
                            game_over_condition = game_controller.game_over_condition
                            player_list = game_controller.player_list
                            game_controller.after_turn()
                            turn = game_controller.turn_of_game

                            # 1) 게임이 바로 종료됨
                            if game_controller.gameobserver.game_over_check(game_over_condition, turn,
                                                                            player_list) == "end":
                                dic = {"지시": "바로 종료"}

                                result = self.view_list_extractor()
                                dic["자원 뷰"] = result[0]
                                dic["예약카드 뷰"] = result[1]
                                dic["바닥카드 뷰"] = result[2]
                                dic["천상계 뷰"] = result[3]
                                dic["포인트 뷰"] = result[4]

                                title_text = "게임 종료조건이 충족되었습니다"
                                points, card_num = game_controller.gameobserver.points_card_num_extractor(
                                    player_list)
                                dic["유저목록"] = self.userman.userlist_for_send
                                dic["포인트"] = points
                                dic["카드개수"] = card_num
                                self.userman.sendMessageToAll(dic)

                            # 2) 이번 턴에 종료
                            elif game_controller.gameobserver.game_over_check(game_over_condition, turn,
                                                                              player_list) == "end soon":
                                dic = {"지시": "이번 턴에 종료"}

                                result = self.view_list_extractor()
                                dic["자원 뷰"] = result[0]
                                dic["예약카드 뷰"] = result[1]
                                dic["바닥카드 뷰"] = result[2]
                                dic["천상계 뷰"] = result[3]
                                dic["포인트 뷰"] = result[4]

                                warning_text = recv_converted["보낸이"] + "님이 " + \
                                               "15점을 달성하여 이번 회에 게임이 종료됩니다. 승리를 넘겨주지 않으려면 서둘러야 합니다" \
                                               + "이번 턴은 " + game_controller.gameobserver.next_player(player_list,
                                                                                                     player) \
                                               + "의 차례입니다"
                                dic["메세지"] = warning_text
                                game_controller.game_over_condition = 1
                                self.userman.sendMessageToAll(dic)

                            # 3) 턴 넘김
                            elif game_controller.gameobserver.game_over_check(game_over_condition, turn, player_list) == "go on":
                                dic = {"지시": "턴 넘김", "순서": player_list[turn % game_controller.player_num].name}
                                result = self.view_list_extractor()
                                dic["자원 뷰"] = result[0]
                                dic["예약카드 뷰"] = result[1]
                                dic["바닥카드 뷰"] = result[2]
                                dic["천상계 뷰"] = result[3]
                                dic["포인트 뷰"] = result[4]

                                print("턴 : ", turn % game_controller.player_num)
                                self.userman.sendMessageToAll(dic)
                    else:
                        dic = {"지시": "재입력", "내용": "3장 이상 예약할 수 없습니다"}
                        self.userman.sendMessageToSomeone(recv_converted["보낸이"], dic)

            # 천상계 선택 리스폰스에 대한 처리
            elif recv_converted["요청"] == "천상계 선택":
                id = recv_converted["선택카드"]
                player = game_controller.who_is_it(recv_converted["보낸이"])

                #선택카드에 대한 내부로직처리
                game_controller.celestiality_event(id, player)

                game_over_condition = game_controller.game_over_condition
                game_controller.after_turn()
                turn = game_controller.turn_of_game
                player_list = game_controller.player_list

                # 천상계 처리 후 결과가 즉시종료인 경우
                if game_controller.gameobserver.game_over_check(game_over_condition, turn, player_list) == "end":
                    dic = {"지시": "즉시 종료"}

                    result = self.view_list_extractor()
                    dic["자원 뷰"] = result[0]
                    dic["예약카드 뷰"] = result[1]
                    dic["바닥카드 뷰"] = result[2]
                    dic["천상계 뷰"] = result[3]
                    dic["포인트 뷰"] = result[4]

                    points, card_num = game_controller.gameobserver.points_card_num_extractor(
                        player_list)

                    print("포인츠, 카드넘", points, card_num, type(points), type(card_num))

                    dic["유저목록"] = self.userman.userlist_for_send
                    dic["포인트"] = points
                    dic["카드개수"] = card_num

                    self.userman.sendMessageToAll(dic)

                # 천상계가 강림하여 15점이 처음으로 넘어가고 이번 턴에 게임이 종료될 경우
                elif game_controller.gameobserver.game_over_check(game_over_condition, turn, player_list) == "end soon":
                    dic = {"지시": "이번 턴에 종료"}

                    result = self.view_list_extractor()
                    dic["자원 뷰"] = result[0]
                    dic["예약카드 뷰"] = result[1]
                    dic["바닥카드 뷰"] = result[2]
                    dic["천상계 뷰"] = result[3]
                    dic["포인트 뷰"] = result[4]

                    warning_text = "천상계 강림으로 " + recv_converted["보낸이"] + "님이 " + \
                                   "15점을 달성하여 이번 회에 게임이 종료됩니다. 승리를 넘겨주지 않으려면 서둘러야 합니다" \
                                   + "이번 턴은 " + game_controller.gameobserver.next_player(player_list, player) \
                                   + "의 차례입니다"
                    dic["메세지"] = warning_text
                    game_controller.game_over_condition = 1
                    self.userman.sendMessageToAll(dic)

                # 천상계가 강림하였으나 이미 15점을 넘긴 유저가 있거나 15점이 아무도 되지 않아 턴이 넘어가는경우
                elif game_controller.gameobserver.game_over_check(game_over_condition, turn, player_list) == "go on":
                    dic = {"지시": "턴 넘김"}

                    result = self.view_list_extractor()
                    dic["자원 뷰"] = result[0]
                    dic["예약카드 뷰"] = result[1]
                    dic["바닥카드 뷰"] = result[2]
                    dic["천상계 뷰"] = result[3]
                    dic["포인트 뷰"] = result[4]

                    self.userman.sendMessageToAll(dic)

    def registerUsername(self, player_name):
        if self.userman.addUser(player_name, self.request, self.client_address):
            return 1

    def view_list_extractor(self):
        # 천상계 뷰 전달 [[플레이어 천상계 인트 카드번호 리스트], ... 마지막 [뱅크 천상계 인트 카드번호 리스트]]
        list_of_celestiality_list = []
        for i in range(len(game_controller.player_list)):
            each_players_card = []
            for j in game_controller.player_list[i].celestial_cards:
                each_players_card.append(j.identification)
            list_of_celestiality_list.append(each_players_card)
        bank_card = []
        for i in game_controller.bank.celestial_card_revealed:
            bank_card.append(i.identification)
        list_of_celestiality_list.append(bank_card)


        # 예약카드 뷰 정보 전달 [플레이어별 예약카드번호 인트 리스트 [], [], ...]
        list_of_reservation_list = []
        for i in range(len(game_controller.player_list)):
            each_players_card = []
            for j in game_controller.player_list[i].reserved_cards:
                each_players_card.append(j.identification)
            list_of_reservation_list.append(each_players_card)

        # 바닥카드 뷰 정보 전달
        # [플레이어 바닥카드 총괄 리스트 [플레이어별 할인카드 인트 리스트 [], [], ...],
        # 은행 바닥카드 총괄 리스트 [레벨별 카드번호 리스트 [lv1], [lv2], [lv3]]]
        all_normal_card_list = []
        list_of_bank_card_list = []
        lv1_card_list = []
        lv2_card_list = []
        lv3_card_list = []
        for card in game_controller.bank.lv1_card_revealed:
            if card is not None:
                lv1_card_list.append(card.identification)
            else:
                lv1_card_list.append(None)
        for card in game_controller.bank.lv2_card_revealed:
            if card is not None:
                lv2_card_list.append(card.identification)
            else:
                lv2_card_list.append(None)
        for card in game_controller.bank.lv3_card_revealed:
            if card is not None:
                lv3_card_list.append(card.identification)
            else:
                lv3_card_list.append(None)
        list_of_bank_card_list.append(lv1_card_list)
        list_of_bank_card_list.append(lv2_card_list)
        list_of_bank_card_list.append(lv3_card_list)

        list_of_player_card_list = []
        for i in range(len(game_controller.player_list)):
            each_players_card = []
            each_players_card.append(len(game_controller.player_list[i].dia_discount_cards))
            each_players_card.append(len(game_controller.player_list[i].eme_discount_cards))
            each_players_card.append(len(game_controller.player_list[i].cho_discount_cards))
            each_players_card.append(len(game_controller.player_list[i].rby_discount_cards))
            each_players_card.append(len(game_controller.player_list[i].spr_discount_cards))
            list_of_player_card_list.append(each_players_card)
        all_normal_card_list.append(list_of_player_card_list)
        all_normal_card_list.append(list_of_bank_card_list)

        # 자원 뷰 전달 [[플레이어 자원 인트 리스트],, ... 마지막 [뱅크 자원 인트 리스트]]
        list_of_resources_list = []
        for i in range(len(game_controller.player_list)):
            list_of_resources_list.append(game_controller.player_list[i].possessed_resources.list_extract())
        list_of_resources_list.append(game_controller.bank.possessed_resources.list_extract())

        # 플레이어 점수 뷰 전달
        players_points_list = []
        for i in range(len(game_controller.player_list)):
            points = game_controller.gameobserver.points(game_controller.player_list[i])
            players_points_list.append(points)

        return list_of_resources_list, list_of_reservation_list, all_normal_card_list, list_of_celestiality_list, players_points_list


class ChatingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def runServer(HOST, PORT):
    print('+++ 스플랜더 서버가 시작되었습니다.')
    try:
        server = ChatingServer((HOST, PORT), MyTcpHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print('--- 스플랜더 서버를 종료합니다.')
        server.shutdown()
        server.server_close()


class Resources:
    dia_discount = 1
    eme_discount = 2
    cho_discount = 3
    rby_discount = 4
    spr_discount = 5

    def __init__(self, dia=0, eme=0, cho=0, rby=0, spr=0, gld=0):
        self.dia = dia
        self.eme = eme
        self.cho = cho
        self.rby = rby
        self.spr = spr
        self.gld = gld

    def sum_cal(self):
        sum_rsc = self.dia + self.eme + self.cho + self.rby + self.spr + self.gld
        return sum_rsc

    def minus_to_zero(self):
        for name, value in self.__dict__.items():
            if value < 0:
                setattr(self, name, 0)

    def contains_minus(self):
        for value in [self.dia, self.eme, self.cho, self.rby, self.spr]:
            if value < 0:
                return True

    def contains_plus(self):
        for value in [self.dia, self.eme, self.cho, self.rby, self.spr]:
            if value > 0:
                return True

    def list_extract(self):
        return [self.dia, self.eme, self.cho, self.rby, self.spr, self.gld]

    def __add__(self, other):
        return Resources(self.dia + other.dia, self.eme + other.eme, self.cho + other.cho,
                           self.rby + other.rby, self.spr + other.spr, self.gld + other.gld)

    def __sub__(self, other):
        return Resources(self.dia - other.dia, self.eme - other.eme, self.cho - other.cho,
                           self.rby - other.rby, self.spr - other.spr, self.gld - other.gld)

    def __eq__(self, other):
        return self.dia == other.dia and self.eme == other.eme and self.cho == other.cho and \
               self.rby == other.rby and self.spr == other.spr and self.gld == other.gld

    def __repr__(self):
        return str(self.dia) + str(self.eme) + str(self.cho) + str(self.rby) + str(self.spr) + str(self.gld)


class Bank:
    def __init__(self, num_of_players, CardList):
        self.celestial_card_hidden = CardList.celestial_card_shuffled
        self.lv1_card_hidden = CardList.lv1_card_shuffled
        self.lv2_card_hidden = CardList.lv2_card_shuffled
        self.lv3_card_hidden = CardList.lv3_card_shuffled

        self.celestial_card_revealed = []
        self.lv1_card_revealed = []
        self.lv2_card_revealed = []
        self.lv3_card_revealed = []

        self.all_hidden_cards = []
        self.all_hidden_cards.append(self.celestial_card_hidden)
        self.all_hidden_cards.append(self.lv1_card_hidden)
        self.all_hidden_cards.append(self.lv2_card_hidden)
        self.all_hidden_cards.append(self.lv3_card_hidden)

        # self.possessed_resources = Resources(1, 1, 1, 1, 1, 1)
        self.possessed_resources = None

        if num_of_players == 2:
            self.possessed_resources = Resources(4, 4, 4, 4, 4, 5)
        elif num_of_players == 3:
            self.possessed_resources = Resources(5, 5, 5, 5, 5, 5)
        elif num_of_players == 4:
            self.possessed_resources = Resources(7, 7, 7, 7, 7, 5)

        for i in range(num_of_players + 1):
            self.celestial_card_revealed.append(self.celestial_card_hidden.pop())
        for i in range(4):
            self.lv1_card_revealed.append(self.lv1_card_hidden.pop())
            self.lv2_card_revealed.append(self.lv2_card_hidden.pop())
            self.lv3_card_revealed.append(self.lv3_card_hidden.pop())

        self.all_revealed_cards = []
        self.all_revealed_cards.append(self.celestial_card_revealed)
        self.all_revealed_cards.append(self.lv1_card_revealed)
        self.all_revealed_cards.append(self.lv2_card_revealed)
        self.all_revealed_cards.append(self.lv3_card_revealed)


    def dispense_card(self, selected_card):
        if selected_card.level == 0:
            self.celestial_card_revealed.remove(selected_card)
        elif selected_card.level == 1:
            index = self.lv1_card_revealed.index(selected_card)
            if len(self.lv1_card_hidden) == 0:
                self.lv1_card_revealed[index] = None
            else:
                self.lv1_card_revealed[index] = self.lv1_card_hidden.pop()
        elif selected_card.level == 2:
            index = self.lv2_card_revealed.index(selected_card)
            if len(self.lv2_card_hidden) == 0:
                self.lv2_card_revealed[index] = None
            else:
                self.lv2_card_revealed[index] = self.lv2_card_hidden.pop()
        elif selected_card.level == 3:
            index = self.lv3_card_revealed.index(selected_card)
            if len(self.lv3_card_hidden) == 0:
                self.lv3_card_revealed[index] = None
            else:
                self.lv3_card_revealed[index] = self.lv3_card_hidden.pop()

    def dispense_resources(self, selected_Resources):
        self.possessed_resources -= selected_Resources

    def stack_resources(self, Resources_inflow):
        self.possessed_resources += Resources_inflow

    def stack_revealed_cards(self, selected_cards):
        if selected_cards.level == 0:
            self.celestial_card_revealed.append(selected_cards)
        elif selected_cards.level == 1:
            self.lv1_card_revealed.append(selected_cards)
        elif selected_cards.level == 2:
            self.lv2_card_revealed.append(selected_cards)
        elif selected_cards.level == 3:
            self.lv3_card_revealed.append(selected_cards)

    def stack_hidden_cards(self, selected_cards):
        if selected_cards.level == 1:
            self.lv1_card_hidden.append(selected_cards)
        elif selected_cards.level == 2:
            self.lv2_card_hidden.append(selected_cards)
        elif selected_cards.level == 3:
            self.lv3_card_hidden.append(selected_cards)

    def id_list_extract(self, original_list):
        id_list = []
        for i, card in enumerate(original_list):
            id_list.append(card.identification)
        return id_list


class Card:
    lv1 = 1
    lv2 = 2
    lv3 = 3

    def __init__(self, point, level, discount, Resources):
        self.point = point
        self.level = level
        self.discount = discount
        self.price = Resources
        self.identification = str(1) + str(self.price.dia) + str(self.price.eme) + str(self.price.cho) + str(
            self.price.rby) + str(self.price.spr)


#file I/O로 하는게 좋음. 유연한 구조. 기획자들과의 협업도 염두
class CardList:
    def __init__(self):
        self.celestial_card = []
        self.lv1_card = []
        self.lv2_card = []
        self.lv3_card = []

        self.all_card = []
        self.all_card.append(self.celestial_card)
        self.all_card.append(self.lv1_card)
        self.all_card.append(self.lv2_card)
        self.all_card.append(self.lv3_card)

        self.card_namelist = {}

        self.card_namelist[(104040)] = Card(3, 0, 0, Resources(0, 4, 0, 4, 0))
        self.card_namelist[(100440)] = Card(3, 0, 0, Resources(0, 0, 4, 4, 0))
        self.card_namelist[(104004)] = Card(3, 0, 0, Resources(0, 4, 0, 0, 4))
        self.card_namelist[(140400)] = Card(3, 0, 0, Resources(4, 0, 4, 0, 0))
        self.card_namelist[(140004)] = Card(3, 0, 0, Resources(4, 0, 0, 0, 4))
        self.card_namelist[(130330)] = Card(3, 0, 0, Resources(3, 0, 3, 3, 0))
        self.card_namelist[(133003)] = Card(3, 0, 0, Resources(3, 3, 0, 0, 3))
        self.card_namelist[(103330)] = Card(3, 0, 0, Resources(0, 3, 3, 3, 0))
        self.card_namelist[(103033)] = Card(3, 0, 0, Resources(0, 3, 0, 3, 3))
        self.card_namelist[(130303)] = Card(3, 0, 0, Resources(3, 0, 3, 0, 3))

        self.card_namelist[(100003)] = Card(0, Card.lv1, Resources.dia_discount, Resources(0, 0, 0, 0, 3))
        self.card_namelist[(100120)] = Card(0, Card.lv1, Resources.dia_discount, Resources(0, 0, 1, 2, 0))
        self.card_namelist[(100202)] = Card(0, Card.lv1, Resources.dia_discount, Resources(0, 0, 2, 0, 2))
        self.card_namelist[(102102)] = Card(0, Card.lv1, Resources.dia_discount, Resources(0, 2, 1, 0, 2))
        self.card_namelist[(130101)] = Card(0, Card.lv1, Resources.dia_discount, Resources(3, 0, 1, 0, 1))
        self.card_namelist[(101111)] = Card(0, Card.lv1, Resources.dia_discount, Resources(0, 1, 1, 1, 1))
        self.card_namelist[(102111)] = Card(0, Card.lv1, Resources.dia_discount, Resources(0, 2, 1, 1, 1))
        self.card_namelist[(104000)] = Card(1, Card.lv1, Resources.dia_discount, Resources(0, 4, 0, 0, 0))

        self.card_namelist[(120033)] = Card(1, Card.lv2, Resources.dia_discount, Resources(2, 0, 0, 3, 3))
        self.card_namelist[(103220)] = Card(1, Card.lv2, Resources.dia_discount, Resources(0, 3, 2, 2, 0))
        self.card_namelist[(100050)] = Card(2, Card.lv2, Resources.dia_discount, Resources(0, 0, 0, 5, 0))
        self.card_namelist[(100350)] = Card(2, Card.lv2, Resources.dia_discount, Resources(0, 0, 3, 5, 0))
        self.card_namelist[(101240)] = Card(2, Card.lv2, Resources.dia_discount, Resources(0, 1, 2, 4, 0))
        self.card_namelist[(160000)] = Card(3, Card.lv2, Resources.dia_discount, Resources(6, 0, 0, 0, 0))

        self.card_namelist[(103353)] = Card(3, Card.lv3, Resources.dia_discount, Resources(0, 3, 3, 5, 3))
        self.card_namelist[(100700)] = Card(4, Card.lv3, Resources.dia_discount, Resources(0, 0, 7, 0, 0))
        self.card_namelist[(130630)] = Card(4, Card.lv3, Resources.dia_discount, Resources(3, 0, 6, 3, 0))
        self.card_namelist[(130700)] = Card(5, Card.lv3, Resources.dia_discount, Resources(3, 0, 7, 0, 0))

        self.card_namelist[(100030)] = Card(0, Card.lv1, Resources.eme_discount, Resources(0, 0, 0, 3, 0))
        self.card_namelist[(120001)] = Card(0, Card.lv1, Resources.eme_discount, Resources(2, 0, 0, 0, 1))
        self.card_namelist[(100022)] = Card(0, Card.lv1, Resources.eme_discount, Resources(0, 0, 0, 2, 2))
        self.card_namelist[(100221)] = Card(0, Card.lv1, Resources.eme_discount, Resources(0, 0, 2, 2, 1))
        self.card_namelist[(111003)] = Card(0, Card.lv1, Resources.eme_discount, Resources(1, 1, 0, 0, 3))
        self.card_namelist[(110111)] = Card(0, Card.lv1, Resources.eme_discount, Resources(1, 0, 1, 1, 1))
        self.card_namelist[(110211)] = Card(0, Card.lv1, Resources.eme_discount, Resources(1, 0, 2, 1, 1))
        self.card_namelist[(100400)] = Card(1, Card.lv1, Resources.eme_discount, Resources(0, 0, 4, 0, 0))

        self.card_namelist[(120203)] = Card(1, Card.lv2, Resources.eme_discount, Resources(2, 0, 2, 0, 3))
        self.card_namelist[(132030)] = Card(1, Card.lv2, Resources.eme_discount, Resources(3, 2, 0, 3, 0))
        self.card_namelist[(105000)] = Card(2, Card.lv2, Resources.eme_discount, Resources(0, 5, 0, 0, 0))
        self.card_namelist[(103005)] = Card(2, Card.lv2, Resources.eme_discount, Resources(0, 3, 0, 0, 5))
        self.card_namelist[(140102)] = Card(2, Card.lv2, Resources.eme_discount, Resources(4, 0, 1, 0, 2))
        self.card_namelist[(106000)] = Card(3, Card.lv2, Resources.eme_discount, Resources(0, 6, 0, 0, 0))

        self.card_namelist[(150333)] = Card(3, Card.lv3, Resources.eme_discount, Resources(5, 0, 3, 3, 3))
        self.card_namelist[(100007)] = Card(4, Card.lv3, Resources.eme_discount, Resources(0, 0, 0, 0, 7))
        self.card_namelist[(133006)] = Card(4, Card.lv3, Resources.eme_discount, Resources(3, 3, 0, 0, 6))
        self.card_namelist[(103007)] = Card(5, Card.lv3, Resources.eme_discount, Resources(0, 3, 0, 0, 7))

        self.card_namelist[(103000)] = Card(0, Card.lv1, Resources.cho_discount, Resources(0, 3, 0, 0, 0))
        self.card_namelist[(102010)] = Card(0, Card.lv1, Resources.cho_discount, Resources(0, 2, 0, 1, 0))
        self.card_namelist[(122000)] = Card(0, Card.lv1, Resources.cho_discount, Resources(2, 2, 0, 0, 0))
        self.card_namelist[(120012)] = Card(0, Card.lv1, Resources.cho_discount, Resources(2, 0, 0, 1, 2))
        self.card_namelist[(101130)] = Card(0, Card.lv1, Resources.cho_discount, Resources(0, 1, 1, 3, 0))
        self.card_namelist[(111011)] = Card(0, Card.lv1, Resources.cho_discount, Resources(1, 1, 0, 1, 1))
        self.card_namelist[(111012)] = Card(0, Card.lv1, Resources.cho_discount, Resources(1, 1, 0, 1, 2))
        self.card_namelist[(100004)] = Card(1, Card.lv1, Resources.cho_discount, Resources(0, 0, 0, 0, 4))

        self.card_namelist[(132002)] = Card(1, Card.lv2, Resources.cho_discount, Resources(3, 2, 0, 0, 2))
        self.card_namelist[(133200)] = Card(1, Card.lv2, Resources.cho_discount, Resources(3, 3, 2, 0, 0))
        self.card_namelist[(150000)] = Card(2, Card.lv2, Resources.cho_discount, Resources(5, 0, 0, 0, 0))
        self.card_namelist[(105030)] = Card(2, Card.lv2, Resources.cho_discount, Resources(0, 5, 0, 3, 0))
        self.card_namelist[(104021)] = Card(2, Card.lv2, Resources.cho_discount, Resources(0, 4, 0, 2, 1))
        self.card_namelist[(100600)] = Card(3, Card.lv2, Resources.cho_discount, Resources(0, 0, 6, 0, 0))

        self.card_namelist[(135033)] = Card(3, Card.lv3, Resources.cho_discount, Resources(3, 5, 0, 3, 3))
        self.card_namelist[(100070)] = Card(4, Card.lv3, Resources.cho_discount, Resources(0, 0, 0, 7, 0))
        self.card_namelist[(103360)] = Card(4, Card.lv3, Resources.cho_discount, Resources(0, 3, 3, 6, 0))
        self.card_namelist[(100370)] = Card(5, Card.lv3, Resources.cho_discount, Resources(0, 0, 3, 7, 0))

        self.card_namelist[(130000)] = Card(0, Card.lv1, Resources.rby_discount, Resources(3, 0, 0, 0, 0))
        self.card_namelist[(101002)] = Card(0, Card.lv1, Resources.rby_discount, Resources(0, 1, 0, 0, 2))
        self.card_namelist[(120020)] = Card(0, Card.lv1, Resources.rby_discount, Resources(2, 0, 0, 2, 0))
        self.card_namelist[(121200)] = Card(0, Card.lv1, Resources.rby_discount, Resources(2, 1, 2, 0, 0))
        self.card_namelist[(110310)] = Card(0, Card.lv1, Resources.rby_discount, Resources(1, 0, 3, 1, 0))
        self.card_namelist[(111101)] = Card(0, Card.lv1, Resources.rby_discount, Resources(1, 1, 1, 0, 1))
        self.card_namelist[(121101)] = Card(0, Card.lv1, Resources.rby_discount, Resources(2, 1, 1, 0, 1))
        self.card_namelist[(140000)] = Card(1, Card.lv1, Resources.rby_discount, Resources(4, 0, 0, 0, 0))

        self.card_namelist[(120320)] = Card(1, Card.lv2, Resources.rby_discount, Resources(2, 0, 3, 2, 0))
        self.card_namelist[(100323)] = Card(1, Card.lv2, Resources.rby_discount, Resources(0, 0, 3, 2, 3))
        self.card_namelist[(100500)] = Card(2, Card.lv2, Resources.rby_discount, Resources(0, 0, 5, 0, 0))
        self.card_namelist[(130500)] = Card(2, Card.lv2, Resources.rby_discount, Resources(3, 0, 5, 0, 0))
        self.card_namelist[(112004)] = Card(2, Card.lv2, Resources.rby_discount, Resources(1, 2, 0, 0, 4))
        self.card_namelist[(100060)] = Card(3, Card.lv2, Resources.rby_discount, Resources(0, 0, 0, 6, 0))

        self.card_namelist[(133305)] = Card(3, Card.lv3, Resources.rby_discount, Resources(3, 3, 3, 0, 5))
        self.card_namelist[(107000)] = Card(4, Card.lv3, Resources.rby_discount, Resources(0, 7, 0, 0, 0))
        self.card_namelist[(106033)] = Card(4, Card.lv3, Resources.rby_discount, Resources(0, 6, 0, 3, 3))
        self.card_namelist[(107030)] = Card(5, Card.lv3, Resources.rby_discount, Resources(0, 7, 0, 3, 0))

        self.card_namelist[(100300)] = Card(0, Card.lv1, Resources.spr_discount, Resources(0, 0, 3, 0, 0))
        self.card_namelist[(110200)] = Card(0, Card.lv1, Resources.spr_discount, Resources(1, 0, 2, 0, 0))
        self.card_namelist[(102200)] = Card(0, Card.lv1, Resources.spr_discount, Resources(0, 2, 2, 0, 0))
        self.card_namelist[(112020)] = Card(0, Card.lv1, Resources.spr_discount, Resources(1, 2, 0, 2, 0))
        self.card_namelist[(103011)] = Card(0, Card.lv1, Resources.spr_discount, Resources(0, 3, 0, 1, 1))
        self.card_namelist[(111110)] = Card(0, Card.lv1, Resources.spr_discount, Resources(1, 1, 1, 1, 0))
        self.card_namelist[(111120)] = Card(0, Card.lv1, Resources.spr_discount, Resources(1, 1, 1, 2, 0))
        self.card_namelist[(100040)] = Card(1, Card.lv1, Resources.spr_discount, Resources(0, 0, 0, 4, 0))

        self.card_namelist[(102032)] = Card(1, Card.lv2, Resources.spr_discount, Resources(0, 2, 0, 3, 2))
        self.card_namelist[(103302)] = Card(1, Card.lv2, Resources.spr_discount, Resources(0, 3, 3, 0, 2))
        self.card_namelist[(100005)] = Card(2, Card.lv2, Resources.spr_discount, Resources(0, 0, 0, 0, 5))
        self.card_namelist[(150003)] = Card(2, Card.lv2, Resources.spr_discount, Resources(5, 0, 0, 0, 3))
        self.card_namelist[(120410)] = Card(2, Card.lv2, Resources.spr_discount, Resources(2, 0, 4, 1, 0))
        self.card_namelist[(100006)] = Card(3, Card.lv2, Resources.spr_discount, Resources(0, 0, 0, 0, 6))

        self.card_namelist[(133530)] = Card(4, Card.lv3, Resources.spr_discount, Resources(3, 3, 5, 3, 0))
        self.card_namelist[(170000)] = Card(4, Card.lv3, Resources.spr_discount, Resources(7, 0, 0, 0, 0))
        self.card_namelist[(160303)] = Card(4, Card.lv3, Resources.spr_discount, Resources(6, 0, 3, 0, 3))
        self.card_namelist[(170003)] = Card(5, Card.lv3, Resources.spr_discount, Resources(7, 0, 0, 0, 3))

        self.celestial_card.append(self.card_namelist[(104040)])
        self.celestial_card.append(self.card_namelist[(100440)])
        self.celestial_card.append(self.card_namelist[(104004)])
        self.celestial_card.append(self.card_namelist[(140400)])
        self.celestial_card.append(self.card_namelist[(140004)])
        self.celestial_card.append(self.card_namelist[(130330)])
        self.celestial_card.append(self.card_namelist[(133003)])
        self.celestial_card.append(self.card_namelist[(103330)])
        self.celestial_card.append(self.card_namelist[(103033)])
        self.celestial_card.append(self.card_namelist[(130303)])

        self.lv1_card.append(self.card_namelist[(100003)])
        self.lv1_card.append(self.card_namelist[(100120)])
        self.lv1_card.append(self.card_namelist[(100202)])
        self.lv1_card.append(self.card_namelist[(102102)])
        self.lv1_card.append(self.card_namelist[(130101)])
        self.lv1_card.append(self.card_namelist[(101111)])
        self.lv1_card.append(self.card_namelist[(102111)])
        self.lv1_card.append(self.card_namelist[(104000)])

        self.lv2_card.append(self.card_namelist[(120033)])
        self.lv2_card.append(self.card_namelist[(103220)])
        self.lv2_card.append(self.card_namelist[(100050)])
        self.lv2_card.append(self.card_namelist[(100350)])
        self.lv2_card.append(self.card_namelist[(101240)])
        self.lv2_card.append(self.card_namelist[(160000)])

        self.lv3_card.append(self.card_namelist[(103353)])
        self.lv3_card.append(self.card_namelist[(100700)])
        self.lv3_card.append(self.card_namelist[(130630)])
        self.lv3_card.append(self.card_namelist[(130700)])

        self.lv1_card.append(self.card_namelist[(100030)])
        self.lv1_card.append(self.card_namelist[(120001)])
        self.lv1_card.append(self.card_namelist[(100022)])
        self.lv1_card.append(self.card_namelist[(100221)])
        self.lv1_card.append(self.card_namelist[(111003)])
        self.lv1_card.append(self.card_namelist[(110111)])
        self.lv1_card.append(self.card_namelist[(110211)])
        self.lv1_card.append(self.card_namelist[(100400)])

        self.lv2_card.append(self.card_namelist[(120203)])
        self.lv2_card.append(self.card_namelist[(132030)])
        self.lv2_card.append(self.card_namelist[(105000)])
        self.lv2_card.append(self.card_namelist[(103005)])
        self.lv2_card.append(self.card_namelist[(140102)])
        self.lv2_card.append(self.card_namelist[(106000)])

        self.lv3_card.append(self.card_namelist[(150333)])
        self.lv3_card.append(self.card_namelist[(100007)])
        self.lv3_card.append(self.card_namelist[(133006)])
        self.lv3_card.append(self.card_namelist[(103007)])

        self.lv1_card.append(self.card_namelist[(103000)])
        self.lv1_card.append(self.card_namelist[(102010)])
        self.lv1_card.append(self.card_namelist[(122000)])
        self.lv1_card.append(self.card_namelist[(120012)])
        self.lv1_card.append(self.card_namelist[(101130)])
        self.lv1_card.append(self.card_namelist[(111011)])
        self.lv1_card.append(self.card_namelist[(111012)])
        self.lv1_card.append(self.card_namelist[(100004)])

        self.lv2_card.append(self.card_namelist[(132002)])
        self.lv2_card.append(self.card_namelist[(133200)])
        self.lv2_card.append(self.card_namelist[(150000)])
        self.lv2_card.append(self.card_namelist[(105030)])
        self.lv2_card.append(self.card_namelist[(104021)])
        self.lv2_card.append(self.card_namelist[(100600)])

        self.lv3_card.append(self.card_namelist[(135033)])
        self.lv3_card.append(self.card_namelist[(100070)])
        self.lv3_card.append(self.card_namelist[(103360)])
        self.lv3_card.append(self.card_namelist[(100370)])

        self.lv1_card.append(self.card_namelist[(130000)])
        self.lv1_card.append(self.card_namelist[(101002)])
        self.lv1_card.append(self.card_namelist[(120020)])
        self.lv1_card.append(self.card_namelist[(121200)])
        self.lv1_card.append(self.card_namelist[(110310)])
        self.lv1_card.append(self.card_namelist[(111101)])
        self.lv1_card.append(self.card_namelist[(121101)])
        self.lv1_card.append(self.card_namelist[(140000)])

        self.lv2_card.append(self.card_namelist[(120320)])
        self.lv2_card.append(self.card_namelist[(100323)])
        self.lv2_card.append(self.card_namelist[(100500)])
        self.lv2_card.append(self.card_namelist[(130500)])
        self.lv2_card.append(self.card_namelist[(112004)])
        self.lv2_card.append(self.card_namelist[(100060)])

        self.lv3_card.append(self.card_namelist[(133305)])
        self.lv3_card.append(self.card_namelist[(107000)])
        self.lv3_card.append(self.card_namelist[(106033)])
        self.lv3_card.append(self.card_namelist[(107030)])

        self.lv1_card.append(self.card_namelist[(100300)])
        self.lv1_card.append(self.card_namelist[(110200)])
        self.lv1_card.append(self.card_namelist[(102200)])
        self.lv1_card.append(self.card_namelist[(112020)])
        self.lv1_card.append(self.card_namelist[(103011)])
        self.lv1_card.append(self.card_namelist[(111110)])
        self.lv1_card.append(self.card_namelist[(111120)])
        self.lv1_card.append(self.card_namelist[(100040)])

        self.lv2_card.append(self.card_namelist[(102032)])
        self.lv2_card.append(self.card_namelist[(103302)])
        self.lv2_card.append(self.card_namelist[(100005)])
        self.lv2_card.append(self.card_namelist[(150003)])
        self.lv2_card.append(self.card_namelist[(120410)])
        self.lv2_card.append(self.card_namelist[(100006)])

        self.lv3_card.append(self.card_namelist[(133530)])
        self.lv3_card.append(self.card_namelist[(170000)])
        self.lv3_card.append(self.card_namelist[(160303)])
        self.lv3_card.append(self.card_namelist[(170003)])


        self.celestial_card_shuffled = random.sample(self.celestial_card, len(self.celestial_card))
        self.lv1_card_shuffled = random.sample(self.lv1_card, len(self.lv1_card))
        self.lv2_card_shuffled = random.sample(self.lv2_card, len(self.lv2_card))
        self.lv3_card_shuffled = random.sample(self.lv3_card, len(self.lv3_card))


class Player:
    def __init__(self, name):
        self.name = name

        # self.possessed_resources = Resources(0, 0, 0, 0, 0, 0)
        self.possessed_resources = Resources(99, 99, 99, 99, 99, 99)

        self.celestial_cards = []

        self.dia_discount_cards = []
        self.eme_discount_cards = []
        self.cho_discount_cards = []
        self.rby_discount_cards = []
        self.spr_discount_cards = []

        self.all_possessed_cards = []
        self.all_possessed_cards.append(self.celestial_cards)
        self.all_possessed_cards.append(self.dia_discount_cards)
        self.all_possessed_cards.append(self.eme_discount_cards)
        self.all_possessed_cards.append(self.cho_discount_cards)
        self.all_possessed_cards.append(self.rby_discount_cards)
        self.all_possessed_cards.append(self.spr_discount_cards)

        self.reserved_cards = []

    def pay_for_card(self, selected_Resources):
        self.possessed_resources -= selected_Resources

    def receive_resources(self, selected_Resources):
        self.possessed_resources += selected_Resources

    def receive_card(self, selected_Card):
        if selected_Card.discount == 0:
            self.celestial_cards.append(selected_Card)
        elif selected_Card.discount == 1:
            self.dia_discount_cards.append(selected_Card)
        elif selected_Card.discount == 2:
            self.eme_discount_cards.append(selected_Card)
        elif selected_Card.discount == 3:
            self.cho_discount_cards.append(selected_Card)
        elif selected_Card.discount == 4:
            self.rby_discount_cards.append(selected_Card)
        elif selected_Card.discount == 5:
            self.spr_discount_cards.append(selected_Card)

    def make_reservation(self, selected_Card):
        self.reserved_cards.append(selected_Card)
        # index = self.reserved_cards.index(None)
        # self.reserved_cards[index] = selected_Card

    def dispense_reservation(self, selected_Card):
        self.reserved_cards.remove(selected_Card)
        # for i in range(3):
        #     if i+1 > len(self.reserved_cards):
        #         self.reserved_cards[i] = None


class GameController:
    def __init__(self):
        pass

    def start(self, user_list):
        self.player_num = len(user_list)
        print("유저리스트", user_list)
        print("유저수", self.player_num)
        self.player_list = {}
        self.name_list = []
        for i in user_list:
            self.name_list.append(user_list[i])

        self.card_list = CardList()
        self.bank = Bank(self.player_num, self.card_list)
        for index, name in enumerate(self.name_list):
            self.player_list[index] = Player(name)
        self.gameobserver = GameObserver()

        self.turn_of_game = 0
        self.game_over_condition = 0

    def message_for_client_list(self):

        pass

    #플레이어 추출기
    def who_is_it(self, name):
        for i, val in enumerate(self.player_list.values()):
            if val.name == name:
                player = self.player_list[i]
        return player

    #클라이언트 선택 추출기
    def rsc_slt_from_client(self, data_from_client):
        return Resources(data_from_client[0], data_from_client[1], data_from_client[2],
                         data_from_client[3], data_from_client[4], data_from_client[5])

    def card_slt_from_client(self, card_level, slot_num):
        print("카드레벨, 슬롯넘버", card_level, slot_num)
        turn = self.turn_of_game % self.player_num

        if card_level == 1:
            selected_card = self.bank.lv1_card_revealed[slot_num]
        elif card_level == 2:
            selected_card = self.bank.lv2_card_revealed[slot_num]
        elif card_level == 3:
            selected_card = self.bank.lv3_card_revealed[slot_num]
        elif card_level == 0:
            selected_card = self.player_list[(turn)].reserved_cards[slot_num]
        else:
            return False
        return selected_card

    #클라이언트 확정에 따른 후속조치 실행. view 적용은 after turn에서 데이터 전달
    def buy_card_confirm(self, selected_card, selected_payment, player):
        player.pay_for_card(selected_payment)
        self.bank.stack_resources(selected_payment)
        self.bank.dispense_card(selected_card)
        player.receive_card(selected_card)

    def reservation_confirm(self, player, selected_card):
        if self.bank.possessed_resources.gld == 0:
            player.make_reservation(selected_card)
            self.bank.dispense_card(selected_card)
        else:
            player.receive_resources(Resources(0, 0, 0, 0, 0, 1))
            self.bank.dispense_resources(Resources(0, 0, 0, 0, 0, 1))
            player.make_reservation(selected_card)
            self.bank.dispense_card(selected_card)

    def buy_reservation_card_confirm(self, selected_card, selected_payment, player):
        player.pay_for_card(selected_payment)
        self.bank.stack_resources(selected_payment)
        player.dispense_reservation(selected_card)
        player.receive_card(selected_card)

    def acquire_resources_confirm(self, selected_resources, player):
        self.bank.dispense_resources(selected_resources)
        player.receive_resources(selected_resources)

    def celestiality_event(self, selected_card_id, player):
        for celestial_card in self.bank.celestial_card_revealed:
            if selected_card_id == celestial_card.identification:
                selected_card = celestial_card
                break
        player.celestial_cards.append(selected_card)
        self.bank.celestial_card_revealed.remove(selected_card)

    def after_turn(self):
        self.turn_of_game += 1


class GameObserver:
    def __init__(self):
        pass

    def next_player(self, player_list, player):
        for i in player_list:
            if player_list[i].name == player.name:
                name_of_next_player = player_list[(i+1) % len(player_list)].name
        return name_of_next_player

    def correct_payment(self, selected_card, players, players_payment):
        discounted_price = selected_card.price - self.discount(players)
        difference_of_player_rsc_and_player_payment = players.possessed_resources - players_payment
        discounted_price.minus_to_zero()
        difference_of_price_and_paid = discounted_price - players_payment
        print("보유자원, 지불자원", players.possessed_resources, players_payment)
        print("할인상황, 카드가격", self.discount(players), selected_card.price)

        if difference_of_price_and_paid.contains_minus():
            text = '더 많은 자원을 낼 수 없습니다'
            return text
        elif difference_of_player_rsc_and_player_payment.contains_minus():
            text = "자원이 부족합니다"
            return text
        elif difference_of_price_and_paid.sum_cal() != 0:
            text = "요구되는 자원을 정확히 내야만 합니다"
            return text
        elif selected_card == False or selected_card == None:
            text = "이곳은 카드가 없습니다. 다른 카드를 선택하세요"
            return text
        else:
            return True

    def correct_selection(self, selected_resources, player, bank):
        for index, value in enumerate(list(selected_resources.__dict__.values())[0:5]):
            if (player.possessed_resources.sum_cal() + selected_resources.sum_cal()) > 10:
                text = "자원을 10개 이상 보유할 수 없습니다"
                return text
            elif selected_resources.gld > 0:
                text = "황금자원을 얻으시려면 카드를 선택하고 예약을 해야 합니다"
                return text
            elif int(value) > 2:
                text = "같은 자원을 2개 넘게 가져갈 수 없습니다"
                return text
            elif selected_resources.sum_cal() > 3:
                text = "자원은 3개까지만 가져갈 수 있습니다"
                return text
            elif int(value) == 2 and selected_resources.sum_cal() >= 3:
                text = "한 자원을 2개 고르면 더이상 가져갈 수 없습니다"
                return text
            elif int(value) == 2 and list(bank.possessed_resources.__dict__.values())[0:5][index] < 4:
                text = "4개 이상이 남아있는 자원만 2개 가져갈 수 있습니다"
                return text
            elif (bank.possessed_resources - selected_resources).contains_minus():
                text = "없는 자원을 선택하였습니다"
                return text
            else:
                continue
        return True

    def descent_of_celestiality(self, player, bank):
        possible_cards = []
        for cards in bank.celestial_card_revealed:
            difference = cards.price - self.discount(player)
            if difference.contains_plus():
                continue
            else:
                possible_cards.append(cards.identification)
        if len(possible_cards) == 0:
            return False
        else:
            return possible_cards

    def correct_reservation(self, player):
        if len(player.reserved_cards) >= 3:
            return False
        else:
            return True

    def discount(self, player):
        return Resources(len(player.dia_discount_cards)+4, len(player.eme_discount_cards)+4, len(player.cho_discount_cards)+4,
                         len(player.rby_discount_cards)+4, len(player.spr_discount_cards)+4)

    def points(self, player):
        points = 0
        for cards_dec in player.all_possessed_cards:
            for cards in cards_dec:
                points += cards.point
        return points + 12

    def game_over_check(self, game_over_condition, turn_of_game, player_list):
        player_num = len(player_list)
        # 첫번째 체크 : 이 유저가 처음으로 15점이 넘은 유저인가?
        if game_over_condition == 0 and self.points(
                player_list[((turn_of_game - 1) % player_num)]) >= 15:
            # 그렇다면 이 유저는 게임 순서상 마지막 유저인가? 그러면 그대로 게임이 종료된다
            if turn_of_game - 1 % player_num == (player_num - 1):
                return "end"
            # 이 유저가 마지막 유저가 아니라면 마지막 유저까지 플레이하고 게임이 종료된다는 것을 알려야 한다
            else:
                return "end soon"
        # 두번째 체크 : 이미 15점을 넘긴 유저가 있는 상태에서 마지막 유저까지 턴을 마쳤는가?
        elif (turn_of_game % player_num == 0) and game_over_condition == 1:
            return "end"
        # 그 외의 경우 : 그냥 턴을 넘김
        else:
            return "go on"

    def points_card_num_extractor(self, player_list):
        points = []
        for i in range(len(player_list)):
            points.append(self.points(player_list[i]))
        card_num = []
        for i in range(len(player_list)):
            card_num.append(self.discount(player_list[i]).sum_cal())
        return points, card_num


game_controller = GameController()

runServer(HOST, PORT)


