from copy import deepcopy
import numpy as np

from rlcard.games.scopa.dealer import ScopaDealer
from rlcard.games.scopa.player import ScopaPlayer
from rlcard.games.scopa.judger import ScopaJudger
from rlcard.games.scopa.utils import (
    card_id, suit_rank_from_id,
    get_valid_captures, best_capture,
)


class ScopaGame:
    """
    Two-player Scopa card game engine.

    Deck:  40-card Italian deck (4 suits x 10 ranks).
    Setup: 4 cards dealt face-up to the table; 3 cards dealt to each player.
    Play:  Players alternate turns. On each turn a player plays one card:
           - If the table contains matching card(s) or a summing combination,
             the player captures them (single-card match takes priority).
           - Otherwise the card is trailed (placed on the table).
           - Clearing the table earns a scopa (+1 point).
    Deal:  When both hands are empty and the deck has cards, deal 3 more each.
    End:   When deck and hands are all empty. Remaining table cards go to the
           player who made the last capture.
    Score: Carte, Denari, Settebello, Primiera, plus accumulated scope.
    """

    def __init__(self, allow_step_back=False):
        self.allow_step_back = allow_step_back
        self.np_random = np.random.RandomState()
        self.num_players = 2
        self.first_player = 0  # set before init_game to control who plays first

    def configure(self, game_config):
        """Placeholder for potential future config (e.g. num players, target score)."""
        pass

    # ------------------------------------------------------------------
    # Core game interface
    # ------------------------------------------------------------------

    def init_game(self):
        """Initialise a new round and return (state, player_id)."""
        self.dealer = ScopaDealer(self.np_random)
        self.dealer.shuffle()

        self.players = [ScopaPlayer(i) for i in range(self.num_players)]
        self.judger = ScopaJudger()

        # 4 cards face-up on the table
        self.table = [self.dealer.deal_card() for _ in range(4)]

        # 3 cards in each player's hand
        for p in self.players:
            p.hand = [self.dealer.deal_card() for _ in range(3)]

        self.game_pointer = self.first_player
        self.last_capturer = self.first_player
        self._is_over = False
        self.history = []

        return self.get_state(self.game_pointer), self.game_pointer

    def step(self, action):
        """
        Advance the game by one move.

        Args:
            action (int): card_id (0-39) of the card to play from hand.

        Returns:
            (dict, int): next state and next player_id.
        """
        if self.allow_step_back:
            self.history.append(self._snapshot())

        player = self.players[self.game_pointer]

        # Remove the played card from hand
        card = self._find_card(player.hand, action)
        player.hand.remove(card)

        # Determine and execute captures
        captures = get_valid_captures(card.rank, self.table)
        if captures:
            chosen = best_capture(captures)
            for c in chosen:
                self.table.remove(c)
            player.captured.extend(chosen)
            player.captured.append(card)
            self.last_capturer = self.game_pointer
            # Scopa: swept the table clean
            if not self.table:
                player.scopa_count += 1
        else:
            # Trail: no capture possible
            self.table.append(card)

        # Advance turn
        self.game_pointer = (self.game_pointer + 1) % self.num_players

        # Refill hands or end the game when both hands are empty
        if all(len(p.hand) == 0 for p in self.players):
            if self.dealer.deck:
                for p in self.players:
                    for _ in range(3):
                        if self.dealer.deck:
                            p.hand.append(self.dealer.deal_card())
            else:
                # Remaining table cards go to the last player who captured
                if self.table:
                    self.players[self.last_capturer].captured.extend(self.table)
                    self.table = []
                self._is_over = True

        return self.get_state(self.game_pointer), self.game_pointer

    def step_back(self):
        """Undo the last move (requires allow_step_back=True)."""
        if not self.allow_step_back or not self.history:
            return False
        self._restore(self.history.pop())
        return True

    def is_over(self):
        return self._is_over

    def get_player_id(self):
        return self.game_pointer

    def get_num_players(self):
        return self.num_players

    @staticmethod
    def get_num_actions():
        """40 possible actions: one per card in the Italian deck."""
        return 40

    def get_state(self, player_id):
        """
        Return the observable state for player_id.

        Returns a dict with:
            hand          - list of card_ids in the player's hand
            table         - list of card_ids on the table
            my_captured   - list of card_ids the player has captured
            opp_captured  - list of card_ids the opponent has captured
            my_scopa_count  - int
            opp_scopa_count - int
            deck_size       - int (cards remaining)
            legal_actions   - list of card_ids (same as hand)
            current_player  - int
        """
        player = self.players[player_id]
        opp = self.players[1 - player_id]

        hand_ids = [card_id(c.suit, c.rank) for c in player.hand]

        return {
            'hand': hand_ids,
            'table': [card_id(c.suit, c.rank) for c in self.table],
            'my_captured': [card_id(c.suit, c.rank) for c in player.captured],
            'opp_captured': [card_id(c.suit, c.rank) for c in opp.captured],
            'my_scopa_count': player.scopa_count,
            'opp_scopa_count': opp.scopa_count,
            'deck_size': len(self.dealer.deck),
            'legal_actions': list(hand_ids),
            'current_player': player_id,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_card(self, hand, action_id):
        suit, rank = suit_rank_from_id(action_id)
        for c in hand:
            if c.suit == suit and c.rank == rank:
                return c
        raise ValueError(f"Card id {action_id} ({suit}{rank}) not found in hand")

    def _snapshot(self):
        return {
            'table': deepcopy(self.table),
            'hand0': deepcopy(self.players[0].hand),
            'hand1': deepcopy(self.players[1].hand),
            'captured0': deepcopy(self.players[0].captured),
            'captured1': deepcopy(self.players[1].captured),
            'scopa0': self.players[0].scopa_count,
            'scopa1': self.players[1].scopa_count,
            'deck': deepcopy(self.dealer.deck),
            'game_pointer': self.game_pointer,
            'last_capturer': self.last_capturer,
            'is_over': self._is_over,
        }

    def _restore(self, snap):
        self.table = snap['table']
        self.players[0].hand = snap['hand0']
        self.players[1].hand = snap['hand1']
        self.players[0].captured = snap['captured0']
        self.players[1].captured = snap['captured1']
        self.players[0].scopa_count = snap['scopa0']
        self.players[1].scopa_count = snap['scopa1']
        self.dealer.deck = snap['deck']
        self.game_pointer = snap['game_pointer']
        self.last_capturer = snap['last_capturer']
        self._is_over = snap['is_over']
