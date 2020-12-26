from typing import List


class Action:
    pass


class GameInterface:

    def get_actions(self) -> List[Action]:
        pass

    def apply_action(self, action: Action):
        pass

    def get_children(self):
        pass

    def is_game_over(self, player_id: int) -> bool:
        pass

    # Returns True iff player has lost
    def has_player_lost(self, player_id: int) -> bool:
        pass
