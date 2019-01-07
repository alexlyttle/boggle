"""
Alexander Lyttle
05/01/2019
Copyright 2019 Alexander Lyttle

This code is a work in progress.
The code describes a Boggle-like computer game.
"""

import time
from random import choice
from numpy import random
from threading import Thread

_VOWELS = list('AEIOU')
_CONSONANTS = list('BCDFGHJKLMNPQRSTVWXYZ')
_POINTS = {3: 1, 4: 2, 5: 4, 6: 6, 7: 9, 8: 15}


class Timer:
    def __init__(self, time_limit, player):
        self.time_limit = time_limit
        self.player = player
        # Run the timer in the background
        thread = Thread(target=self.timer)
        thread.daemon = True  # Allows the program to be exited, stopping this thread also
        thread.start()

    def timer(self):
        print('You have {0} seconds to complete the round.\n'.format(self.time_limit))
        for i in range(self.time_limit):
            # print('Time: {0}\r'.format(i), end='')  # This does not work
            time.sleep(1)
        print('Out of time!')
        self.player.stop()
        # Here need to write code to exit main game loop when this is achieved


def load_dictionary(file, min_len=3):
    """
    Loads a dictionary of words from a given file or string and returns all words and prefixes.
    :param file: File location or string for dictionary
    :param int min_len: Optional minimum length of words
    :return tuple: A 2-tuple of words and prefixes
    """
    def load(f):
        for line in f:
            # Strip off whitespace at end of line and capitalize
            word = line.rstrip().upper()
            if len(word) >= min_len:
                # If the word length is at least the minimum, yield word in iteration
                yield word

    if isinstance(file, str):
        with open(file) as f:
            words = set(load(f))
    else:
        words = set(load(file))
    # Finds set of prefixes for each word
    prefixes = {w[:i] for w in words for i in range(1, len(w))}
    return words, prefixes


def random_letter(p_vow, p_con):
    """
    Return a random letter for a given distribution of vowels and consonants.
    :param float p_vow: Probability of returning a vowel
    :param float p_con: Probability of returning a consonant
    :return string: Random letter
    """
    return random.choice((choice(_VOWELS), choice(_CONSONANTS)), p=(p_vow, p_con))


def find_score(words, points=None):
    """
    Calculate score for given word(s).
    :param words: String (or set) of the word (or words) to score
    :param points: Optional points assignment to word lengths
    :return: Score for the given word(s)
    """
    if points is None:
        points = _POINTS
    if isinstance(words, str):  # If words is just a string, make iterable
        words = {words}
    score = 0
    for w in words:
        score += points[len(w)]
    return score


class Player:

    def __init__(self, name, score=0, found_words=None):
        """
        Initialise the player.
        :param name: Name of the player
        :param score: Optional, player score
        :param found_words: Optional, words found by the player
        """
        self.name = name
        self.score = score
        if found_words is None:
            found_words = set()
        self.found_words = found_words
        self.in_play = False

    def guess_word(self, words):
        """
        Asks the player to guess a word and checks if it is in a set of words.
        :param set words: Set of allowed words
        :return:
        """
        # while self.in_play is True:
        guess = input('Enter word:\n').upper()
        # if self.in_play is False:
        # break
        if guess in words and guess not in self.found_words:
            self.score += find_score(guess)
            self.found_words.add(guess)
        elif guess in self.found_words:
            print('You have already entered this word, please try again!')
        else:
            print('Invalid word, try again!')

    def reset(self, score=0, found_words=None):
        """
        Resets the score and list of found words for the player.
        :param score: Optional, default score
        :param found_words: Optional, initial found words
        :return:
        """
        self.score = score
        if found_words is None:
            found_words = set()
        self.found_words = found_words

    def go(self, board, words):
        self.in_play = True
        seconds = 0
        # thread = Thread(target=self.guess_word, args=(words,))
        # thread.daemon = True
        # thread.start()
        while self.in_play is True:
            # print('Time: {0}'.format(seconds))
            print(board)
            print('Score: {0}'.format(self.score))
            print('Words found:')
            print(self.found_words)  # Make this cleaner looking / more efficient
            self.guess_word(words)  # May do this another way
            # time.sleep(1)
            # seconds += 1

    def stop(self):
        self.in_play = False


class Boggle:

    def __init__(self, size=4, letters=None, p_vow=0.3, p_con=0.7):
        """
        Initialise a Boggle board.
        :param int size: Size, N, for an N x N board
        :param letters: Optional list of letters to fill the board
        :param float p_vow: Probability of there being a vowel on the board
        :param float p_con: Probability of there being a consonant on the board
        """
        self.size = size
        self.letters = [random_letter(p_vow, p_con) for _ in range(size*size)] if not letters else letters.upper()

        if size*size != len(self.letters):
            raise ValueError('Boggle board is not square: Please check letters is equal to the size squared.')

        # Find the adjacent tiles for each letter on the board:
        self.adjacency = {}
        for i in range(size*size):
            x, y = divmod(i, size)
            self.adjacency[i] = adj = []
            if x > 0:  # If row is not first, add above element index
                adj.append(i - size)
                if y > 0:  # If column is not first, add northwest element index
                    adj.append(i - size - 1)
                if y < size - 1:  # If column is not last, add northeast element index
                    adj.append(i - size + 1)
            if x < size - 1:  # If row is not last, add below element index
                adj.append(i + size)
                if y > 0:  # If column is not first, add southwest element index
                    adj.append(i + size - 1)
                if y < size - 1:  # If column is not last, add southeast element index
                    adj.append(i + size + 1)
            if y > 0:  # If column is not first, add left element index
                adj.append(i - 1)
            if y < size - 1:  # If column is not last, add right element index
                adj.append(i + 1)

    def __str__(self):
        return '\n'.join(map(' '.join, zip(*[iter(self.letters)] * self.size)))

    def find_words(self, dictionary):
        """
        Finds all possible words on the board.
        :param tuple dictionary: A 2-tuple containing all words and prefixes
        :return set: Set of found words
        """
        words, prefixes = dictionary
        found = set()

        def advance_path(prefix, path):
            """ Advance the path of possible words given the prior prefix and path indices. """
            if prefix in words:  # If the prefix is in list of words, add to found words
                found.add(prefix)
            if prefix in prefixes:  # If the prefix is in the list of prefixes, advance the path
                for j in self.adjacency[path[-1]]:
                    # For each adjacent letter to the last element in the path
                    if j not in path:  # If the element is not already in the path, advance path
                        advance_path(prefix + self.letters[j], path + [j])

        for (i, letter) in enumerate(self.letters):
            # For each letter in the list of board letters, start a path
            advance_path(letter, [i])
        return found


if __name__ == '__main__':
    # run = True  # For eventual game loop, give option for player to try again
    player = Player(input('Please enter your name:\n'))
    board = Boggle(size=int(input('Please enter the size of the Boggle board.\n')))
    dictionary = load_dictionary('dictionary.txt')
    words = board.find_words(dictionary)  # Finds all possible words on the board
    Timer(int(input('Enter the time limit in seconds:\n')), player)
    player.go(board, words)
    # Issue: when time is up, player does not exit loop in player.go() until after entered word!

    # player.in_play = True
    # while player.in_play is True:
    #     # When pl
    #     print(board)
    #     print('Score: {0}'.format(player.score))
    #     print('Words found:')
    #     print(player.found_words)  # Make this cleaner looking
    #     player.guess_word(words)
    #     # elapsed_time = time.time() - start_time
    print('Out of time!')
    print('You found the following words:')
    print(player.found_words)
    print('You missed the following words:')
    print(words.difference(player.found_words))
    # print('Would you like to play again?')
    # replay = input('Y/n')
    # # Need to change this!
    # run = False if replay is 'n' or 'N' else True
    total_score = find_score(words)
    final_score = 100 * player.score/total_score
    print(('\nYour final score was {0:.0f}%!\n' +
          'You scored {1} out of {2} possible points on this board.').format(final_score, player.score, total_score))
