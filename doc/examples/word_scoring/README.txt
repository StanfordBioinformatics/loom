This template shows how Loom data is not restricted to
scalars or arrays but also supports higher dimensionality,
and here this is used to create a
scatter-scatter-gather-gather pattern. In this example,
a sentence is split into words, which are split into
letters. Each letter is converted to an integer score.
When a "gather" is applied to sum the scores letters,
it merges only the last level of split, creating a separate
sum for each word. A second gather is applied to calculate
the product of the scores of all the words.

To run this workflow:

1. If running for the first time, start the server

      loom server start --settings-file local.conf

2. Import the template

      loom import template word_scoring.yaml

3. Execute the run

      loom run word_scoring

      # or to override the default input value:

      loom run word_scoring wordlist="my own crazy input here"

4. Monitor the run from the commandline

      loom show run word_scoring --detail

5. Monitor the run in the browser

      loom browser

6. If you want to delete the Loom server

      loom server delete
