This example shows how to import files and use them as inputs

To run this workflow:

1. If running for the first time, start the server

      loom server start --settings-file local.conf

2. Import the input files

      loom import files hello.txt world.txt

3. Import the template

      loom import template hello_world.yaml

4. Select inputs and execute the run

      loom run hello_world hello=hello.txt world=world.txt

5. Monitor the run from the commandline

      loom show run hello_world --detail

6. Monitor the run in the browser

      loom browser

7. If you want to delete the Loom server

      loom server delete

