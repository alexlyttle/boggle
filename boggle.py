"""
Alexander Lyttle
05/01/2019
Copyright 2019 Alexander Lyttle

This code is a work in progress.
The code describes a Boggle-like computer game.
"""

import os, time, threading, shutil, sys
from typing import Optional, Sequence
from random import choice, choices
from pyfiglet import Figlet


class BoardWidthError(Exception):
    pass


class Board:
    """
    Class for the Boggle board.

    Parameters
    ----------
    size : int, optional
        The size, N for an N x N board. Default is 4.
    letters : Sequence of str or str, optional
        If letters is not None, size will be ignored. The Sequence must have
        length equal to a square number. Default is None.
    p_vow : float, optional
        Probability of a letter on the board being a float. Not used if letter
        is not None. Default is 0.38.
    p_con : float, optional
        Probability of a letter on the board being a float. Not used if letter
        is not None. Default is 0.62.

    Attributes
    ----------
    size : int
    p_vow : float
    p_con : float
    letters : list of str
    adjacency : dict of 
    found_words

    Methods
    -------

    """

    _vowels = list('AEIOU')
    _consonants = list('BCDFGHJKLMNPQRSTVWXYZ')
    _consonants[_consonants.index('Q')] += 'U'

    def __init__(self, size: Optional[int]=4, 
                 letters: Optional[Sequence[str]]=None, 
                 p_vow: Optional[float]=None, p_con: Optional[float]=None):
        self.size = size
        self.p_vow = p_vow or 0.38
        self.p_con = p_con or 0.62
        self.letters = self._validate_letters(letters)
        
        if letters is not None:
            size = len(self.letters)**0.5
            if size % 1 != 0:
                raise ValueError('Length of letters is not a square number.')
            self.size = int(size)

        sep = '|||'
        wrap = '||'
        self._width = self.size * (len(sep) + 3) - len(sep) + 2 * len(wrap)
        rows = map(
            lambda row: wrap + \
                sep.join([f'{r:<3}' for r in row]) + wrap,
            zip(*[iter(self.letters)] * self.size)
        )
        # self._str = ('\n'+'-'*self._width+'\n').join(rows)
        row_head = (' ' + '_' * (len(sep) + 2)) * self.size + '\n'
        row_sep = '\n|' + ('|' + '___' + '||') * self.size + '\n'
        row_foot = '|' + ('/' + '___' + '\\|') * self.size
        self._str = row_head + row_sep.join(rows) + row_sep + row_foot
        self.adjacency = self._init_adjacency()
        self.found_words = list()

        self._check_width()

    def __str__(self):
        return self._str

    def _check_width(self):
        if self._width > Boggle._width:
            raise BoardWidthError('Board width exceeds terminal window width.')

    def _validate_letter(self, letter):
        if isinstance(letter, str):
            if letter in self._vowels or letter in self._consonants:
                return letter.upper()
            else:
                msg = f'Character {letter} is not a vowel or consonant.'
                raise ValueError(msg)
        else:
            raise TypeError(f'Letter {letter} is not an instance of str.')

    def _validate_letters(self, letters):
        if isinstance(letters, Sequence):
            letters = [self._validate_letter(letter) for letter in letters]
        elif letters is None:
            letter_choices = self.choose_letters(k=self.size**2)
            letters = [c() for c in letter_choices]
        else:
            raise TypeError('Variable letters is not a Sequence or None.')
        return letters

    def _init_adjacency(self):
        adjacency = {}
        for i in range(self.size**2):
            x, y = divmod(i, self.size)
            adjacency[i] = adj = []
            if x > 0: 
                # If row is not first, add above element index
                adj.append(i - self.size)
                if y > 0:
                    # If column is not first, add northwest element index
                    adj.append(i - self.size - 1)
                if y < self.size - 1:
                    # If column is not last, add northeast element index
                    adj.append(i - self.size + 1)
            if x < self.size - 1:
                # If row is not last, add below element index
                adj.append(i + self.size)
                if y > 0:
                    # If column is not first, add southwest element index
                    adj.append(i + self.size - 1)
                if y < self.size - 1:
                    # If column is not last, add southeast element index
                    adj.append(i + self.size + 1)
            if y > 0:
                # If column is not first, add left element index
                adj.append(i - 1)
            if y < self.size - 1:
                # If column is not last, add right element index
                adj.append(i + 1)
        return adjacency

    def choose_letters(self, k=1):
        """
        Choose vowel or consonant letter types.
        """
        return choices([lambda: choice(self._vowels), 
                        lambda: choice(self._consonants)], 
                       weights=[self.p_vow, self.p_con], k=k)

    def find_words(self, words):
        """
        Finds all possible words on the board.
        :param tuple words: A 2-tuple containing all words and prefixes
        :return set: Set of found words
        """
        prefixes = {w[:i] for w in words for i in range(1, len(w))}
        
        found = list()

        def _advance_path(prefix, path):
            """
            Advance the path of possible words given the prior prefix and path
            indices.
            """
            if prefix in words:
                # If prefix is in list of words, add to found words
                found.append(prefix)
            if prefix in prefixes:
                # If prefix is in the list of prefixes, advance the path
                for j in self.adjacency[path[-1]]:
                    # For each adjacent letter to the last element in the path
                    if j not in path:
                        # If element is not already in the path, advance path
                        _advance_path(prefix + self.letters[j], path + [j])

        for (i, letter) in enumerate(self.letters):
            # For each letter in the list of board letters, start a path
            sys.stdout.write('\r')
            sys.stdout.write(
                'Finding words on board {:2.0f}%'.format(100*i/self.size**2)
            ) 
            sys.stdout.flush()
            _advance_path(letter, [i])
        self.found_words = found


class Player:

    def __init__(self, name='Player', score=0, found_words=None):
        """
        Initialise the player.
        :param name: Name of the player
        :param score: Optional, player score
        :param found_words: Optional, words found by the player
        """
        self.name = name
        self.score = score
        self.found_words = found_words or list() 
        self.message = None

    def score_word(self, guess, available_words):
        if guess in available_words and guess not in self.found_words:
            self.score += Boggle.find_score(guess)
            self.found_words.append(guess)
        elif guess in self.found_words:
            self.message = 'You have already entered this word, ' + \
                'please try again!'
        elif guess is not None:
            self.message = 'Invalid word, try again!'

    def reset(self, score=0, found_words=None):
        """
        Resets the score and list of found words for the player.
        :param score: Optional, default score
        :param found_words: Optional, initial found words
        :return:
        """
        self.score = score
        self.found_words = found_words or list()


class Boggle:
    _points: dict = {3: 1, 4: 2, 5: 4, 6: 6, 7: 9, 8: 15}

    _indent: int = 24
    _wordrows: dict = {}  
    for k, v in _points.items():
        plural = 's' if v > 1 else ''
        _wordrows[k] = f'{f"{k} letters ({v} point{plural})":<{_indent-2}}: '
        del plural
    _width: int = max(shutil.get_terminal_size()[0], 80)
    # _height: int = shutil.get_terminal_size()[1]
    _div: str = _width * '='
    _figlet: Figlet = Figlet(font='smkeyboard', width=_width)
    _title: str = _figlet.renderText('Boggle')

    def __init__(self, player: Optional[Player]=None,
                 board: Optional[Board]=None, time_limit: int=120,
                 words_file: str='words.txt'):
        """
        Initialise the game.
        :param player: Player
        :param board: Board
        :param time_limit: Optional, time limit in seconds
        """
        self.player = player or Player()
        self.board = board or Board()
        self.timer = threading.Timer(time_limit, self.stop)
        self.timer.daemon = True  # Timer thread closes with main thread
        
        words = self.load_words(words_file)
        self.board.find_words(words)

    @staticmethod
    def load_words(file, min_len=3):
        """
        Loads a dictionary of words from a given file or string and returns all
        words and prefixes.
        :param file: File location or string for words
        :param int min_len: Optional minimum length of words
        :return tuple: A 2-tuple of words and prefixes
        """
        def load(f):
            for line in f:
                # Strip off whitespace at end of line and capitalize
                word = line.rstrip().upper()
                if len(word) >= min_len:
                    # If word length is at least the minimum,
                    # yield word in iteration
                    yield word

        if isinstance(file, str):
            with open(file) as f:
                words = list(load(f))
        else:
            words = list(load(file))
        # Finds set of prefixes for each word
        return words

    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    @classmethod
    def find_score(cls, words):
        """
        Calculate score for given word(s).
        :param words: String (or set) of the word (or words) to score
        :param points: Optional points assignment to word lengths
        :return: Score for the given word(s)
        """
        if isinstance(words, str):  # If words is just a string, make iterable
            words = {words}
        score = 0
        for w in words:
            score += cls._points[len(w)]
        return score

    def format_words(self, words, separator=', '):
        available = self._width - self._indent
        rows = {k: [] for k in self._points.keys()}
        words.sort()  # sort alphabetically
        for word in words:
            rows[len(word)].append(word)

        blocks = []
        for key, value in rows.items():
            if len(value) == 0:
                continue
            s = f'{self._wordrows[key]:<{self._indent}}'

            words_per_line = available//(key+len(separator))
            total_lines = len(value)//words_per_line + 1

            indices = [i*words_per_line for i in range(total_lines)]
            lines = [separator.join(value[i:j]) for i, j in \
                zip(indices, indices[1:]+[None])]
            
            s += (separator+'\n'+' '*self._indent).join(lines)
            blocks.append(s)
        return '\n'.join(blocks)

    def display(self):
        self.clear_screen()
        print(self._title)
        print('Score: {0}'.format(self.player.score))
        print(self._div)
        print(self.board)
        print(self._div)
        print('Words found:')
        print(self.format_words(self.player.found_words))
        print(self._div)
        if self.player.message:
            print(self.player.message)
            print(self._div)
            self.player.message = None

    def endgame(self):
        self.clear_screen()
        print(self._title)
        total_score = self.find_score(self.board.found_words)
        final_score = 100 * self.player.score/total_score
        print((
            'Your final score was {0:.0f}%!\n' +
            'You scored {1} out of {2} possible points on this board.'
            ).format(final_score, self.player.score, total_score))
        print(self._div)
        print('You found the following words:')
        print(self.format_words(self.player.found_words))
        print(self._div)
        print('You missed the following words:')
        missed_words = list(
            set(self.board.found_words).difference(
                set(self.player.found_words)
            )
        )
        print(self.format_words(missed_words))

    def start(self):
        self.in_play = True
        self.timer.start()

        guess = None
        while self.in_play:
            self.player.score_word(guess, self.board.found_words)
            self.display()
            guess = input('Enter word: ').upper()
        
        self.endgame()

    def stop(self):
        self.in_play = False
        print('\nGame over! Press ENTER to see your score.')
  

def main():
    Boggle.clear_screen()
    print(Boggle._title)

    name = input('Please enter your name: ')
    player = Player(name)
    
    size = int(input('Please enter the size of the Boggle board: '))
    board = Board(size=size)
    
    time_limit = int(input('Enter the time limit in seconds: '))

    game = Boggle(player=player, board=board, time_limit=time_limit)
    game.start()

if __name__ == '__main__':
    main()
