# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


# def print_hi(name):
#    Use a breakpoint in the code line below to debug your script.
#    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
from random import seed

from AIGym.gym_referee import GymReferee
from Common.mcts_player import MCTSPlayer
from Common.random_player import RandomPlayer
from Coup.coup_referee import CoupReferee

if __name__ == '__main__':
    for i in range(5):
        seed(i + 1542)
        ref = CoupReferee([RandomPlayer(), MCTSPlayer(1), RandomPlayer(), RandomPlayer()])
        # ref = GymReferee([RandomPlayer()])
        ref.run_game(game_number=i)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
