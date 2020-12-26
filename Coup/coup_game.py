from enum import Enum, auto
from typing import List, Optional
from random import shuffle

from Common.game_interface import GameInterface, Action


class CoupCards(Enum):
    DUKE = auto()
    ASSASSIN = auto()
    CAPTAIN = auto()
    AMBASSADOR = auto()
    CONTESSA = auto()


class CoupActionType(Enum):
    # Regular actions
    INCOME = auto()
    FOREIGN_AID = auto()
    TAX = auto()
    STEAL = auto()
    EXCHANGE = auto()
    ASSASSINATE = auto()
    COUP = auto()

    # Passing actions
    PASS = auto()

    # Counter-actions
    BLOCK_FOREIGN_AID = auto()
    BLOCK_STEAL = auto()
    BLOCK_ASSASSINATE = auto()
    DISPUTE = auto()

    # Choice actions:
    CHOOSE_EXCHANGED = auto()
    CHOOSE_REMOVED = auto()

    # System actions
    REMOVE_CARD_FROM_PLAYER = auto()


CARD_ACTION_TYPES = {CoupCards.DUKE: [CoupActionType.TAX, CoupActionType.BLOCK_FOREIGN_AID],
                     CoupCards.ASSASSIN: [CoupActionType.ASSASSINATE],
                     CoupCards.CAPTAIN: [CoupActionType.STEAL, CoupActionType.BLOCK_STEAL],
                     CoupCards.AMBASSADOR: [CoupActionType.EXCHANGE, CoupActionType.BLOCK_STEAL],
                     CoupCards.CONTESSA: [CoupActionType.BLOCK_ASSASSINATE]}

BLOCKABLE_ACTION_TYPES = [CoupActionType.ASSASSINATE,
                          CoupActionType.STEAL,
                          CoupActionType.FOREIGN_AID]


class CoupAction(Action):
    def __init__(self, action_type: CoupActionType, acting_player, target_player=-1,
                 card_removed=None, card_exchanged=None):
        self.action_type = action_type
        self.acting_player = acting_player
        self.target_player = target_player
        self.card_removed = card_removed
        self.card_exchanged = card_exchanged

    def __str__(self):
        return " ".join([str(self.action_type),
                         str(self.acting_player),
                         str(self.target_player),
                         str(self.card_removed),
                         str(self.card_exchanged)])

    def __eq__(self, other):
        if not isinstance(other, CoupAction):
            return False
        return self.action_type == other.action_type \
               and self.acting_player == other.acting_player \
               and self.target_player == other.target_player \
               and self.card_removed == other.card_removed \
               and self.card_exchanged == other.card_exchanged

    def __attrs(self):
        return (self.action_type,
                self.acting_player,
                self.target_player,
                self.card_removed,
                self.card_exchanged)

    def __hash__(self):
        return hash(self.__attrs())


class CoupPlayerData:
    def __init__(self, initial_cards: List[CoupCards]):
        self.num_coins = 2
        self.cards = initial_cards


class TurnPhase(Enum):
    ACTION = auto()
    DISPUTE_ACTION = auto()
    COUNTERACTION = auto()
    DISPUTE_COUNTERACTION = auto()


class Coup(GameInterface):

    def __init__(self, num_players: int):
        self.deck: List[CoupCards] = []
        self.players: List[CoupPlayerData] = []
        self.init_deck()
        self.deal_cards(num_players)

        self.turn_index: int = 0
        self.priority_index: int = 0
        self.turn_action: Optional[CoupAction] = None
        self.turn_dispute_action: Optional[CoupAction] = None
        self.turn_counteraction: Optional[CoupAction] = None
        self.turn_dispute_counteraction: Optional[CoupAction] = None
        self.requires_choice: List[CoupAction] = []
        self.turn_phase: TurnPhase = TurnPhase.ACTION

    def init_deck(self):
        for card in CoupCards:
            for i in range(3):
                self.deck.append(card)
        shuffle(self.deck)

    def deal_cards(self, num_players: int):
        for i in range(num_players):
            card_list = []
            for j in range(2):
                card_list.append(self.deck.pop())
            self.players.append(CoupPlayerData(card_list))

    def get_actions(self) -> List[CoupAction]:
        if self.requires_choice:
            target_player = self.requires_choice[-1].target_player
            requires_choice = self.requires_choice[-1]
            if requires_choice.action_type == CoupActionType.EXCHANGE:
                return self._get_possible_exchange_choices(target_player)
            elif requires_choice.action_type == CoupActionType.REMOVE_CARD_FROM_PLAYER:
                return self._get_possible_removal_choices(target_player)
        if self.turn_phase == TurnPhase.ACTION:
            return self._get_possible_initial_actions()
        elif self.turn_phase == TurnPhase.DISPUTE_ACTION:
            return self._get_possible_disputes()
        elif self.turn_phase == TurnPhase.COUNTERACTION:
            return self._get_possible_blocks()
        elif self.turn_phase == TurnPhase.DISPUTE_COUNTERACTION:
            return self._get_possible_disputes()

    def _get_possible_initial_actions(self):
        possible_actions = []
        possible_actions.extend([CoupAction(CoupActionType.INCOME, self.turn_index),
                                 CoupAction(CoupActionType.FOREIGN_AID, self.turn_index),
                                 CoupAction(CoupActionType.TAX, self.turn_index),
                                 CoupAction(CoupActionType.EXCHANGE, self.turn_index,
                                            target_player=self.turn_index)])
        if self.players[self.turn_index].num_coins >= 3:
            possible_actions.extend(self._get_action_for_each_player(CoupActionType.ASSASSINATE,
                                                                     self.turn_index))
            if self.players[self.turn_index].num_coins >= 7:
                possible_actions.extend(self._get_action_for_each_player(CoupActionType.COUP,
                                                                         self.turn_index))
        return possible_actions

    def _get_possible_removal_choices(self, target_player: int):
        possible_actions = []
        for removing_card in self.players[target_player].cards:
            possible_actions.append(CoupAction(CoupActionType.CHOOSE_REMOVED,
                                               target_player,
                                               target_player=target_player,
                                               card_removed=removing_card))
        return possible_actions

    # CHOOSE_EXCHANGED: Action exchanging [your card] for [a card you drew]
    def _get_possible_exchange_choices(self, target_player: int):
        possible_actions = []
        self.exchange_pile = [self.deck.pop(), self.deck.pop(), self.deck.pop()]
        for removing_card in self.players[target_player].cards:
            for drawn_card in self.exchange_pile:
                possible_actions.append(CoupAction(CoupActionType.CHOOSE_EXCHANGED,
                                                   target_player,
                                                   card_removed=removing_card,
                                                   card_exchanged=drawn_card))
        return possible_actions

    def _get_possible_blocks(self):
        possible_actions = []
        if self.turn_action.action_type == CoupActionType.FOREIGN_AID:
            possible_actions.append(CoupAction(CoupActionType.BLOCK_FOREIGN_AID,
                                               self.priority_index,
                                               target_player=self.turn_index))
        if self.priority_index == self.turn_action.target_player:
            if self.turn_action.action_type == CoupActionType.ASSASSINATE:
                possible_actions.append(CoupAction(CoupActionType.BLOCK_ASSASSINATE,
                                                   self.priority_index,
                                                   target_player=self.turn_index))
            elif self.turn_action.action_type == CoupActionType.STEAL:
                possible_actions.append(CoupAction(CoupActionType.BLOCK_STEAL,
                                                   self.priority_index,
                                                   target_player=self.turn_index))
            if self.turn_action.action_type in [CoupActionType.ASSASSINATE, CoupActionType.COUP]:
                pass
                # for removed_card in self.players[self.priority_index].cards:
                #     possible_actions.append(CoupAction(CoupActionType.CHOOSE_REMOVED,
                #                                        self.priority_index,
                #                                        target_player=self.priority_index,
                #                                        card_removed=removed_card))
        possible_actions.append(CoupAction(CoupActionType.PASS, self.priority_index))
        return possible_actions

    def _get_possible_disputes(self):
        possible_disputes = []
        if self.turn_phase == TurnPhase.DISPUTE_ACTION:
            possible_disputes.append(CoupAction(CoupActionType.DISPUTE, self.priority_index,
                                                target_player=self.turn_index))
        elif self.turn_phase == TurnPhase.DISPUTE_COUNTERACTION:
            possible_disputes.append(CoupAction(CoupActionType.DISPUTE, self.priority_index,
                                                target_player=self.turn_counteraction.acting_player))
        possible_disputes.append(CoupAction(CoupActionType.PASS, self.priority_index))
        return possible_disputes

    def _get_action_for_each_player(self, action_type: CoupActionType, acting_player: int) -> \
            List[CoupAction]:
        action_list = []
        for i in range(len(self.players)):
            if i != acting_player and self.players[i].cards:
                action_list.append(CoupAction(action_type, acting_player, target_player=i))
        return action_list

    def apply_action(self, action: CoupAction):
        if action.action_type == CoupActionType.CHOOSE_EXCHANGED:
            self.requires_choice.pop()
            self._exchange_cards(action)
            self._fix_priority_index()
        elif action.action_type == CoupActionType.CHOOSE_REMOVED:
            self.requires_choice.pop()
            self._remove_card(action.target_player, action.card_removed)
            self._fix_priority_index()
        elif self.turn_action is None and self.turn_phase == TurnPhase.ACTION:
            # Unblockable initial actions
            if action.action_type in [CoupActionType.INCOME, CoupActionType.COUP]:
                self._execute_initial_action(action)
            # Blockable but indisputable
            elif action.action_type == CoupActionType.FOREIGN_AID:
                self.turn_action = action
                self.turn_phase = TurnPhase.COUNTERACTION
                self._increment_priority()
            else:
                self.turn_action = action
                self.turn_phase = TurnPhase.DISPUTE_ACTION
                self._increment_priority()
        elif self.turn_action is None:
            raise RuntimeError("Is this a bug? turn_action is None")
        elif action.action_type == CoupActionType.DISPUTE:
            self._dispute(action)
        elif action.action_type == CoupActionType.PASS:
            self._increment_priority()
            # Check if everyone's passed
            if self.turn_phase == TurnPhase.DISPUTE_ACTION:
                if self.priority_index == self.turn_index:
                    self._advance_phase_from_dispute()
            elif self.turn_phase == TurnPhase.DISPUTE_COUNTERACTION:
                if self.priority_index == self.turn_counteraction.acting_player:
                    # Action was blocked, go to next turn
                    self._increment_turn()
            elif self.turn_phase == TurnPhase.COUNTERACTION:
                if self.turn_action.action_type == CoupActionType.FOREIGN_AID:
                    if self.priority_index == self.turn_action.acting_player:
                        # Action was NOT blocked, execute action
                        self._execute_initial_action(self.turn_action)
                else:
                    # Person targeted hasn't blocked, execute action
                    self._execute_initial_action(self.turn_action)
        elif action.action_type in [CoupActionType.BLOCK_ASSASSINATE,
                                    CoupActionType.BLOCK_STEAL,
                                    CoupActionType.BLOCK_FOREIGN_AID]:
            # TODO: Edge case where 1 claimed Duke blocks, correctly disputed, other Dukes can block
            self.turn_counteraction = action
            self.turn_phase = TurnPhase.DISPUTE_COUNTERACTION
            self._increment_priority()

    # Called after executing a choice action outside the usual turn structure.
    def _fix_priority_index(self):
        if self.requires_choice:
            self.priority_index = self.requires_choice[-1].target_player
        elif self.turn_phase == TurnPhase.ACTION:
            self.priority_index = self.turn_index
        elif self.turn_phase in [TurnPhase.DISPUTE_ACTION, TurnPhase.DISPUTE_COUNTERACTION]:
            self.priority_index = self.turn_index
            self._increment_priority()
        elif self.turn_phase == TurnPhase.COUNTERACTION:
            if self.turn_action.action_type in BLOCKABLE_ACTION_TYPES:
                if self.turn_action.action_type != CoupActionType.FOREIGN_AID:
                    self.priority_index = self.turn_action.target_player
                else:
                    # Player just past the current player gets to block
                    self.priority_index = self.turn_index
                    self._increment_priority()

    def _execute_initial_action(self, action):
        if action.action_type == CoupActionType.INCOME:
            self.players[self.turn_index].num_coins += 1
            self._increment_turn()
        elif action.action_type == CoupActionType.COUP:
            self.players[self.turn_index].num_coins -= 7
            self._put_remove_action(action.target_player)
            if not self.is_game_over():
                self._increment_turn()
            # Turn still increments w/ Coup and Ass, remove action just gets called at start of turn
        elif action.action_type == CoupActionType.FOREIGN_AID:
            self.players[self.turn_index].num_coins += 2
            self._increment_turn()
        elif action.action_type == CoupActionType.TAX:
            self.players[self.turn_index].num_coins += 3
            self._increment_turn()
        elif action.action_type == CoupActionType.STEAL:
            coins_stolen = min(2, self.players[action.target_player].num_coins)
            self.players[self.turn_index].num_coins += coins_stolen
            self.players[action.target_player].num_coins -= coins_stolen
        elif action.action_type == CoupActionType.ASSASSINATE:
            self.players[self.turn_index].num_coins -= 3
            self._put_remove_action(action.target_player)
            if not self.is_game_over():
                self._increment_turn()
        elif action.action_type == CoupActionType.EXCHANGE:
            self.requires_choice.append(action)

    def _increment_priority(self):
        if self.is_game_over():
            raise RuntimeError("Shouldn't have incremented priority while game is over")
        self.priority_index = (self.priority_index + 1) % len(self.players)
        i = 0
        while not self.players[self.priority_index].cards:
            i += 1
            self.priority_index = (self.priority_index + 1) % len(self.players)

    def _increment_turn(self):
        self.turn_action = None
        self.turn_dispute_action = None
        self.turn_counteraction = None
        self.turn_dispute_counteraction = None
        self.turn_phase = TurnPhase.ACTION
        # Doesn't reset requires_choice, those are dealt with at beginning of next turn

        if self.is_game_over():
            raise RuntimeError("Shouldn't have incremented turn while game is over")
        self.turn_index = (self.turn_index + 1) % len(self.players)
        i = 0
        while not self.players[self.turn_index].cards:
            i += 1
            self.turn_index = (self.turn_index + 1) % len(self.players)
        self.priority_index = self.turn_index

    # If player has 1 card, removes it. Otherwise, he gets to make a choice.
    def _put_remove_action(self, target_player):
        if len(self.players[target_player].cards) == 1:
            self._remove_card(target_player, self.players[target_player].cards[0])
        else:
            self.requires_choice.append(CoupAction(CoupActionType.REMOVE_CARD_FROM_PLAYER, -1,
                                                   target_player=target_player))
            self.priority_index = target_player

    def _exchange_cards(self, choose_exchanged_action):
        player_object = self.players[choose_exchanged_action.acting_player]
        self.deck.append(choose_exchanged_action.card_removed)
        player_object.cards.remove(choose_exchanged_action.card_removed)
        player_object.cards.append(choose_exchanged_action.card_exchanged)
        self.exchange_pile.remove(choose_exchanged_action.card_exchanged)
        self.deck.extend(self.exchange_pile)
        self.exchange_pile = []
        shuffle(self.deck)

    def _remove_card(self, target_player, target_card):
        self.players[target_player].cards.remove(target_card)
        # Removes anything that targets a dead player
        if not self.players[target_player].cards:
            for i in range(len(self.requires_choice)):
                if self.requires_choice[i].target_player == target_player:
                    if self.requires_choice[i].action_type == CoupActionType.EXCHANGE:
                        self.deck.extend(self.exchange_pile)
                        self.exchange_pile = []
                    self.requires_choice.pop(i)
                    i -= 1
            if self.turn_index == target_player or (self.turn_action is not None
                                                    and self.turn_action.target_player == target_player):
                if not self.is_game_over():
                    self._increment_turn()

    def _dispute(self, dispute_action):
        if self.turn_phase == TurnPhase.DISPUTE_ACTION:
            target_action = self.turn_action
        elif self.turn_phase == TurnPhase.DISPUTE_COUNTERACTION:
            target_action = self.turn_counteraction
        else:
            raise RuntimeError("Disputed on turn phase " + str(self.turn_phase))
        for card in self.players[dispute_action.target_player].cards:
            if target_action.action_type in CARD_ACTION_TYPES[card]:
                # Player had card, dispute is canceled and disputing player loses a card
                self._advance_phase_from_dispute()
                self._put_remove_action(dispute_action.acting_player)
                return
        self._increment_turn()
        self._put_remove_action(dispute_action.target_player)

    # Called if initial action isn't rightly disputed.
    # Advances to blocking phase if able, otherwise executes the action.
    def _advance_phase_from_dispute(self):
        if self.turn_action.action_type in BLOCKABLE_ACTION_TYPES and self.turn_phase == TurnPhase.DISPUTE_ACTION:
            self.turn_phase = TurnPhase.COUNTERACTION
            if self.turn_action.action_type != CoupActionType.FOREIGN_AID:
                self.priority_index = self.turn_action.target_player
            else:
                # Player just past the current player gets to block
                self.priority_index = self.turn_index
                self._increment_priority()
        else:
            self._execute_initial_action(self.turn_action)

    # Returns true iff game is over
    def is_game_over(self):
        num_active_players = 0
        for player in self.players:
            if player.cards:
                num_active_players += 1
        return num_active_players < 2

    def get_winning_player(self):
        for i in range(len(self.players)):
            if self.players[i].cards:
                return i

    def randomize_cards_except(self, player_id: int):
        num_cards_of_player = {}
        for i in range(len(self.players)):
            if i != player_id:
                num_cards_of_player[i] = len(self.players[i].cards)
                self.deck.extend(self.players[i].cards)
                self.players[i].cards = []
        shuffle(self.deck)
        for i in range(len(self.players)):
            if i != player_id:
                for j in range(num_cards_of_player[i]):
                    self.players[i].cards.append(self.deck.pop())

    def has_player_lost(self, player_id: int):
        return not bool(self.players[player_id].cards)
