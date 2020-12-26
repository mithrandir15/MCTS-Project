from typing import List
from random import seed

from Common.player_interface import PlayerInterface
from Coup.coup_game import Coup


class CoupReferee:

    def __init__(self, players: List[PlayerInterface]):
        if len(players) < 3 or len(players) > 6:
            raise ValueError("Wrong # of players")
        self.players = players

    def run_game(self, game_number=-1):
        # seed(170)
        # print("hi")
        game = Coup(len(self.players))
        actions_taken = 0
        actions_since = {}

        for i in range(len(self.players)):
            actions_since[i] = []

        while (not game.is_game_over()) and actions_taken < 200:
            actions_taken += 1
            # print("Turn action: ", game.turn_action)
            # print("Dispute action: ", game.turn_dispute_action)
            # print("Counteraction: ", game.turn_counteraction)
            # print("Dispute counteraction: ", game.turn_dispute_counteraction)
            # print("Turn phase: ", game.turn_phase)
            # print("Turn index: ", game.turn_index)
            possible_actions = game.get_actions()
            current_id = possible_actions[0].acting_player
            # print([str(action) for action in possible_actions])
            chosen_action = self.players[current_id].choose_action(possible_actions,
                                                                   game, actions_since[current_id])
            # print(chosen_action)

            for i in range(len(self.players)):
                if i == current_id:
                    actions_since[i] = []
                else:
                    actions_since[i].append(chosen_action)

            # print()
            game.apply_action(chosen_action)

        if actions_taken >= 200:
            print("INF LOOP")
        else:
            print(game.get_winning_player())
