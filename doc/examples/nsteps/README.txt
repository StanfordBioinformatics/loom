To run this workflow:

1. Import the template

      loom import template nsteps.yaml

2. Execute the run

      loom run nsteps

3. Monitor the run from the commandline

      loom show run nsteps --detail

4. Monitor the run in the browser

      loom browser

5. If you want to delete the Loom server

      loom server delete

(Optional) You can re-generate this workflow with an arbitrary number of steps. Edit nsteps.py, change NUM_STEPS to the desired number of steps, and run it like this:

      python nsteps.py

This will overwrite nsteps.yaml, after which you can proceed as above.

You might need to "pip install pyyaml" if you don't have it already.
