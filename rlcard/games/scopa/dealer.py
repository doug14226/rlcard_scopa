from rlcard.games.scopa.card import ScopaCard
from rlcard.games.scopa.utils import SUITS, RANKS


class ScopaDealer:
    """Manages the 40-card Italian Scopa deck."""

    def __init__(self, np_random):
        self.np_random = np_random
        self.deck = []
        self._init_deck()

    def _init_deck(self):
        self.deck = [ScopaCard(s, r) for s in SUITS for r in RANKS]

    def shuffle(self):
        self.np_random.shuffle(self.deck)

    def deal_card(self):
        return self.deck.pop()
