from draughts.engine import HubEngine, DXPEngine, CheckerBoardEngine, Limit
from draughts import Board, WHITE, BLACK
from draughts.PDN import PDNWriter
from typing import List, Tuple, Dict, Any, Union
import datetime
import itertools
import time
import logging

logger = logging.getLogger("pydraughts")


class RoundRobin:
    def __init__(self, filename: str, players: List[Tuple[Union[str, List[str]], str, Dict[str, Any]]],
                 start_time: Union[int, float], increment: Union[int, float] = 0, variant: str = "standard",
                 games_per_pair: int = 2, starting_fen: str = "startpos", max_moves: int = 300) -> None:
        self.filename = filename
        self.players = players
        self.start_time = start_time
        self.increment = increment
        self.variant = variant
        self.games_per_pair = games_per_pair
        self.starting_fen = starting_fen
        self.max_moves = max_moves
        self.player_count = len(self.players)
        self.int_players = list(range(self.player_count))
        self.results = [[0, 0, 0] for _ in range(self.player_count)]
        self.scores = [0] * self.player_count
        self.complete_results: List[List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]] = []
        self.pairs: List[Tuple[int, int]] = list(itertools.combinations(self.int_players, 2))
        logger.debug(f"There are {len(self.pairs)} possible pairs.")
        self.complete_pairs: List[List[Tuple[int, int]]] = []
        self.get_complete_pairs()
        logger.debug(f"There will be {len(self.complete_pairs)} games.")
        date = datetime.datetime.now()
        year = str(date.year).zfill(4)
        month = str(date.month).zfill(2)
        day = str(date.day).zfill(2)
        self.tags = {"Event": "Tournament", "Site": "pydraughts", "EventDate": f"{year}.{month}.{day}",
                     "ResultType": "International", "WhiteType": "program", "BlackType": "program", "GameType": "20",
                     "TimeControl": f"{self.start_time}+{self.increment}"}
        if self.starting_fen != "startpos":
            self.tags["FEN"] = self.starting_fen
        self.round = 0

        self.latest_round_results: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = []
        self.latest_complete_results: List[List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]] = []

    def get_complete_pairs(self) -> None:
        pairs = self.pairs.copy()
        for match in range(self.games_per_pair):
            self.complete_pairs.append(pairs.copy())
            pairs = list(map(lambda _pair: (_pair[1], _pair[0]), pairs))

    def get_engine(self, command: Union[str, List[str]], protocol: str, options: Dict[str, Any]
                   ) -> Union[HubEngine, DXPEngine, CheckerBoardEngine]:
        engine: Union[HubEngine, DXPEngine, CheckerBoardEngine]
        if protocol.lower() == "hub":
            engine = HubEngine(command)
            engine.configure(options)
        elif protocol.lower() == "dxp":
            options["initial-time"] = self.start_time
            options["max-moves"] = self.max_moves
            engine = DXPEngine(command, options)
        elif protocol.lower() == "cb" or protocol.lower() == "checkerboard":
            engine = CheckerBoardEngine(command)
            engine.configure(options)
        else:
            raise ValueError(f"There is no protocol `{protocol}`.")
        return engine

    def play(self) -> List[int]:
        while self.round < self.games_per_pair:
            logger.debug(f"Playing round {self.round + 1}/{self.games_per_pair}")
            self.play_round()
            self.round += 1
        for player in range(self.player_count):
            self.scores[player] = self.results[player][0] * 2 + self.results[player][1]
        return self.scores

    def play_round(self) -> None:
        round_results = []
        for game_number, match in enumerate(self.complete_pairs[self.round]):
            logger.debug(f"Playing game {game_number+1}/{len(self.complete_pairs[self.round])} in {self.round+1}th round.")
            result1, result2 = self.play_game(self.players[match[0]], self.players[match[1]], game_number+1)
            round_results.append((result1, result2))
            # Player 1
            self.results[match[0]][0] += result1[0]
            self.results[match[0]][1] += result1[1]
            self.results[match[0]][2] += result1[2]

            # Player 2
            self.results[match[1]][0] += result2[0]
            self.results[match[1]][1] += result2[1]
            self.results[match[1]][2] += result2[2]
            self.latest_round_results = round_results.copy()
            logger.debug(f"Round results until now: {self.latest_round_results}")
        self.complete_results.append(round_results)
        self.latest_complete_results = self.complete_results.copy()
        logger.debug(f"Complete results until now: {self.latest_complete_results}")

    def play_game(self, player_1_info: Tuple[Union[str, List[str]], str, Dict[str, Any]],
                  player_2_info: Tuple[Union[str, List[str]], str, Dict[str, Any]], game_number: int
                  ) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        logger.debug(f"Player 1: '{player_1_info[0]}', Player 2: '{player_2_info[0]}'")
        board = Board(self.variant, self.starting_fen)
        player_1 = self.get_engine(*player_1_info)
        player_2 = self.get_engine(*player_2_info)
        if isinstance(player_1, HubEngine):
            player_1.init()
        if isinstance(player_2, HubEngine):
            player_2.init()
        player_1_limit = Limit(self.start_time, self.increment)
        player_2_limit = Limit(self.start_time, self.increment)
        max_moves = self.max_moves
        if max_moves == 0:
            max_moves = 10000
        while not board.is_over() and len(board.move_stack) < max_moves:
            logger.info(f'move: {len(board.move_stack)}')
            if board.turn == WHITE:
                start = time.perf_counter_ns()
                if isinstance(player_1, HubEngine):
                    best_move = player_1.play(board, player_1_limit, False)
                elif isinstance(player_1, DXPEngine):
                    best_move = player_1.play(board)
                else:  # Checkerboard
                    best_move = player_1.play(board, player_1_limit)
                end = time.perf_counter_ns()
                player_1_limit.time = player_1_limit.time - (end - start) / 1e9 + player_1_limit.inc
            else:
                start = time.perf_counter_ns()
                if isinstance(player_2, HubEngine):
                    best_move = player_2.play(board, player_2_limit, False)
                elif isinstance(player_2, DXPEngine):
                    best_move = player_2.play(board)
                else:  # Checkerboard
                    best_move = player_2.play(board, player_2_limit)
                end = time.perf_counter_ns()
                player_2_limit.time = player_2_limit.time - (end - start) / 1e9 + player_2_limit.inc
            if best_move.move:
                board.push(best_move.move)
            else:
                break
        if not isinstance(player_1, CheckerBoardEngine):
            player_1.quit()
        if not isinstance(player_2, CheckerBoardEngine):
            player_2.quit()
        player_1.kill_process()
        player_2.kill_process()
        winner = board.winner()
        game_ending = "1-1"
        if winner == WHITE:
            game_ending = "2-0"
        elif winner == BLACK:
            game_ending = "0-2"

        # Write PDN
        tags = self.tags.copy()
        tags["Result"] = game_ending
        tags["Round"] = f"{self.round + 1}.{game_number}"
        tags["White"] = str(player_1_info[0])
        tags["Black"] = str(player_2_info[0])
        tags["PlyCount"] = str(len(board.move_stack))
        date_tag, time_tag, utc_date_tag, utc_time_tag = self._get_date_tags()
        tags["Date"] = date_tag
        tags["Time"] = time_tag
        tags["UTCDate"] = utc_date_tag
        tags["UTCTime"] = utc_time_tag
        PDNWriter(self.filename, board, tags=tags, game_ending=game_ending)

        # Return result
        if winner == WHITE:  # Player 1 won
            logger.debug("Player 1 won")
            return (1, 0, 0), (0, 0, 1)
        elif winner == BLACK:  # player 2 won
            logger.debug("Player 2 won")
            return (0, 0, 1), (1, 0, 0)
        else:  # Draw
            logger.debug("Game ended in a draw.")
            return (0, 1, 0), (0, 1, 0)

    def _get_date_tags(self) -> Tuple[str, str, str, str]:
        date = datetime.datetime.now()
        year = str(date.year).zfill(4)
        month = str(date.month).zfill(2)
        day = str(date.day).zfill(2)
        hour = str(date.hour).zfill(2)
        minute = str(date.minute).zfill(2)
        second = str(date.second).zfill(2)
        date_tag = f"{year}.{month}.{day}"
        time_tag = f"{hour}:{minute}:{second}"
        date = datetime.datetime.utcnow()
        year = str(date.year).zfill(4)
        month = str(date.month).zfill(2)
        day = str(date.day).zfill(2)
        hour = str(date.hour).zfill(2)
        minute = str(date.minute).zfill(2)
        second = str(date.second).zfill(2)
        utc_date_tag = f"{year}.{month}.{day}"
        utc_time_tag = f"{hour}:{minute}:{second}"
        return date_tag, time_tag, utc_date_tag, utc_time_tag

    def get_standings(self) -> List[Tuple[int, int]]:
        standings = list(zip(self.scores, self.int_players))
        standings.sort(reverse=True)
        return standings

    def print_standings(self) -> None:
        standings = self.get_standings()
        for place, engine in enumerate(standings):
            logger.debug(f"{place + 1}th place: {self.players[engine[1]][0]} with {engine[0]} points.")
            print(f"{place+1}th place: {self.players[engine[1]][0]} with {engine[0]} points.")
