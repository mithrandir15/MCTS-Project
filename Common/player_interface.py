from typing import List

from Common.game_interface import Action, GameInterface


class PlayerInterface:

    def choose_action(self, actions: List[Action], game: GameInterface, actions_since: List[Action]):
        pass
