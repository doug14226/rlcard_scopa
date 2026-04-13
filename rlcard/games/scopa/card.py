from rlcard.games.scopa.utils import SUITS, RANKS


class ScopaCard:
    """A single card from the Italian Scopa deck."""

    def __init__(self, suit, rank):
        self.suit = suit  # 'D', 'C', 'S', 'B'
        self.rank = rank  # '1'-'7', 'J', 'Q', 'K'

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def __repr__(self):
        return f"ScopaCard({self.rank}{self.suit})"

    def __eq__(self, other):
        if isinstance(other, ScopaCard):
            return self.suit == other.suit and self.rank == other.rank
        return NotImplemented

    def __hash__(self):
        return SUITS.index(self.suit) * 10 + RANKS.index(self.rank)

    def get_index(self):
        return self.suit + self.rank
