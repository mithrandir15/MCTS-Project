from time import sleep
from typing import List
import gym

from Common.game_interface import GameInterface, Action


class AIGame(GameInterface):

    def __init__(self):
        self.env = gym.make('CartPole-v0')
        self.env.reset()
        self.game_over = False
        # self.env.render()

    def get_actions(self) -> List[Action]:
        return list(range(self.env.action_space.n))

    def apply_action(self, action: Action):
        step = self.env.step(action)
        print(step)
        self.game_over = step[2]
        self.env.render()
        sleep(0.1)

    def is_game_over(self, player_id: int) -> bool:
        return self.game_over
