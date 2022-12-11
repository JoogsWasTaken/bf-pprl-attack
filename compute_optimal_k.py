import argparse
import csv
import math
from typing import TextIO

from pprl.bloom import tokenize


def compute_optimal_k_for_wordlist(
        word_lst: list[str],
        m: int, q: int
) -> float:
    total_uniq_token_count = 0

    for word in word_lst:
        total_uniq_token_count += len(tokenize(word, q))

    # k that minimizes false positives in lookup operations is computed as m*n*ln(2) where
    # m is the CLK size and n is the amount of expected insertions. n is just the average
    # token count across the entire frequency table.
    average_token_count = total_uniq_token_count / len(word_lst)
    ln2 = math.log(2) / math.log(math.e)

    return ln2 * m / average_token_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("words", type=argparse.FileType(mode="r", encoding="utf-8"),
                        help="list of words with frequency information")
    parser.add_argument("-m", type=int, help="bloom filter size", default=256)
    parser.add_argument("-q", type=int, help="token size", default=2)

    args = parser.parse_args()

    words_io: TextIO = args.words

    words_reader = csv.reader(words_io)
    words_lst = [row[0] for row in words_reader]
    words_io.close()

    print(compute_optimal_k_for_wordlist(words_lst, args.m, args.q))
