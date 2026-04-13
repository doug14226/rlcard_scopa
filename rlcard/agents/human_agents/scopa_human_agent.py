from rlcard.games.scopa.utils import suit_rank_from_id, SUITS, RANKS, get_valid_captures, RANK_TO_VALUE


# Human-readable suit names
SUIT_NAMES = {'D': 'Denari', 'C': 'Coppe', 'S': 'Spade', 'B': 'Bastoni'}

# Unicode suit symbols for compact display
SUIT_SYMBOLS = {'D': 'D', 'C': 'C', 'S': 'S', 'B': 'B'}


def _card_str(cid):
    suit, rank = suit_rank_from_id(cid)
    return f'{rank}{suit}'  # e.g. '7D', 'KS'


def _cards_str(cid_list):
    if not cid_list:
        return '(empty)'
    return '  '.join(_card_str(c) for c in sorted(cid_list))


class HumanAgent(object):
    """A human agent for Scopa. Displays game state and prompts for card selection."""

    def __init__(self, num_actions):
        self.use_raw = False
        self.num_actions = num_actions

    @staticmethod
    def step(state):
        """Display state and prompt the human to choose a card to play.

        Args:
            state (dict): env state dict with 'raw_obs', 'legal_actions', 'action_record'

        Returns:
            action (int): card_id of the chosen card
        """
        _print_state(state['raw_obs'], state['action_record'])
        legal = list(state['legal_actions'].keys())  # list of card_ids

        while True:
            try:
                idx = int(input('>> Choose card index: '))
                if 0 <= idx < len(legal):
                    return legal[idx]
                print(f'Please enter a number between 0 and {len(legal) - 1}.')
            except ValueError:
                print('Invalid input — enter an integer.')

    def eval_step(self, state):
        return self.step(state), {}


def _print_state(raw_obs, action_record):
    """Print the current Scopa game state for the human player."""
    current = raw_obs['current_player']

    # Show what the opponent just played (last action before ours)
    _action_list = []
    for i in range(1, len(action_record) + 1):
        if action_record[-i][0] == current:
            break
        _action_list.insert(0, action_record[-i])
    for player_id, action in _action_list:
        print(f'>> Player {player_id} played {_card_str(action)}')

    print('\n========== Table Cards ==========')
    print(_cards_str(raw_obs['table']))

    print('\n=========== Your Hand ===========')
    legal = raw_obs['legal_actions']
    for i, cid in enumerate(legal):
        suit, rank = suit_rank_from_id(cid)
        captures = get_valid_captures(rank, _make_table_cards(raw_obs['table']))
        cap_note = ' [captures!]' if captures else ''
        print(f'  {i}: {_card_str(cid)}{cap_note}')

    print('\n======= Score Tracker ==========')
    my_cap = raw_obs['my_captured']
    opp_cap = raw_obs['opp_captured']
    my_denari = sum(1 for c in my_cap if suit_rank_from_id(c)[0] == 'D')
    opp_denari = sum(1 for c in opp_cap if suit_rank_from_id(c)[0] == 'D')
    print(f'  You:      {len(my_cap):2d} cards  {my_denari:2d} Denari  {raw_obs["my_scopa_count"]} scope')
    print(f'  Opponent: {len(opp_cap):2d} cards  {opp_denari:2d} Denari  {raw_obs["opp_scopa_count"]} scope')
    print(f'  Deck remaining: {raw_obs["deck_size"]}')
    print()


class _FakeCard:
    """Minimal card object for get_valid_captures (needs .rank and .suit)."""
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank


def _make_table_cards(table_ids):
    return [_FakeCard(*suit_rank_from_id(cid)) for cid in table_ids]
