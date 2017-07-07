This template shows how to create parallel workflows
by using nonscalar inputs, defining scatter/gather modes
on outputs/inputs respectively. It shows how to combine array
inputs with cross-product behavior by giving the inputs different
groups. (Inputs within the same group combine as a dot-product).
It also shows how "gather depth" can be set to flatten input data
that is more than scalar or 1-dimensional (in this case gather(2).

To run this workflow:

1. If running for the first time, start the server

      loom server start --settings-file local.conf

2. Import the template

      loom import template word_combinations.yaml

3. Execute the run

      loom run word_combinations

      # or to override the default input values:

      loom run word_combinations adjectives="[hard,soft]" nouns="[ball,sell,wood]"

4. Monitor the run from the commandline

      loom show run word_combinations --detail

5. Monitor the run in the browser

      loom browser

6. If you want to delete the Loom server

      loom server delete
