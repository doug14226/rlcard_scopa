import numpy as np
from collections import OrderedDict

from rlcard.envs import Env
from rlcard.games.scopa import Game
from rlcard.games.scopa.utils import suit_rank_from_id


class ScopaEnv(Env):
    """
    Scopa Environment for RLCard.

    Observation (163-dim float32 vector):
        [  0- 39] My hand             (binary, 1 = holding that card)
        [ 40- 79] Table cards         (binary)
        [ 80-119] My captured cards   (binary)
        [120-159] Opponent's captures (binary)
        [160]     My scopa count      (normalised by 10)
        [161]     Opponent scopa count(normalised by 10)
        [162]     Deck size           (normalised by 36)

    Actions: integer card_id in [0, 39], legal actions = cards in hand.

    Payoffs: +1 (win), 0 (tie), -1 (loss) per player at game end.
    """

    def __init__(self, config):
        self.name = 'scopa'
        self.game = Game()
        super().__init__(config)
        self.state_shape = [[163] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    # ------------------------------------------------------------------
    # Required Env interface methods
    # ------------------------------------------------------------------

    def _extract_state(self, state):
        obs = np.zeros(163, dtype=np.float32)

        for cid in state['hand']:
            obs[cid] = 1.0
        for cid in state['table']:
            obs[40 + cid] = 1.0
        for cid in state['my_captured']:
            obs[80 + cid] = 1.0
        for cid in state['opp_captured']:
            obs[120 + cid] = 1.0
        obs[160] = state['my_scopa_count'] / 10.0
        obs[161] = state['opp_scopa_count'] / 10.0
        obs[162] = state['deck_size'] / 36.0

        legal_actions = OrderedDict({cid: None for cid in state['legal_actions']})
        raw_legal = [
            ''.join(suit_rank_from_id(cid)) for cid in state['legal_actions']
        ]

        return {
            'obs': obs,
            'legal_actions': legal_actions,
            'raw_obs': state,
            'raw_legal_actions': raw_legal,
            'action_record': self.action_recorder,
        }

    def _decode_action(self, action_id):
        """
        Map RL action_id (card_id 0-39) to game action.
        Falls back to first legal action if the card is not in hand.
        """
        legal = self.game.get_state(self.game.get_player_id())['legal_actions']
        if action_id in legal:
            return action_id
        return legal[0]

    def _get_legal_actions(self):
        return self.game.get_state(self.game.get_player_id())['legal_actions']

    def get_payoffs(self):
        payoffs = self.game.judger.judge_payoffs(self.game.players)
        return np.array(payoffs, dtype=np.float32)
