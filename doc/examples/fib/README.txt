This template demonstrates how channels are used to declare
dependencies between steps to create concurrent
or serial execution. It is also useful for creating
a wide, shallow workflow, i.e. with many steps that
are not nested.

To run this workflow:

1. If running for the first time, start the server

      loom server start --settings-file local.conf

2. Import the template

      loom import template fib.yaml

3. Execute the run

      loom run fib

      # Or to override default input values:

      loom run fib fib0=7 fib1=13

4. Monitor the run from the commandline

      loom show run fib --detail

5. Monitor the run in the browser

      loom browser

6. If you want to delete the Loom server

      loom server delete

(Optional) You can re-generate this workflow with an arbitrary number of steps. Edit fib.py, change NUM_STEPS to the desired number of steps, and run it like this:

      python fib.py

This will overwrite fib.yaml, after which you can proceed as above.

You might need to "pip install pyyaml" if you don't have it already.
