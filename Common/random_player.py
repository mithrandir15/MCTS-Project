from Common.player_interface import PlayerInterface
from random import randint, seed


class RandomPlayer(PlayerInterface):

    def choose_action(self, actions, game, actions_since):
        return actions[randint(0, len(actions) - 1)]