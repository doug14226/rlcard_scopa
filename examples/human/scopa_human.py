"""
Play Scopa against a random agent (multi-deal match).

Usage:
    python examples/human/scopa_human.py [--target-score N] [--first-player 0|1]
"""

import argparse

import rlcard
from rlcard.agents import RandomAgent
from rlcard.agents import ScopaHumanAgent as HumanAgent


def _winner_label(winner, tie_msg='Tie — no point'):
    if winner == 0:
        return 'You (+1)'
    if winner == 1:
        return 'Opponent (+1)'
    return tie_msg


def _print_deal_result(scores, breakdown):
    """Print a detailed breakdown of points won in the completed deal."""
    print('\n---------- Deal Score Breakdown ----------')

    # Scope
    s = breakdown['scope']['counts']
    print(f'  Scope:      You {s[0]}  Opponent {s[1]}'
          + (f'  → You +{s[0]}' if s[0] else '')
          + (f'  → Opponent +{s[1]}' if s[1] else ''))

    # Carte
    c = breakdown['carte']
    cc = c['counts']
    print(f'  Carte:      You {cc[0]} cards  Opponent {cc[1]} cards'
          f'  → {_winner_label(c["winner"])}')

    # Denari
    d = breakdown['denari']
    dc = d['counts']
    print(f'  Denari:     You {dc[0]}  Opponent {dc[1]}'
          f'  → {_winner_label(d["winner"])}')

    # Settebello
    se = breakdown['settebello']
    print(f'  Settebello: → {_winner_label(se["winner"], "Not yet captured")}')

    # Primiera
    pr = breakdown['primiera']
    pv = pr['values']
    prim_detail = ''
    if pv[0] > 0 or pv[1] > 0:
        prim_detail = f' (You {pv[0]}  Opponent {pv[1]})'
    print(f'  Primiera:  {prim_detail} → {_winner_label(pr["winner"])}')

    print(f'  {"─" * 36}')
    print(f'  Deal total: You {scores[0]}  Opponent {scores[1]}')


def _play_match(env, target_score, first_to_play):
    """Play a full multi-deal match and return cumulative scores."""
    cumulative = [0, 0]
    deal_num = 0

    print(f'\n  Target score: {target_score}')
    labels = ['You (Player 0)', 'Opponent (Player 1)']

    while max(cumulative) < target_score:
        deal_num += 1
        print(f'\n>> Deal {deal_num} — first to play: {labels[first_to_play]}')
        print()

        env.game.first_player = first_to_play
        env.run(is_training=False)

        scores, breakdown = env.game.judger.judge_scores_detail(env.game.players)

        _print_deal_result(scores, breakdown)

        cumulative[0] += scores[0]
        cumulative[1] += scores[1]
        print(f'  Running total: You {cumulative[0]}  Opponent {cumulative[1]}'
              f'  (target {target_score})')

        first_to_play = 1 - first_to_play

    return cumulative


def main():
    parser = argparse.ArgumentParser(description='Play Scopa: Human vs Random Agent')
    parser.add_argument('--target-score', type=int, default=15,
                        help='Points needed to win the match (default: 15)')
    parser.add_argument('--first-player', type=int, default=0, choices=[0, 1],
                        help='Player who plays first in the opening deal (default: 0)')
    args = parser.parse_args()

    env = rlcard.make('scopa')
    human_agent = HumanAgent(env.num_actions)
    random_agent = RandomAgent(num_actions=env.num_actions)
    env.set_agents([human_agent, random_agent])

    print('=== Scopa: Human vs Random Agent ===')
    print('Suits: D=Denari  C=Coppe  S=Spade  B=Bastoni')
    print('Ranks: 1 2 3 4 5 6 7 J Q K  (J/Q/K = Fante/Cavallo/Re, value 8/9/10)')

    while True:
        cumulative = _play_match(env, args.target_score, args.first_player)

        print('\n============= Match Over =============')
        if cumulative[0] > cumulative[1]:
            print(f'YOU WIN!  ({cumulative[0]} - {cumulative[1]})')
        elif cumulative[1] > cumulative[0]:
            print(f'OPPONENT WINS  ({cumulative[1]} - {cumulative[0]})')
        else:
            print(f'TIE  ({cumulative[0]} - {cumulative[1]})')

        again = input('\nPlay again? [y/n]: ').strip().lower()
        if again != 'y':
            print('Thanks for playing!')
            break


if __name__ == '__main__':
    main()
