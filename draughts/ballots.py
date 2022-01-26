# 11 english, 11 italian, 4 move english and 5 move english ballots are from Ed Gilbert (http://edgilbert.org/Checkers/KingsRow.htm).
import random
import json
import os


class Ballots:
    def __init__(self, variant, moves=3, eleven_pieces=False, basic_positions=False, include_lost_games=False):
        self.variant = variant
        self.moves = moves
        self.eleven_pieces = eleven_pieces
        self.basic_positions = basic_positions
        self.include_lost_games = include_lost_games
        self.filename = self._find_file()
        self.positions, self.keys = self.open_file()
        self.keys_to_use = self.keys.copy()

    def _find_file(self):
        if self.variant == 'italian':
            return '11_italian.json'
        if self.variant == 'english':
            if self.eleven_pieces:
                return '11_english.json'
            if self.moves == 2:
                return '2move_english.json'
            if self.moves == 4:
                return '4move_english.json'
            if self.moves == 5:
                return '5move_english.json'
        if self.basic_positions:
            return '150russian_and_brazilian.json'
        if self.variant == 'russian':
            return 'russian.json'
        if self.variant == 'brazilian':
            return 'brazilian.json'
        return '3move_english.json'

    def open_file(self):
        filepath = os.path.join(os.path.dirname(__file__), 'ballot_files', self.filename)
        with open(filepath) as file:
            data = json.load(file)
        keys = data['standard'] + (data.get('lost', []) if self.include_lost_games else [])
        return data['all'], keys

    def get_ballot(self):
        if not self.keys_to_use:
            self.keys_to_use = self.keys.copy()
        key = self.keys_to_use.pop(random.randint(0, len(self.keys_to_use) - 1))
        return self.positions[key]
