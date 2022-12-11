# Frequency-based attack on Bloom filters in PPRL

This repository contains an implementation of a frequency-based re-identification attack on Bloom filters in privacy-preserving record linkage protocols.
The attack was first described by Christen et al.[^1] and discussed on my personal website in a series dedicated to Bloom-filter-based PPRL.

## How to use

You will need a frequency table of values you want to mask using Bloom filters.
You can find an example in the [data directory](./data/) using the top 1k first names in Germany[^2].
The first column must contain values and the second column their respective absolute frequencies.
The table must be CSV-formatted.

Using this project assumes you have [Poetry](https://python-poetry.org/) installed.
Run `poetry install` in the root of this repository, then drop into a virtual environment using `poetry shell`.

To perform the attack the same way the authors did, you will need to compute the amount of hash values *k*.
Choose a filter size *m* (e.g. 256) and token size *q* (e.g. 2) and run the following script.

```
$ python compute_optimal_k.py data/german-names.csv -m 256 -q 2
24.19163983958364
```

In this example, *k* should be 24.
Next, generate a list of CLKs based on the frequency information of your word list.
It's advisable that you create an output directory first, e.g. using `mkdir -p out`.
Select an amount of CLKs to generate, e.g. 1m, then run the following script with your previously selected value *k*.

```
$ python generate_bf.py data/german-names.csv out/german-names-masked.csv -n 1000000 -q 2 -m 256 -k 24
```

Finally, run the attack with the following script.
You can enable CSV output with the `--stdout-csv` flag which will print the amount of exact matches, potential matches, false matches and no matches as comma-separated values.
The output file contains the detailed guesses for each CLK.

```
$ python perform_attack.py data/german-names.csv out/german-names-masked.csv out/german-names-guess.csv -q 2 
TOTAL WORD COUNT:  1000
Exact matches:     3
Potential matches: 0
False matches:     81
No matches:        916
```

## References

[^1]: Christen, Peter, et al. "Efficient cryptanalysis of bloom filters for privacy-preserving record linkage." Pacific-Asia Conference on Knowledge Discovery and Data Mining. Springer, Cham, 2017.
[^2]: Taken from Forebears' "Most Common Last Names In Germany" ([URL](https://forebears.io/germany/surnames), [Archive](https://web.archive.org/web/20220922090455/https://forebears.io/germany/surnames))