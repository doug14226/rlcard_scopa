from itertools import combinations

# Italian Scopa deck: 4 suits x 10 ranks = 40 cards
SUITS = ['D', 'C', 'S', 'B']   # Denari, Coppe, Spade, Bastoni
RANKS = ['1', '2', '3', '4', '5', '6', '7', 'J', 'Q', 'K']
RANK_TO_VALUE = {r: i + 1 for i, r in enumerate(RANKS)}  # 1-10

# Primiera point values (for end-of-round scoring)
PRIMIERA_VALUES = {
    '7': 21, '6': 18, '1': 16, '5': 15,
    '4': 14, '3': 13, '2': 12, 'J': 10, 'Q': 10, 'K': 10,
}

SETTEBELLO_SUIT = 'D'
SETTEBELLO_RANK = '7'


def card_id(suit, rank):
    """Convert (suit, rank) to a unique integer 0-39."""
    return SUITS.index(suit) * 10 + RANKS.index(rank)


def suit_rank_from_id(cid):
    """Convert card_id back to (suit, rank) tuple."""
    return SUITS[cid // 10], RANKS[cid % 10]


def rank_value(rank):
    return RANK_TO_VALUE[rank]


def get_valid_captures(played_rank, table_cards):
    """
    Return all valid capture sets for a played card given the current table.

    Rules:
    - Single-card matches (same rank) take priority over multi-card combinations.
    - If multiple single-card matches exist, each is a separate option.
    - If no single match, return all combinations of table cards whose values sum
      to the played card's value.
    - Returns list of lists; each inner list is one capture option.
    """
    pv = rank_value(played_rank)
    singles = [c for c in table_cards if rank_value(c.rank) == pv]
    if singles:
        return [[c] for c in singles]

    combos = []
    n = len(table_cards)
    for size in range(2, n + 1):
        for combo in combinations(table_cards, size):
            if sum(rank_value(c.rank) for c in combo) == pv:
                combos.append(list(combo))
    return combos


def best_capture(options):
    """
    Auto-select the best capture from a list of options.
    Priority: contains Settebello > most Denari cards > most cards total.
    """
    if not options:
        return None
    if len(options) == 1:
        return options[0]

    def score_option(opt):
        has_settebello = any(
            c.suit == SETTEBELLO_SUIT and c.rank == SETTEBELLO_RANK for c in opt
        )
        denari_count = sum(1 for c in opt if c.suit == 'D')
        return (has_settebello, denari_count, len(opt))

    return max(options, key=score_option)


def compute_primiera(cards):
    """
    Compute a player's Primiera score.
    Requires at least one card per suit; returns 0 if any suit is missing.
    """
    best = {}
    for c in cards:
        v = PRIMIERA_VALUES[c.rank]
        if c.suit not in best or v > best[c.suit]:
            best[c.suit] = v
    if len(best) < 4:
        return 0
    return sum(best.values())


def compute_round_scores(players):
    """
    Compute integer point scores for each player at the end of a round.

    Points awarded:
    - Scope:     1 pt each (accumulated during play)
    - Carte:     1 pt for player with more captured cards (tie = no point)
    - Denari:    1 pt for player with more Denari captured (tie = no point)
    - Settebello: 1 pt for player who captured the 7 of Denari
    - Primiera:  1 pt for player with higher Primiera (tie = no point)

    Returns:
        list[int]: [score_player0, score_player1]
    """
    scores, _ = compute_round_scores_detail(players)
    return scores


def compute_round_scores_detail(players):
    """
    Compute scores and a per-category breakdown for each player at the end of a round.

    Returns:
        tuple:
            scores (list[int]): [score_player0, score_player1]
            breakdown (dict): per-category results with winner index (None = tie/not awarded):
                'scope':      {'counts': [p0, p1]}
                'carte':      {'winner': 0|1|None, 'counts': [p0_cards, p1_cards]}
                'denari':     {'winner': 0|1|None, 'counts': [p0_denari, p1_denari]}
                'settebello': {'winner': 0|1}
                'primiera':   {'winner': 0|1|None, 'values': [p0_prim, p1_prim]}
    """
    scores = [p.scopa_count for p in players]
    breakdown = {
        'scope': {'counts': [players[0].scopa_count, players[1].scopa_count]},
    }

    # Carte
    counts = [len(p.captured) for p in players]
    if counts[0] > counts[1]:
        scores[0] += 1
        carte_winner = 0
    elif counts[1] > counts[0]:
        scores[1] += 1
        carte_winner = 1
    else:
        carte_winner = None
    breakdown['carte'] = {'winner': carte_winner, 'counts': counts}

    # Denari
    denari = [sum(1 for c in p.captured if c.suit == 'D') for p in players]
    if denari[0] > denari[1]:
        scores[0] += 1
        denari_winner = 0
    elif denari[1] > denari[0]:
        scores[1] += 1
        denari_winner = 1
    else:
        denari_winner = None
    breakdown['denari'] = {'winner': denari_winner, 'counts': denari}

    # Settebello
    sette_winner = None
    for i, p in enumerate(players):
        if any(c.suit == SETTEBELLO_SUIT and c.rank == SETTEBELLO_RANK
               for c in p.captured):
            scores[i] += 1
            sette_winner = i
            break
    breakdown['settebello'] = {'winner': sette_winner}

    # Primiera
    prims = [compute_primiera(p.captured) for p in players]
    if prims[0] > 0 and prims[0] > prims[1]:
        scores[0] += 1
        prim_winner = 0
    elif prims[1] > 0 and prims[1] > prims[0]:
        scores[1] += 1
        prim_winner = 1
    else:
        prim_winner = None
    breakdown['primiera'] = {'winner': prim_winner, 'values': prims}

    return scores, breakdown
