# -*- coding:utf-8 -*-
import unittest
from MCTSSample import *

class Test_test(unittest.TestCase):
    def test_001(self):
        board = create_board()
        ko = Ko()

        board[get_xy(1, 1)] = WHITE
        board[get_xy(2, 1)] = BLACK
        color = BLACK

        xy = get_xy(1, 2)

        move(board, ko, xy, color)

        self.assertEqual(board[get_xy(1, 1)], SPACE)

    def test_002(self):
        board = create_board()
        ko = Ko()

        board[get_xy(9, 5)] = WHITE
        board[get_xy(9, 6)] = BLACK
        board[get_xy(8, 5)] = BLACK
        color = BLACK

        xy = get_xy(9, 4)

        move(board, ko, xy, color)

        self.assertEqual(board[get_xy(9, 5)], SPACE)

    #def test_003(self):
    #            #   1  2  3  4  5  6  7  8  9 
    #    board = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    #             3, 1, 1, 1, 1, 1,-1, 0, 1, 0, 3, #1
    #             3, 1, 1, 1, 1, 1,-1, 0, 1, 1, 3, #2
    #             3, 1, 1, 1, 1, 1,-1, 0, 1, 0, 3, #3
    #             3, 1, 1, 1, 1, 1,-1, 0, 1, 1, 3, #4
    #             3, 1, 1, 1, 1, 1,-1, 0, 1, 1, 3, #5
    #             3, 1, 1, 1, 1, 1,-1, 0, 1, 1, 3, #6
    #             3,-1,-1,-1,-1, 1,-1, 0, 1, 1, 3, #7
    #             3, 0, 0, 0, 0, 0,-1, 0, 1, 1, 3, #8
    #             3, 0, 0, 0, 0, 1, 1, 1, 1, 1, 3, #9
    #             3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
    #    ko = Ko()

    #    color = WHITE
    #    player = MCTSSample(color)

    #    PLAYOUT_MAX = 200

    #    xy = player.select_move(board, ko)

    #    x, y = get_x_y(xy)
    #    print "{0},{1}".format(x, y)

    #    # プレイアウトの結果
    #    for child in player.root.child:
    #        x, y = get_x_y(child.xy)
    #        print "{0},{1} : {2} / {3}".format(x, y, child.win_num, child.playout_num)

    #    self.assertEqual(xy, get_xy(5, 8))

    def test_004(self):
                #   1  2  3  4  5  6  7  8  9 
        board = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                 3,-1,-1,-1,-1,-1, 1, 0,-1, 0, 3, #1
                 3,-1,-1,-1,-1,-1, 1, 0,-1,-1, 3, #2
                 3,-1,-1,-1,-1,-1, 1, 0,-1, 0, 3, #3
                 3,-1,-1,-1,-1,-1, 1, 0,-1,-1, 3, #4
                 3,-1,-1,-1,-1,-1, 1, 0,-1,-1, 3, #5
                 3,-1,-1,-1,-1,-1, 1, 0, 1, 1, 3, #6
                 3, 1, 1, 1, 1,-1, 1, 0, 1, 0, 3, #7
                 3, 0, 0, 0, 0, 0, 1, 0, 1, 1, 3, #8
                 3, 0, 0, 0, 0,-1,-1,-1, 1, 0, 3, #9
                 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        ko = Ko()

        color = BLACK
        player = MCTSSample(color)

        PLAYOUT_MAX = 200

        xy = player.select_move(board, ko)

        x, y = get_x_y(xy)
        print "{0},{1}".format(x, y)

        # プレイアウトの結果
        for child in player.root.child:
            x, y = get_x_y(child.xy)
            print "{0},{1} : {2} / {3}".format(x, y, child.win_num, child.playout_num)

        self.assertEqual(xy, get_xy(5, 8))

if __name__ == '__main__':
    unittest.main()
