import copy
from typing import List, Dict
from math import sqrt, log
from random import randint

from Common.player_interface import Action, GameInterface, PlayerInterface
from Coup.coup_game import Coup

NUM_ROLLOUTS = 1000
EXPLORATION_PARAMETER = sqrt(2)


class MCT:
    def __init__(self, player_id):
        self.player_id = player_id
        self.num_wins = 0
        self.num_simulations = 0
        self.children: Dict[Action, MCT] = {}


class MCTSPlayer(PlayerInterface):

    def __init__(self, player_id: int):
        self.mct = MCT(player_id)
        self.player_id = player_id

    def choose_action(self, actions: List[Action], game: GameInterface, actions_since: List[Action]):
        self.game = game
        self._update_mct_with_actions_since(actions_since)
        for i in range(NUM_ROLLOUTS):
            self.do_rollout()
        # chosen_move = self._find_most_played_move(actions, self.mct)
        chosen_move = self._find_best_move(actions, self.mct, 0)
        self.mct = self.mct.children[chosen_move]
        return chosen_move

    # Currently unused due to an unresolved bug
    def _find_most_played_move(self, possible_actions: List[Action], mct: MCT):
        most_played = None
        greatest_n = -1
        for action in mct.children.keys():
            if action in possible_actions and mct.children[action].num_simulations > greatest_n:
                most_played = action
                greatest_n = mct.children[action].num_simulations
        return most_played


    def _update_mct_with_actions_since(self, actions_since):
        mct = self.mct
        for action in actions_since:
            if action in mct.children.keys():
                mct = mct.children[action]
            else:
                print("New MCT")
                mct = MCT(self.player_id)
                break
        self.mct = mct

    def do_rollout(self):
        game = copy.deepcopy(self.game)
        if isinstance(game, Coup):
            game.randomize_cards_except(self.player_id)

        mct = self.mct
        mct.num_simulations += 1
        mct_list = [self.mct]
        while not game.is_game_over():
            possible_actions = game.get_actions()
            best_move = self._find_best_move(possible_actions, mct, EXPLORATION_PARAMETER)
            game.apply_action(best_move)
            if best_move in mct.children.keys():
                mct = mct.children[best_move]
            else:
                mct.children[best_move] = MCT(possible_actions[0].acting_player)
                mct = mct.children[best_move]
            mct.num_simulations += 1
            mct_list.append(mct)

        winner = game.get_winning_player()
        for mct in mct_list:
            if winner == mct.player_id:
                mct.num_wins += 1

    # Returns the move with the greatest move value according to UCT
    def _find_best_move(self, possible_actions: List[Action], mct: MCT, exploration_parameter: float):
        possible_actions_values = []
        for action in possible_actions:
            if action in mct.children.keys():
                num_wins = mct.children[action].num_wins
                num_sims = mct.children[action].num_simulations + 1
            else:
                num_wins = 0
                num_sims = 1
            num_sims_of_parent = mct.num_simulations + 1
            possible_actions_values.append(self._get_move_value(num_wins,
                                                                num_sims,
                                                                num_sims_of_parent,
                                                                exploration_parameter))

        # Chooses a random action from among the actions w/ the best values.
        best_action_value = max(possible_actions_values)
        best_action_indices = []
        for i in range(len(possible_actions_values)):
            if possible_actions_values[i] == best_action_value:
                best_action_indices.append(i)
        chosen_index = best_action_indices[randint(0, len(best_action_indices) - 1)]
        return possible_actions[chosen_index]

    # UCT: Upper confidence bound applied to trees
    def _get_move_value(self, num_wins, num_sims, num_sims_of_parent, exp_parameter):
        return (float(num_wins) / num_sims) + exp_parameter * sqrt(log(num_sims_of_parent) / num_sims)
