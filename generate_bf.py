import argparse
import csv
from typing import TextIO

import numpy as np
from bitarray import bitarray

from pprl.bloom import new_bf, tokenize, populate_bf, encode_bf


def create_bf(word: str, m: int, q: int, k: int) -> bitarray:
    bf = new_bf(m)

    for token in tokenize(word, q):
        populate_bf(bf, k, token.encode("utf-8"))

    return bf


def mask_words_with_frequency(
        word_freq_list: list[tuple[str, int]],
        n: int, q: int, m: int, k: int, s: int
) -> list[tuple[bitarray, int, str]]:
    # collect all absolute frequencies in an array ...
    absolute_freq_lst = np.asarray([wf[1] for wf in word_freq_list])
    # ... and compute the relative frequencies
    abs_freq_sum = np.sum(absolute_freq_lst)
    rel_freq_lst = absolute_freq_lst / abs_freq_sum

    # collect all words ...
    word_lst = [wf[0] for wf in word_freq_list]
    # ... and construct a mapping of word to masked value
    word_to_mask_dict: dict[str, bitarray] = {
        w: create_bf(w, m, q, k) for w in word_lst
    }

    # rng instance with specified seed
    rng = np.random.default_rng(s)
    # draw random words with respect to their relative frequencies
    chosen_words = rng.choice(word_lst, n, p=rel_freq_lst)
    # count the occurrences of every unique word
    chosen_words, chosen_word_counts = np.unique(chosen_words, return_counts=True)[0:100]

    return [
        (
            word_to_mask_dict[chosen_words[i]],  # first element is the masked value
            chosen_word_counts[i],  # second value is the occurrences of this masked value
            chosen_words[i],  # third value is the actual word that has been masked
        ) for i in range(len(chosen_words))
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("words", type=argparse.FileType(mode="r", encoding="utf-8"),
                        help="list of words with frequency information")
    parser.add_argument("output", type=argparse.FileType(mode="w", encoding="utf-8"),
                        help="file to write bloom filters with frequency information to")
    parser.add_argument("-n", type=int, help="amount of words to mask", default=100000)
    parser.add_argument("-q", type=int, help="token size", default=2)
    parser.add_argument("-m", type=int, help="bloom filter size", default=256)
    parser.add_argument("-k", type=int, help="amount of hash values", default=3)
    parser.add_argument("-s", type=int, help="seed for rng-based operations", default=727)

    args = parser.parse_args()

    words_io: TextIO = args.words
    output_io: TextIO = args.output

    words_reader = csv.reader(words_io)
    words_freq_list = [(row[0], int(row[1]),) for row in words_reader]
    words_io.close()

    masked_word_lst = mask_words_with_frequency(words_freq_list, args.n, args.q, args.m, args.k, args.s)

    output_writer = csv.writer(output_io)
    output_writer.writerows([
        # number needs to be converted back to str
        [encode_bf(mw[0]), str(mw[1]), mw[2]] for mw in masked_word_lst
    ])

    output_io.close()
