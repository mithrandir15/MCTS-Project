from typing import List

from Common.player_interface import PlayerInterface
from AIGym.ai_game import AIGame


class GymReferee:
    def __init__(self, players: List[PlayerInterface]):
        # if len(players) < 3 or len(players) > 6:
        #    raise ValueError("Wrong # of players")
        self.players = players

    def run_game(self, game_number=-1):
        game = AIGame()
        while not game.is_game_over(0):
            possible_actions = game.get_actions()
            action = self.players[0].choose_action(possible_actions, game, [])
            game.apply_action(action)
