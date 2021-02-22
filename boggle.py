"""
Alexander Lyttle
05/01/2019
Copyright 2019 Alexander Lyttle

This code is a work in progress.
The code describes a Boggle-like computer game.
"""

import os, time, threading, shutil, sys
from typing import Optional, Sequence, Callable, Union
from random import choice, choices, seed


class LetterFormatter:
    """
    Letter formatter. Formats any given Sequence of letters to appear as if
    they were letters on a Boggle board.

    Parameters
    ----------
    letter_width : int
        The width assigned to each letter. Default is 3, meaning letters can
        be up to 3 characters wide and are padded with whitespace.
    letters_per_row : int
        The number of letters allowed before starting a new line. Default is
        6, corresponding to the length of the word 'Boggle'.
    
    Attributes
    ----------
    sep : str
        Characters separating each letter.
    wrap : str
        Characters wrapping the beginning and end of each line.
    letter_width : int
        The width assigned to each letter. 
    letters_per_row : int
        The number of letters allowed before starting a new line.   
    header : str
        The header string for the formatter.
    row_sep : str
        The string separating each row of letters.
    footer : str
        The footer string for the formatter.

    """
    sep = '|||'
    wrap = '||'

    def __init__(self, letter_width: int=3, letters_per_row:int=6):

        self.letter_width = letter_width
        self.letters_per_row = letters_per_row
        self.header = (' ' + '_' * (len(self.sep)+self.letter_width-1)) * \
            self.letters_per_row + '\n'
        self.row_sep = '\n|' + ('|' + '___' + '||') * self.letters_per_row + \
            '\n'
        self.footer = '|' + ('/' + '___' + '\\|') * self.letters_per_row

    def format(self, letters: Sequence[str]) -> str:
        rows = map(
            lambda row: self.wrap + \
                self.sep.join([f'{r:<{self.letter_width}}' for r in row]) + \
                self.wrap,
            zip(*[iter(letters)] * self.letters_per_row)
        )
        s = self.header + self.row_sep.join(rows) + self.row_sep + \
            self.footer
        return s


class Board:
    """
    Class for the Boggle board.

    Parameters
    ----------
    size : int, optional
        The size, N for an N x N board. Default is 4.
    letters : Sequence of str or str, optional
        Sequence of letters on the board. If letters is not None, size will be
        ignored. The Sequence must have length equal to a square number.
        Default is None.
    p_vow : float, optional
        Probability of a letter on the board being a vowel. Not used if letter
        is not None. Default is 0.38.
    p_con : float, optional
        Probability of a letter on the board being a consonant. Not used if
        letter is not None. Default is 0.62.
    random_seed : optional
        Seed for choosing random letters for the board.

    Attributes
    ----------
    size : int
        Size of the board, N for an N x N board.
    p_vow : float
        Probability of a letter on the board being a vowel.
    p_con : float
        Probability of a letter on the board being a consonant.
    letters : list of str
        List of letters on the board.
    adjacency : dict of list of int
        Adjacency matrix for each index on the board.
    found_words : list of str
        List of all possible words on the board. Empty unless find_words is
        called.

    """

    _vowels = list('AEIOU')
    _consonants = list('BCDFGHJKLMNPQRSTVWXYZ')
    _consonants[_consonants.index('Q')] += 'U'

    def __init__(self, size: Optional[int]=4, 
                 letters: Optional[Sequence[str]]=None, 
                 p_vow: Optional[float]=None, p_con: Optional[float]=None,
                 random_seed=None):
        seed(random_seed)
        
        self.size = size
        self.p_vow = p_vow or 0.38
        self.p_con = p_con or 0.62
        self.letters = self._validate_letters(letters)
        
        if letters is not None:
            size = len(self.letters)**0.5
            if size % 1 != 0:
                raise ValueError('Length of letters is not a square number.')
            self.size = int(size)

        formatter = LetterFormatter(letters_per_row=self.size)
        self._str = formatter.format(self.letters)

        self.adjacency = self._init_adjacency()
        self.found_words = list()
    
    @classmethod
    def vowels(cls):
        return cls._vowels

    @classmethod
    def consonants(cls):
        return cls._consonants

    @classmethod
    def set_vowels(cls, vowels: Sequence[str]):
        cls._vowels = vowels

    @classmethod
    def set_consonants(cls, consonants: Sequence[str]):
        cls._consonants = consonants

    def __str__(self):
        return self._str

    def _validate_letter(self, letter: str):
        """
        Validate a single letter.

        Raises
        ------
        ValueError :
            If a letter is not a vowel or consonant (excluding 'Q' and 
            including 'QU').
        TypeError :
            If the letter is not a string.

        """
        if isinstance(letter, str):
            if letter in self._vowels or letter in self._consonants:
                return letter.upper()
            else:
                msg = f'Character {letter} is not a vowel or consonant.'
                raise ValueError(msg)
        else:
            raise TypeError(f'Letter {letter} is not an instance of str.')

    def _validate_letters(self, letters: Optional[Sequence[str]]=None):
        """
        Validate a Sequence of letters. If letters is None, a list of letters
        will be assigned at random according to p_vow and p_con.

        Parameters
        ----------
        letters : Sequence of str, optional
            Letters to validate. If None (default) then a random list of
            letters will be drawn.

        Returns
        -------
        letters : list of str
            List of letters on the board.

        Raises
        ------
        TypeError :
            If letters is not a Sequence or None.

        """
        if isinstance(letters, Sequence):
            letters = [self._validate_letter(letter) for letter in letters]
        elif letters is None:
            letter_choices = self.choose_letters(k=self.size**2)
            letters = [c() for c in letter_choices]
        else:
            raise TypeError('Variable letters is not a Sequence or None.')
        return letters

    def _init_adjacency(self):
        """
        Initialise the adjacency matrix for the board.

        Returns
        -------
        adjacency : dict of list of int
            The adjacency for each index of the board.

        """
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

        Properties
        ----------
        k : int
            The length of list of chosen letters to return.

        Returns
        -------
        choices : list of Callable
            List of functions which choose from vowels or consonants when
            called.
        """
        return choices([lambda: choice(self._vowels), 
                        lambda: choice(self._consonants)], 
                       weights=[self.p_vow, self.p_con], k=k)

    def find_words(self, words: Sequence[str]):
        """
        Finds all possible words on the board and sets found_words.

        Parameters
        ----------
        words : Sequence of str
            The sequence of valid words.
        
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
    """
    Class for the player.

    Parameters
    ----------
    name : str
        Name of the player. Default is 'Player'. This is not currently used.
    score : int
        The player's initial score. Default is 0.
    found_words : Sequence of str, optional
        Initial list of found words for the player.
    
    Attributes
    ----------
    name : str
        Name of the player.
    score : int
        The player's current score.
    found_words : list of str
        List of words found by the player.
    messsage : str
        Message to display to the player at the beginning of their turn.

    """

    def __init__(self, name: str='Player', score: int=0,
                 found_words: Optional[Sequence[str]]=None):
        self.name = name
        self.score = score
        self.found_words = list(found_words or [])
        self.message = None

    def score_word(self, guess: str, available_words: Sequence[str]):
        """
        Scores a word given a guess and list of available words.
        """
        if guess in available_words and guess not in self.found_words:
            self.score += Boggle.find_score(guess)
            self.found_words.append(guess)
        elif guess in self.found_words:
            self.message = 'You have already entered this word, ' + \
                'please try again!'
        elif guess is not None:
            self.message = 'Invalid word, try again!'

    def reset(self, score: int=0, found_words: Optional[Sequence[str]]=None):
        """
        Resets the score and list of found words for the player.
        """
        self.score = score
        self.found_words = list(found_words or [])


class Boggle:
    """
    Class for the Boggle game. Controls the operation of the game.

    """
    _points: dict = {3: 1, 4: 2, 5: 4, 6: 6, 7: 9, 8: 15}

    _indent: int = 24
    _wordrows: dict = {}  
    # for k, v in _points.items():
    #     plural = 's' if v > 1 else ''
    #     _wordrows[k] = f'{f"{k} letters ({v} point{plural})":<{_indent-2}}: '
    #     del plural
    # _width: int = max(shutil.get_terminal_size()[0], 80)
    # _div: str = _width * '='
    _formatter: LetterFormatter = LetterFormatter()
    _title: str = _formatter.format('Boggle')

    def __init__(self, player: Optional[Player]=None,
                 board: Optional[Board]=None, time_limit: int=120,
                 words_file: str='words.txt'):
        
        for k, v in self._points.items():
            plural = 's' if v > 1 else ''
            self._wordrows[k] = f'{f"{k} letters ({v} point{plural})":<{self._indent-2}}: '
            # del plural       
        self._width = max(shutil.get_terminal_size()[0], 80)
        self._div = self._width * '='

        self.player = player or Player()
        self.board = board or Board()
        self.timer = threading.Timer(time_limit, self.stop)
        self.timer.daemon = True  # Timer thread closes with main thread
        
        words = self.load_words(words_file)
        self.board.find_words(words)

    @classmethod
    def points(cls):
        return cls._points

    @classmethod
    def set_points(cls, points: dict):
        cls._points = points
    
    @classmethod
    def find_score(cls, words: Union[str, Sequence[str]]):
        """
        Calculate score for given word(s).
        """
        if isinstance(words, str):  # If words is just a string, make iterable
            words = {words}
        score = 0
        for w in words:
            score += cls._points[len(w)]
        return score

    @staticmethod
    def load_words(file, min_len: int=3):
        """
        Loads a list of words from a given file.
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
        """
        Clear the screen.
        """
        os.system('cls' if os.name == 'nt' else 'clear')

    def format_words(self, words: Sequence[str], separator: str=', '):
        """
        Formats a list of words neatly.
        """
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
        """
        Displays the board on a blank screen.
        """
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
        """
        Displays the endgame screen and information.
        """
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
        """
        Starts the game.
        """
        self.in_play = True
        self.timer.start()

        guess = None
        while self.in_play:
            self.player.score_word(guess, self.board.found_words)
            self.display()
            guess = input('Enter word: ').upper()
        
        self.endgame()

    def stop(self):
        """
        Calls to stop the game.
        """
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
