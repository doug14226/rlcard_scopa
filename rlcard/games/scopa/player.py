class ScopaPlayer:
    """Represents a single Scopa player."""

    def __init__(self, player_id):
        self.player_id = player_id
        self.hand = []       # list of ScopaCard currently held
        self.captured = []   # list of ScopaCard captured during the round
        self.scopa_count = 0 # number of scope (sweeps) scored during play
