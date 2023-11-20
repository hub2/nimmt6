import random
from typing import Set, List, Dict


def get_score(card_number):
    if card_number == 55:
        return 7
    if card_number % 11 == 0:
        return 5
    elif card_number % 10 == 0:
        return 3
    elif card_number % 10 == 5:
        return 2
    else:
        return 1


class Board:
    """6nimmt game rules in a nutshell:
    - X players, 2 <= X.
    - 10*X + 4 cards numbered sequentially.
    - Cards lay on four lanes on the board (initially lanes have one card).
    - Each round every player choses and plays a card.
    - Played cards are added to lanes (lowest to highest).
    - Card of value C is added to tha lane ending with highest V s.t. V < C.
    - If card is added to a lane as 6th, card owner gets negative points
      and the lane is cleared.
    """

    def __init__(self, lanes: List[int]) -> None:
        # lanes are represented as four lists
        self.lanes = [[l] for l in lanes]

    def update(self, cards: Dict["Player", int]):
        """Returns penalties"""
        for player, card in sorted(cards.items(), key=lambda x: x[1]):
            best_lane = None
            best_lane_idx = 0
            for idx, lane in enumerate(self.lanes):
                if lane[-1] < card:
                    if best_lane is None:
                        best_lane = lane
                        best_lane_idx = idx
                    elif lane[-1] > best_lane[-1]:
                        best_lane = lane
                        best_lane_idx = idx
            if best_lane is None:
                take = player.pick_lane()
                player.penalty += sum(
                    [get_score(lane_card) for lane_card in self.lanes[take]]
                )
                self.lanes[take] = [card]
            else:
                if len(best_lane) == 5:
                    player.penalty += sum(
                        [
                            get_score(lane_card)
                            for lane_card in self.lanes[best_lane_idx]
                        ]
                    )
                    self.lanes[best_lane_idx] = [card]
                else:
                    best_lane.append(card)

    def print(self):
        print("===")
        for lane in self.lanes:
            print(" ".join(str(i) for i in lane))


class AI:
    def __init__(self, name):
        self.name = name

    def pick_lane(self, board: Board, seen: Set[int]) -> int:
        # Generic dumb "pick lane with the smallest penalty" strategy
        lane_scores = [
            (i, sum([get_score(x) for x in lane])) for i, lane in enumerate(board.lanes)
        ]
        return sorted(lane_scores)[0][0]


class RandomAI(AI):
    """Not very smarts. Not even street-smarts."""

    def play(self, board: Board, hand: List[int], seen: Set[int]) -> int:
        return random.choice(hand)


class SmallestFirstAI(AI):
    """Always pick the smallest card on hand"""

    def play(self, board: Board, hand: List[int], seen: Set[int]) -> int:
        return sorted(hand)[0]


class LargestFirstAI(AI):
    """Always pick the smallest card on hand"""

    def play(self, board: Board, hand: List[int], seen: Set[int]) -> int:
        return sorted(hand)[-1]


class StreetSmartAI(AI):
    """Always pick the smartest card on hand"""

    def play(self, board: Board, hand: List[int], seen: Set[int]) -> int:
        blacklist = []
        for lane in board.lanes:
            if len(lane) == 5:
                last = lane[-1]
                for i in range(last + 1, 45):
                    if i in hand:
                        blacklist.append(i)
                    elif i not in seen:
                        break
            if len(lane) == 4:
                last = lane[-1]
                for i in range(last + 2, 45):
                    if i in hand:
                        blacklist.append(i)
                    elif i not in seen:
                        break

        max_lanes = sorted([x[-1] for x in board.lanes])
        between = []
        for idx, step in enumerate(max_lanes):
            if idx == 0:
                continue
            between.append((max_lanes[idx - 1], max_lanes[idx]))
        for start, stop in between:
            for i in range(start, stop):
                if i in hand and i not in blacklist:
                    return i

        for i in range(len(hand) // 3, 2 * len(hand) // 3):
            if hand[i] not in blacklist:
                return hand[i]

        return sorted(hand)[0]


class Player:
    def __init__(self, ai, board: Board, hand: List[int]) -> None:
        self.board = board
        self.ai = ai
        self.hand = hand
        self.penalty = 0
        self.seen = set()

    def pop(self) -> int:
        card = self.ai.play(self.board, self.hand, self.seen)
        self.hand.remove(card)
        return card

    def see(self, cards: List[int]) -> None:
        self.seen |= set(cards)

    def pick_lane(self):
        # TODO AI
        return self.ai.pick_lane(self.board, self.seen)


def play(ais):
    cards = list(range(1, 10 * len(ais) + 4 + 1))
    random.shuffle(cards)

    board = Board(cards[-4:])
    players = [
        Player(ai, board, cards[i * 10 : (i + 1) * 10]) for i, ai in enumerate(ais)
    ]

    for p in players:
        p.see([lane[0] for lane in board.lanes])

    for turn in range(10):
        choices = {p: p.pop() for p in players}
        for p in players:
            p.see(list(choices.values()))
        board.update(choices)
        # board.print()
    return {p.ai: p.penalty for p in players}


def main():
    players = [
        # RandomAI("random"),
        # RandomAI("random2"),
        RandomAI("random3"),
        RandomAI("random4"),
        SmallestFirstAI("smol1"),
        SmallestFirstAI("smol2"),
        SmallestFirstAI("smol3"),
        StreetSmartAI("street"),
        # LargestFirstAI("lorge"),
    ]
    scores = {p.name: 0 for p in players}
    for i in range(1000):
        penalties = play(players)
        for ai, penalty in penalties.items():
            scores[ai.name] += penalty
        print(scores)


if __name__ == "__main__":
    main()
