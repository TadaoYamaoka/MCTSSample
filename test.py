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

if __name__ == '__main__':
    unittest.main()
