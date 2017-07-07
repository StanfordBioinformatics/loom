This template demonstrates how steps can be nested in other steps.
It is also useful for creating a narrow, deep workflow, i.e. with few
(1) steps per level but with many nested levels.

To run this workflow:

1. If running for the first time, start the server

      loom server start --settings-file local.conf

2. Import the template

      loom import template skinny_tree.yaml

3. Execute the run

      loom run skinny_tree

      # Or to override the defalt input value:

      loom run skinny_tree in=MyValue

4. Monitor the run from the commandline

      loom show run skinny_tree --detail

5. Monitor the run in the browser

      loom browser

6. If you want to delete the Loom server

      loom server delete

(Optional) You can re-generate this workflow with an arbitrary number of steps. Edit skinny_tree.py, change NUM_STEPS to the desired number of steps, and run it like this:

      python skinny_tree.py

This will overwrite skinny_tree.yaml, after which you can proceed as above.

You might need to "pip install pyyaml" if you don't have it already.
