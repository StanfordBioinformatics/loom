NOTE: This example does not work currently! The parallel feature is not yet available.
This template demonstrates how parallel steps WILL BE implemented using
"scatter" and "gather" modes on inputs and outputs.

To run this workflow:

1. If running for the first time, start the server

      loom server start --settings-file local.conf

2. Import the input file

      loom import file wordfile.txt

3. Import the template

      loom import template word_scoring.yaml

4. Select inputs and execute the run

      loom run word_scoring wordfile=wordfile.txt

5. Monitor the run from the commandline

      loom show run word_scoring --detail

6. Monitor the run in the browser

      loom browser

7. If you want to delete the Loom server

      loom server delete
