# -*- coding:utf-8 -*-
import sys
from PyQt4 import QtGui, QtCore
import random
import math
import time

# 定数
GRID_WIDTH = 50 # 1マスの幅
BOARD_X0 = 150 # 盤面の描画位置(X座標)
BOARD_Y0 = 20  # 盤面の描画位置(Y座標)
BLACK = 1
WHITE = -1
SPACE = 0
SENTINEL = 3
KOMI = 6.5

GRID = 9
BOARD_MAX = (GRID + 2) * (GRID + 2)

DIR4 = [1, -1, GRID + 2, -(GRID + 2)] # 右左下上
PASS = 0

# 打った結果
SUCCESS = 0
ILLIGAL = 1
KO = 2
EYE = 3

# UCB用定数
FPU = 5 # First Play Urgency
C = 0.31

PLAYOUT_MAX = 300

# 盤初期化
def create_board():
    board = [SPACE for i in range(BOARD_MAX)]
    for x in range(GRID+2):
        board[x] = SENTINEL
        board[x + (GRID+2)*(GRID+1)] = SENTINEL
    for y in range(1, GRID+2):
        board[(GRID+2) * y] = SENTINEL
        board[GRID+1 + (GRID+2) * y] = SENTINEL
    return board

# x, y座標をboardのインデックスに変換
def get_xy(x, y):
    return x + (GRID+2) * y

def get_x_y(xy):
    return xy % (GRID+2),  xy / (GRID+2)

# 盤面print(デバッグ用)
def print_board(board):
    for y in range(GRID):
        for x in range(GRID):
            xy = get_xy(x+1, y+1)
            print "{0:2},".format(board[xy]) ,
        print ""

class UTCNode:
    xy = -1
    playout_num = 0
    playout_num_sum = 0
    win_num = 0

    def __init__(self):
        self.child = []

def expand_node(node, board):
    for xy, c in enumerate(board):
        if c == SPACE:
            new_node = UTCNode()
            new_node.xy = xy
            node.child.append(new_node)
    # PASSを追加
    new_node = UTCNode()
    new_node.xy = PASS
    node.child.append(new_node)

# コウの位置
class Ko:
    xy = 0
    def copy(self):
        new_ko = Ko()
        new_ko.xy = self.xy
        return new_ko

class LibertiesAndChains:
    liberties = 0
    chains = 0

    def __init__(self):
        self.checked = [False for i in range(BOARD_MAX)] # チェック済みか

# 呼吸点の数と連結した石の数を取得(内部用再帰処理)
def count_liberties_and_chains_inner(board, xy, color, liberties_and_chains):
    # チェック済みする
    liberties_and_chains.checked[xy] = True

    # 石の数をカウントアップ
    liberties_and_chains.chains += 1

    # 4方向について
    for d in DIR4:
        xyd = xy + d
        # チェック済みの場合
        if liberties_and_chains.checked[xyd] == True:
            continue
        # 空きの場合
        if board[xyd] == SPACE:
            liberties_and_chains.checked[xyd] = True
            liberties_and_chains.liberties += 1
        # 同じ色の場合
        elif board[xyd] == color:
            # 再帰呼び出し
            count_liberties_and_chains_inner(board, xyd, color, liberties_and_chains)

# 呼吸点の数と連結した石の数を取得
def count_liberties_and_chains(board, xy, color):
    liberties_and_chains = LibertiesAndChains()
    # 内部用再帰処理
    count_liberties_and_chains_inner(board, xy, color, liberties_and_chains)
    return liberties_and_chains.liberties, liberties_and_chains.chains

def capture(board, xy, color):
    board[xy] = SPACE
    for d in DIR4:
        if board[xy + d] == color:
            capture(board, xy + d, color)

# 石を打つ
def move(board, ko, xy, color):
    # パスの場合
    if xy == PASS:
        return SUCCESS

    spaces = 0 # 空きの数
    edges = 0 # 壁の数
    captures = 0 # 取れる石の数
    alive = 0 # 生き

    # 4方向の・・・
    around_liberties = [0, 0, 0, 0]
    around_chains = [0, 0, 0, 0]

    for i, d in enumerate(DIR4):
        xyd = xy + d
        c = board[xyd]
        # 空きの場合
        if c == SPACE:
            spaces += 1
            continue
        # 壁の場合
        if c == SENTINEL:
            edges += 1
            continue
        # 呼吸点の数と連結した石の数を取得
        liberties, chains = count_liberties_and_chains(board, xyd, c)

        around_liberties[i] = liberties
        around_chains[i] = chains

        # 取ることができる
        if c == -color and liberties == 1:
            captures += chains
            tmp_ko = xyd
        elif c == color and liberties >= 2:
            alive += 1

    # 自殺手
    if captures == 0 and spaces == 0 and alive == 0:
        return ILLIGAL
    # コウ
    if xy == ko.xy:
        return KO
    # 眼
    if edges + alive == 4:
        return EYE

    # 石を取る
    for i, d in enumerate(DIR4):
        xyd = xy + d
        if around_liberties[i] == 1 and board[xyd] == -color:
            # 取る
            capture(board, xyd, -color)
    
    # 石を打つ
    board[xy] = color

    # 呼吸点の数と連結した石の数を取得
    liberties, chains = count_liberties_and_chains(board, xy, color)

    if captures == 1 and chains == 1 and liberties == 1:
        ko.xy = tmp_ko
    else:
        ko.xy = 0

    return SUCCESS

# UCBからプレイアウトする手を選択
def select_node_with_ucb(node):
    max_ucb = -999
    for child in node.child:
        if child.playout_num == 0:
            # 未実行
            ucb = FPU + random.randrange(FPU)
        else:
            ucb = float(child.win_num) / child.playout_num + C * math.sqrt(math.log(node.playout_num_sum) / child.playout_num)
            
        if ucb > max_ucb:
            max_ucb = ucb
            selected_node = child

    return selected_node

# UCT
def search_uct(board, ko, color, node, root_color):
    # UCBからプレイアウトする手を選択
    while True:
        selected_node = select_node_with_ucb(node)
        err = move(board, ko, selected_node.xy, color)
        if err == SUCCESS:
            break
        else:
            # 除外
            node.child.remove(selected_node)

    # 閾値以下の場合プレイアウト
    if selected_node.playout_num_sum < 1:
        win = playout(board, ko, selected_node, -color, root_color)
    else:
        # ノードを展開
        if len(selected_node.child) == 0:
            expand_node(selected_node, board)
        win = search_uct(board, ko, -color, selected_node, root_color)

    # 勝率を更新
    selected_node.win_num += win
    selected_node.playout_num += 1
    node.playout_num_sum += 1

    return win

# 終局 勝敗を返す
def end_game(board, color):
    # 中国ルールで数える

    # 石の数
    stone_num = {BLACK : 0, WHITE : 0, SPACE : 0}
    score = 0

    for x in range(GRID):
        for y in range(GRID):
            xy = get_xy(x + 1, y + 1)
            c = board[xy]
            stone_num[c] += 1
            if c != SPACE:
                continue
            mk = {BLACK : 0, WHITE : 0, SPACE : 0, SENTINEL : 0} # 4方向の石の数
            for d in DIR4:
                mk[board[xy + d]] += 1
            if mk[BLACK] > 0 and mk[WHITE] == 0:
                score += 1
            if mk[WHITE] > 0 and mk[BLACK] == 0:
                score -= 1
    score = stone_num[BLACK] - stone_num[WHITE] - KOMI

    if color == BLACK:
        if score > 0:
            return 1
        else:
            return 0
    if color == WHITE:
        if score < 0:
            return 1
        else:
            return 0

# プレイアウト
def playout(board, ko, node, color, root_color):
    # 終局までランダムに打つ
    color_tmp = color
    for loop in range(GRID*GRID + 200):
        pre_xy = 0

        # 候補手一覧
        possibles = []
        for xy, c in enumerate(board):
            if c == SPACE:
                possibles.append(xy)
        
        while True:
            if len(possibles) == 0:
                selected = PASS
            else:
                # ランダムで手を選ぶ
                selected = possibles[random.randrange(len(possibles))]

            # 石を打つ
            err = move(board, ko, selected, color_tmp)

            if err == SUCCESS:
                break;

            # 手を削除
            possibles.remove(selected)

        # 連続パスで終了
        if selected == PASS and pre_xy == PASS:
            break

        # 一つ前の手を保存
        pre_xy = selected

        # プレイヤー交代
        color_tmp = -color_tmp

    # 終局 勝敗を返す
    return end_game(board, root_color)

# 思考ルーチン
class MCTSSample:

    def __init__(self, color):
        self.color = color

    def select_move(self, board, ko):
        self.root = UTCNode()
        expand_node(self.root, board)

        for i in range(PLAYOUT_MAX):
            # 局面コピー
            board_tmp = board[:]
            ko_tmp = ko.copy()

            # UCT
            search_uct(board_tmp, ko_tmp, self.color, self.root, self.color)

        # 最もプレイアウト数が多い手を選ぶ
        num_max = -999
        rate_min = 1 # 勝率
        rate_max = 0 # 勝率
        for child in self.root.child:
            if child.playout_num > 0:
                num = child.playout_num
                if num > num_max:
                    best_move = child
                    num_max = num

                if rate_min == 1:
                    rate = float(child.win_num) / child.playout_num
                    if rate < rate_min:
                        rate_min = rate
                if rate_max == 0:
                    rate = float(child.win_num) / child.playout_num
                    if rate > rate_max:
                        rate_max = rate

        if rate_min == 1:
            return PASS
        if rate_max == 0:
            return PASS

        return best_move.xy

# 人間プレイヤー
class Human:
    xy = -1

    def __init__(self, color):
        self.color = color

    def select_move(self, board, ko):

        while self.xy < 0:
            time.sleep(0.1)
            QtCore.QCoreApplication.processEvents()

        xy = self.xy
        self.xy = -1
        return xy

    def set_xy(self, x, y):
        self.xy = get_xy(x, y)

# メインウィンドウ
class MainWindow(QtGui.QWidget):

    # 初期化
    def __init__(self):
        super(MainWindow, self).__init__()
        self.app = app

        # 盤初期化
        self.board = create_board()

        # コウ
        self.ko = Ko()

        # 思考ルーチン一覧
        self.player_lists = []
        self.player_lists.append(MCTSSample)
        self.player_lists.append(Human)


        # プレイヤー選択
        self.selectedPlayer = []
        # Black
        self.selectedPlayer.append(self.player_lists[0])
        self.cmbPlayer = []
        self.labelBlack = QtGui.QLabel(self)
        self.labelBlack.setText("Black:")
        self.labelBlack.move(10, 10)
        self.cmbPlayer.append(QtGui.QComboBox(self))
        self.cmbPlayer[0].activated.connect(self.onActivatedBalack)
        self.cmbPlayer[0].move(10, 30)

        # White
        self.selectedPlayer.append(self.player_lists[0])
        x_white = BOARD_X0 + GRID_WIDTH * 10 + 10
        self.labelWhite = QtGui.QLabel(self)
        self.labelWhite.setText("White:")
        self.labelWhite.move(x_white, 10)
        self.cmbPlayer.append(QtGui.QComboBox(self))
        self.cmbPlayer[1].activated.connect(self.onActivatedWhite)
        self.cmbPlayer[1].move(x_white, 30)

        for player in self.player_lists:
            for cmb in self.cmbPlayer:
                cmb.addItem(player.__name__)

        self.current_player = None

        # 開始ボタン
        self.btnStart = QtGui.QPushButton(self)
        self.btnStart.setText("Start")
        self.btnStart.resize(GRID_WIDTH * 3, GRID_WIDTH)
        self.btnStart.clicked.connect(self.start)
        self.btnStart.move(BOARD_X0 + GRID_WIDTH * (GRID / 2 - 0.5), BOARD_Y0 + GRID_WIDTH * GRID / 2)

        # ウィンドウサイズ
        self.resize(BOARD_X0 * 2 + GRID_WIDTH * (GRID + 1), BOARD_Y0 * 2 + GRID_WIDTH * (GRID + 1))

    # 描画
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QColor(190, 160, 60))
        painter.drawRect(BOARD_X0, BOARD_Y0, GRID_WIDTH * 10, GRID_WIDTH * (GRID + 1))

        # 盤面
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 2))
        for x in range(1, GRID + 1):
            painter.drawLine(BOARD_X0 + GRID_WIDTH * x, BOARD_Y0 + GRID_WIDTH,
                                BOARD_X0 + GRID_WIDTH * x, BOARD_Y0 + GRID_WIDTH * GRID)
        for y in range(1, GRID + 1):
            painter.drawLine(BOARD_X0 + GRID_WIDTH, BOARD_Y0 + GRID_WIDTH * y,
                                BOARD_X0 + GRID_WIDTH * GRID, BOARD_Y0 + GRID_WIDTH * y)

        # 石
        for x in range(GRID):
            for y in range(GRID):
                xy = get_xy(x + 1, y + 1)
                c = self.board[xy]
                if c != SPACE:
                    if c == BLACK:
                        painter.setBrush(QtCore.Qt.black)
                    else:
                        painter.setBrush(QtCore.Qt.white)
                    painter.drawEllipse(BOARD_X0 + GRID_WIDTH * (x+0.5), BOARD_Y0 + GRID_WIDTH * (y+0.5), GRID_WIDTH, GRID_WIDTH)

        # 位置ごとの勝率を表示
        if isinstance(self.current_player, MCTSSample):
            painter.setPen(QtCore.Qt.red)
            for child in self.current_player.root.child:
                x, y = get_x_y(child.xy)
                text = "{0:^3}/{1:^3}".format(child.win_num, child.playout_num)
                painter.drawText(BOARD_X0 + GRID_WIDTH * (x-0.35), BOARD_Y0 + GRID_WIDTH * y, text)

        painter.end()

    # コンボボックス選択(Black)
    def onActivatedBalack(self, number):
        self.selectedPlayer[0] = self.player_lists[number]

    # コンボボックス選択(White)
    def onActivatedWhite(self, number):
        self.selectedPlayer[1] = self.player_lists[number]

    # Start
    def start(self):
        self.btnStart.hide()

        players = {BLACK : self.selectedPlayer[0](BLACK), WHITE : self.selectedPlayer[1](WHITE)}

        color = BLACK
        pre_xy = -1
        while True:
            # 局面コピー
            board_tmp = self.board[:]
            ko_tmp = self.ko.copy()

            # 手を選択
            start = time.time()

            self.current_player = players[color]
            xy = self.current_player.select_move(board_tmp, ko_tmp)

            elapsed_time = time.time() - start
            print ("elapsed_time:{0}".format(elapsed_time)) + "[sec]"

            # 石を打つ
            err = move(self.board, self.ko, xy, color)

            if err != SUCCESS:
                print "error {0},{1}".format(get_x_y(xy))
                break

            if xy == PASS and pre_xy == PASS:
                if end_game(board, BLACK) > 0:
                    print "black won."
                else:
                    print "white won."
                break

            # 描画更新
            self.update()
            QtCore.QCoreApplication.processEvents()

            pre_xy = xy
            color = -color

    # マウスクリック
    def mousePressEvent(self, event):
        if isinstance(self.current_player, Human):
            x = (event.pos().x() - BOARD_X0 + GRID_WIDTH/2) / GRID_WIDTH
            y = (event.pos().y() - BOARD_Y0 + GRID_WIDTH/2) / GRID_WIDTH
            #print "{0}, {1}".format(x, y)
            self.current_player.set_xy(x, y)

    # 閉じる
    def closeEvent(self, event):
        QtCore.QCoreApplication.quit()
        sys.exit()

# main
if __name__ == '__main__':
    if len(sys.argv) >= 2:
        PLAYOUT_MAX = int(sys.argv[1])
    app = QtGui.QApplication(sys.argv)
    mainwnd = MainWindow()
    mainwnd.show()
    sys.exit(app.exec_())
