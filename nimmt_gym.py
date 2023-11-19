import numpy as np
import random

import gymnasium as gym
from gymnasium import spaces

INVALID_MOVE = -100


class InvalidCardException(Exception):
    pass


class NimmtEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, render_mode=None, players=4):
        self.players_count = players
        self._num_rows = 4
        self._max_row = 5
        self.cards_in_game = 10 * players + self._num_rows + 1
        self.cards_space = self.cards_in_game

        # Observations are dictionaries with the agent's and the target's location.
        # Each location is encoded as an element of {0, ..., `size`}^2, i.e. MultiDiscrete([size, size]).
        table_size = self._num_rows * self._max_row
        players_size = 10
        self.observation_space = spaces.Dict(
            {
                "players": spaces.Box(
                    low=-1.0, high=1.0, shape=(players_size,), dtype=np.float64
                ),
                "table": spaces.Box(
                    low=-1.0,
                    high=1.0,
                    shape=(table_size,),
                    dtype=np.float64,
                ),
                "cards_left": spaces.Discrete(11),
            }
        )

        self.action_space = spaces.Discrete(10)

        self.render_mode = render_mode

    def _get_obs(self):
        normalized_empty = self._normalize(self.cards_in_game)
        return {
            "players": np.array(
                [self._normalize(player_elem) for player_elem in self.players[0]]
                + [normalized_empty] * (10 - len(self.players[0]))
            ).flatten(),
            "table": np.array(
                [
                    [self._normalize(table_elem) for table_elem in x]
                    + [normalized_empty] * (self._max_row - len(x))
                    for x in self.table
                ]
            ).flatten(),
            "cards_left": len(self.players[0]),
        }  # cards left in the game

    def _get_info(self):
        return {
            "player_scores": self.players_scores,
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.deck = list(range(1, self.cards_in_game))
        self.table = []
        self.np_random.shuffle(self.deck)
        self.players = []
        self.players_scores = []

        for _ in range(self._num_rows):
            self.table.append([self.deck.pop()])

        for _ in range(self.players_count):
            self.players_scores.append(0)
            self.players.append([])
            for _ in range(10):
                self.players[-1].append(self.deck.pop())
            self.players[-1] = sorted(self.players[-1])

        assert len(self.players[0]) == 10
        assert len(self.deck) == 0

        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def _play(self, player, card, row_number):
        self.players[player].remove(card)
        if len(self.table[row_number]) == 5 or card < self.table[row_number][-1]:
            self.players_scores[player] += sum(
                [self._card_value(x) for x in self.table[row_number]]
            )
            self.table[row_number] = [card]
        else:
            self.table[row_number].append(card)

    def _smallest_row(self):
        smallest = 1000
        idx = 0
        for idx, row in enumerate(self.table):
            tmp = sum([self._card_value(x) for x in row])
            if tmp < smallest:
                smallest = tmp

        return idx

    @staticmethod
    def _card_value(card):
        assert 0 < card <= 104

        if card == 55:
            return 7
        elif card % 11 == 0:
            return 5
        elif card % 10 == 0:
            return 3
        elif card % 10 == 5:
            return 2
        else:
            return 1

    def _denormalize(self, card):
        return int((card + 1) * (self.cards_in_game - 1) / 2 + 1)

    def _denormalize_hand(self, card):
        return int((card + 1) * (10 - 1) / 2 + 1)

    def _normalize(self, card):
        return (card - 1 - (self.cards_in_game - 1) / 2) / (self.cards_in_game - 1) / 2

    def step(self, action):
        if action >= len(self.players[0]):
            # raise InvalidCardException("Cant play that")
            return self._get_obs(), INVALID_MOVE, False, False, self._get_info()
        actions = [self.players[0][action]]

        for player in range(1, self.players_count):
            actions.append(
                self.players[player][random.randint(0, len(self.players[0]) - 1)]
            )

        actions_to_be_played = sorted(list(enumerate(actions)), key=lambda x: x[0])
        for player, card in actions_to_be_played:
            sorted_table = sorted(enumerate(self.table), key=lambda x: x[1][-1])
            for row_number, row in sorted_table:
                # Card is higher than some row
                if card > row[-1]:
                    self._play(player, card, row_number)
                    break
            # No row to put the card into, need to take smallest row instead
            # TODO: this should be another step in this case where agent decides which row to take, lets KISS for now
            else:
                self._play(player, card, self._smallest_row())

        terminated = len(self.players[0]) == 0
        reward = -self.players_scores[0] if terminated else 0
        observation = self._get_obs()
        info = self._get_info()

        return observation, reward, terminated, False, info
