import argparse
import csv
from typing import TextIO

from bitarray import bitarray

from pprl.bloom import tokenize, decode_bf


def perform_attack(
        clk_freq_sol_list: list[tuple[bitarray, int, str]],
        word_freq_list: list[tuple[str, int]],
        q: int
) -> list[tuple[str, set[str]]]:
    # sort both lists in descending order (alignment step)
    clk_freq_sol_list.sort(key=lambda t: t[1], reverse=True)
    word_freq_list.sort(key=lambda t: t[1], reverse=True)

    # construct word -> token lookup
    word_to_token_dict: dict[str, set[str]] = {wf[0]: tokenize(wf[0], q) for wf in word_freq_list}
    # determine bit length
    bit_len = max([len(cfs[0]) for cfs in clk_freq_sol_list])
    # determine frequency table length (since len(clk) != len(words) in most cases)
    freq_table_len = min(len(clk_freq_sol_list), len(word_freq_list))

    # list of candidate tokens
    candidate_token_lst: list[set[str]] = []

    # iterate over all bits (candidate token set generation step)
    for i in range(bit_len):
        candidate_p: set[str] = set()  # positive token set
        candidate_n: set[str] = set()  # negative token set

        for j in range(freq_table_len):
            bf = clk_freq_sol_list[j][0]  # look at j-th bloom filter
            tokens = word_to_token_dict[word_freq_list[j][0]]  # look at j-th ranked word and its tokens

            if bf[i] == 1:
                # if the i-th bit is set, add it to the positive token set
                candidate_p.update(tokens)
            else:
                candidate_n.update(tokens)

        # compute the actual candidate tokens for the i-th bit
        candidate_token_lst.append(candidate_p - candidate_n)

    result_lst: list[tuple[str, set[str]]] = []

    # perform guesses for every clk
    for cfs in clk_freq_sol_list:
        clk = cfs[0]
        correct_word = cfs[2]

        # start by using all words in the frequency table as candidates
        candidate_words = set([wf[0] for wf in word_freq_list])

        # iterate over every bit
        for i in range(bit_len):
            # do not consider unset bits
            if clk[i] == 0:
                continue

            # look at the candidate tokens for the i-th bit
            candidate_tokens = candidate_token_lst[i]
            # keep track of words that will be excluded. this is just to avoid concurrent modifications
            # to the set while we're eliminating candidate words.
            words_to_exclude: set[str] = set()

            # iterate over remaining candidate words
            for word in candidate_words:
                word_tokens = word_to_token_dict[word]

                # check if there's any overlap between the word's tokens and the candidate tokens for this bit.
                # if not, this word is excluded from the candidates for this clk.
                if len(candidate_tokens.intersection(word_tokens)) == 0:
                    words_to_exclude.add(word)

            # update candidate words
            candidate_words = candidate_words - words_to_exclude

            # we can exit here if we have no more candidates or exactly one
            if len(candidate_tokens) <= 1:
                break

        result_lst.append((correct_word, candidate_words,))

    return result_lst


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("words", type=argparse.FileType(mode="r", encoding="utf-8"),
                        help="list of words with frequency information")
    parser.add_argument("clks", type=argparse.FileType(mode="r", encoding="utf-8"),
                        help="list of CLKs with frequency information and words for verification")
    parser.add_argument("output", type=argparse.FileType(mode="w", encoding="utf-8"),
                        help="file to write correct words with guessed words to")
    parser.add_argument("-q", type=int, help="token size", default=2)
    parser.add_argument("--stdout-csv", action="store_true", help="flag to enable CSV output")

    args = parser.parse_args()

    words_io: TextIO = args.words
    clks_io: TextIO = args.clks
    output_io: TextIO = args.output

    words_reader = csv.reader(words_io)
    words_freq_lst = [(row[0], int(row[1]),) for row in words_reader]
    words_io.close()

    clks_reader = csv.reader(clks_io)
    clks_freq_sol_lst = [(decode_bf(row[0]), int(row[1]), row[2]) for row in clks_reader]
    clks_io.close()

    result_lst = perform_attack(clks_freq_sol_lst, words_freq_lst, args.q)

    output_writer = csv.writer(output_io)
    output_writer.writerows([(row[0], ",".join(row[1]),) for row in result_lst])
    output_io.close()

    count_exact_match = 0  # one result, that being the correct one
    count_potential_match = 0  # one result, that contained in a set of candidates
    count_false_match = 0  # no results, but candidates exist
    count_no_match = 0  # no results at all

    for word, candidate_words in result_lst:
        candidate_word_count = len(candidate_words)

        if candidate_word_count == 0:
            count_no_match += 1
            continue

        if word in candidate_words:
            if candidate_word_count == 1:
                count_exact_match += 1
            else:
                count_potential_match += 1
        else:
            count_false_match += 1

    format_stdout_csv: bool = args.stdout_csv

    if format_stdout_csv:
        print(",".join([
            str(len(result_lst)),
            str(count_exact_match),
            str(count_potential_match),
            str(count_false_match),
            str(count_no_match)
        ]))
    else:
        print(f"TOTAL WORD COUNT:  {len(result_lst)}")
        print(f"Exact matches:     {count_exact_match}")
        print(f"Potential matches: {count_potential_match}")
        print(f"False matches:     {count_false_match}")
        print(f"No matches:        {count_no_match}")
