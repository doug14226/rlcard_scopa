from rlcard.games.scopa.utils import compute_round_scores_detail


class ScopaJudger:
    """Handles end-of-round scoring and payoff calculation for Scopa."""

    @staticmethod
    def judge_payoffs(players):
        """
        Compute payoffs for each player as actual Scopa point totals.

        Returns:
            list[float]: [points_p0, points_p1]
        """
        scores, _ = compute_round_scores_detail(players)
        return [float(s) for s in scores]

    @staticmethod
    def judge_scores_detail(players):
        """
        Compute point scores and per-category breakdown.

        Returns:
            tuple: (scores, breakdown) — see compute_round_scores_detail for structure.
        """
        return compute_round_scores_detail(players)
