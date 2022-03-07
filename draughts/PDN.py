import re
import string
from functools import reduce
from draughts.convert import move_to_variant, fen_to_variant
from draughts import Game, Move
from typing import List, Optional, Dict, Union


class _PDNGame:
    def __init__(self, pdn_text: str) -> None:
        self._tag_value_to_int = ["WhiteRating", "BlackRating"]
        self.values_to_variant = {20: "standard", 21: "english", 22: "italian", 23: "american pool", 24: "spanish", 25: "russian", 26: "brazilian", 27: "canadian", 28: "portuguese", 29: "czech", 30: "turkish", 31: "thai", 40: "frisian", 41: "spantsiretti"}
        self.tags = {}
        self.moves = []
        self.variant = None
        self.notation = None
        self.notation_type = None
        self.game_ending = '*'
        self.pdn_text = pdn_text
        self._rest_of_games = []
        self._read()

    def _read(self) -> None:
        """Read a PDN game."""
        lines = self.pdn_text
        lines = lines.split('\n')
        tag_lines = []
        last_tag_line = -1
        for index, line in enumerate(lines):
            if line.startswith('['):
                tag_lines.append(line)
                last_tag_line = index
            elif re.sub(r'\s', '', line):
                break

        for tag_line in tag_lines:
            line = tag_line[1:-1]
            quote_index = line.index('"')
            name = line[:quote_index - 1]
            value = line[quote_index + 1:-1]
            if name in self._tag_value_to_int:
                value = int(value)
            self.tags[name] = value

        rest_of_games = []
        last_move_line = -1
        move_lines = []
        for index, line in enumerate(lines[last_tag_line + 1:]):
            splitted_line = re.split(r'\s(1-0|1/2-1/2|0-1|2-0|1-1|0-2|0-0|\*)\s', ' ' + line + ' ', maxsplit=1)
            if len(splitted_line) == 3:
                move_lines.append(splitted_line[0])
                last_move_line = index
                self.game_ending = splitted_line[1]
                rest_of_games.append(splitted_line[2])
                break
            if re.sub(r'\s', '', line):
                move_lines.append(line)
                last_move_line = index

        rest_of_games += lines[last_tag_line + 1 + last_move_line + 1:]

        moves = " ".join(move_lines)

        # Changes to the PDN.

        # From https://stackoverflow.com/a/37538815/10014873
        def remove_text_between_parens(text):
            n = 1  # Run at least once.
            while n:
                text, n = re.subn(r'\([^()]*\)', '', text)  # Remove non-nested/flat balanced parts.
            return text

        def remove_text_between_brackets(text):
            n = 1  # Run at least once.
            while n:
                text, n = re.subn(r'{[^{}]*}', '', text)  # Remove non-nested/flat balanced parts.
            return text

        moves = remove_text_between_parens(moves)
        moves = remove_text_between_brackets(moves)
        moves = re.sub(r" +", " ", moves)
        moves = re.sub(r"\$[0-9]+", "", moves)
        moves = moves.replace('. ...', '...')
        moves = moves.replace('...', '.')
        moves = moves.replace('?', '')
        moves = moves.replace('!', '')
        moves = moves.replace('. ', '.')
        moves = moves.replace('- ', '-')
        moves = moves.replace('x ', 'x')
        moves = moves.replace(': ', ':')

        move_numbers = re.findall(r"\d+\.", moves)
        double_numbers = list(set(filter(lambda move: move_numbers.count(move) >= 2, move_numbers)))
        for move_number in double_numbers:
            moves = moves[:moves.index(move_number) + len(move_number)] + moves[moves.index(move_number) + len(move_number):].replace(move_number, "")

        moves = moves.split(".")[1:]
        if not moves:
            return
        starts = self.tags.get('FEN', 'W')
        if starts.startswith('W'):
            moves = list(reduce(lambda x, y: x + y.split()[:2], moves, []))
        else:
            moves = [moves[0].split()[0]] + list(reduce(lambda x, y: x + y.split()[:2], moves[1:], []))
        results = ["1-0", "1/2-1/2", "0-1", "2-0", "1-1", "0-2", "0-0", "*"]
        moves = moves[:-1] if moves[-1] in results else moves
        self.moves = moves

        if "GameType" in self.tags:
            game_type = self.tags["GameType"]
            values = game_type.split(',')
            variant_number = int(values[0])
            self.variant = self.values_to_variant.get(variant_number, None)
            if len(values) == 6:
                notation = values[4]
                self.notation_type = notation[0].lower()
                self.notation = int(notation[1])
        else:  # Try to guess the variant.
            board_10 = ['31', '32', '33', '34', '35', '16', '17', '18', '19', '20']
            board_8 = ['21', '22', '23', '24', '9', '09', '10', '11', '12']
            first_move = moves[0]
            if list(filter(lambda move: move.startswith(first_move), board_10)):
                self.variant = "standard"
            elif list(filter(lambda move: move.startswith(first_move), board_8)):
                self.variant = "english"
            elif first_move[0] in string.ascii_letters:
                self.variant = "russian"

        self._rest_of_games = rest_of_games

    def get_titles(self) -> List[str]:
        """Get player titles."""
        return [self.tags.get("WhiteTitle", ""), self.tags.get("BlackTitle", "")]

    def get_ratings(self) -> List[str]:
        """Get player ratings."""
        return [self.tags.get("WhiteRating", ""), self.tags.get("BlackRating", "")]

    def get_na(self) -> List[str]:
        """Get player network address."""
        return [self.tags.get("WhiteNA", ""), self.tags.get("BlackNA", "")]

    def get_types(self) -> List[str]:
        """Get player types (human, computer, etc.)."""
        return [self.tags.get("WhiteType", ""), self.tags.get("BlackType", "")]

    def _get_rest_of_games(self) -> str:
        """Get the rest of the games."""
        # This class only reads the first game. You can get the rest with this function.
        return '\n'.join(self._rest_of_games)


class PDNReader:
    def __init__(self, pdn_text: Optional[str] = None, filename: Optional[str] = None, encodings: Union[List[str], str, None] = None) -> None:
        if encodings is None:
            encodings = ['utf8', 'ISO 8859/1']
        if type(encodings) == str:
            encodings = [encodings]
        assert pdn_text or filename
        if not pdn_text:
            pdn_text = ''
            for encoding in encodings:
                try:
                    with open(filename, encoding=encoding) as pdn_file:
                        pdn_text = pdn_file.read()
                    break
                except Exception:
                    pass
        self.pdn_text = pdn_text
        self.pdn_text = re.sub('\n +', '\n', self.pdn_text)
        self.pdn_text = re.sub('\n\n+', '\n\n', self.pdn_text)
        self.games = []
        game = _PDNGame(self.pdn_text)
        self.games.append(game)
        more_games = game._get_rest_of_games()
        while re.sub(r'\s', '', more_games):
            game = _PDNGame(more_games)
            self.games.append(game)
            more_games = game._get_rest_of_games()


class PDNWriter:
    VARIANT_TO_GAMETYPE = {'standard': 20, 'english': 21, 'italian': 22, 'russian': 25, 'brazilian': 26, 'turkish': 30, 'frisian': 40, 'frysk!': 40}
    SHORT_TO_LONG_GAMETYPE = {'20': '20,W,10,10,N2,0', '21': '21,B,8,8,N1,0', '22': '22,W,8,8,N2,1', '25': '25,W,8,8,A0,0', '26': '26,W,8,8,A0,0', '30': '30,W,8,8,A0,0', '40': '40,W,10,10,N2,0'}

    def __init__(self, filename: str, board: Optional[Game] = None, moves: List[Union[str, Move]] = None, variant: Optional[str] = None, starting_fen: Optional[str] = None, tags: Optional[Dict[str, str]] = None, game_ending: str = '*', replay_moves_from_board: bool = True, file_encoding: str = 'utf8', file_mode: str = 'a') -> None:
        """
        :param replay_moves_from_board: The already saved pdn_move in move_stack may be wrong because it is pseudolegal
        and doesn't account for ambiguous moves. If replay_moves_from_board is enabled, it will replay all the moves to
        find the correct representation of them.
        """
        assert board or moves
        self.pdn_text = ''
        self.notation_type = None
        self.notation = None
        self.convert_fen = True

        self.board = board
        if self.board:
            self.moves = self.board.move_stack
            self.variant = self.board.variant
            self.starting_fen = self.board.initial_fen
            self.tags = {}
            self.to_standard_notation = True
        else:
            self.moves = moves
            self.variant = variant or 'standard'
            if starting_fen:
                self.convert_fen = False
            self.starting_fen = starting_fen or self._startpos_to_fen('startpos')
            self.tags = tags or {}
            self.to_standard_notation = False
        self.game_ending = game_ending

        self.replay_moves_from_board = replay_moves_from_board
        self.filename = filename
        self.file_encoding = file_encoding
        self.file_mode = file_mode
        self._fix_ambiguous_moves()
        self._write()

    def _fix_ambiguous_moves(self) -> None:
        """Replay the moves to fix any ambiguous PDN move."""
        if self.moves and type(self.moves[0]) == str:
            return
        game = Game(self.variant, self.starting_fen)
        correct_moves = []
        for move in self.moves:
            correct_move = Move(game, board_move=move.board_move)
            correct_moves.append(correct_move)
            for semi_move in move.board_move:
                game.move(semi_move)
        self.moves = correct_moves

    def _write(self) -> None:
        """Write the PDN file."""
        pdn_text = ''
        if 'GameType' not in self.tags:
            short_gametype = str(self.VARIANT_TO_GAMETYPE.get(self.variant.lower(), 20))
            long_gametype = self.SHORT_TO_LONG_GAMETYPE[short_gametype]
            self.tags['GameType'] = long_gametype
        if 'FEN' not in self.tags:
            if self.convert_fen:
                self.starting_fen = fen_to_variant(self.starting_fen, variant=self.variant)
            self.tags['FEN'] = self.starting_fen
        for tag in self.tags:
            pdn_text += f'[{tag} "{self.tags[tag]}"]\n'
        pdn_text += '\n'

        if self.to_standard_notation:
            game_type = self.SHORT_TO_LONG_GAMETYPE.get(self.tags['GameType'], self.tags['GameType'])
            values = game_type.split(',')
            notation = values[4]
            self.notation_type = notation[0].lower()
            self.notation = int(notation[1])

        standard_moves = []
        for move in self.moves:
            if type(move) != str:
                standard_move = move.pdn_move
            else:
                standard_move = move

            if self.to_standard_notation:
                standard_move = move_to_variant(standard_move, variant=self.variant)

            standard_moves.append(standard_move)

        if not standard_moves:
            pass
        elif len(standard_moves) == 1 and self.starting_fen[0] == 'W':
            pdn_text += f'1. {standard_moves[0]}'
            standard_moves = []
        else:
            if self.starting_fen[0] == 'W':
                pdn_text += f'1. {standard_moves[0]} {standard_moves[1]}'
                standard_moves = standard_moves[2:]
            else:
                pdn_text += f'1... {standard_moves[0]}'
                standard_moves = standard_moves[1:]

        write_move_number = True
        move_number = 2
        while standard_moves:
            move_number_to_write = f'{move_number}. ' if write_move_number else ''
            pdn_text += f' {move_number_to_write}{standard_moves.pop(0)}'
            write_move_number = not write_move_number
            if write_move_number:
                move_number += 1
        pdn_text += f' {self.game_ending}'
        pdn_text += '\n\n'

        self.pdn_text = pdn_text

        if self.filename:
            with open(self.filename, self.file_mode, encoding=self.file_encoding) as file:
                file.write(self.pdn_text)

    def _startpos_to_fen(self, fen: str) -> str:
        """Get the starting fen."""
        if fen != 'startpos':
            return fen
        if self.variant == 'frysk!':
            return 'W:W46,47,48,49,50:B1,2,3,4,5'
        elif self.variant == 'turkish':
            return 'W:W41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56:B9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24'
        elif self.variant in ['brazilian', 'russian', 'italian']:
            return 'W:W21,22,23,24,25,26,27,28,29,30,31,32:B1,2,3,4,5,6,7,8,9,10,11,12'
        elif self.variant == 'english':
            return 'B:W21,22,23,24,25,26,27,28,29,30,31,32:B1,2,3,4,5,6,7,8,9,10,11,12'
        else:
            return 'W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20'
