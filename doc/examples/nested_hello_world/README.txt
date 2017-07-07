This example shows how with nested templates, children
can be defined separately from their parents.

To run this workflow:

1. If running for the first time, start the server

      loom server start --settings-file local.conf

2. Import the input files

      loom import files hello.txt world.txt

3. Import the child templates

      loom import template steps/hello_step.yaml
      loom import template steps/world_step.yaml
      loom import template steps/final_step.yaml

4. Import the parent template

      loom import template hello_world.yaml

5. Select inputs and execute the run

      loom run hello_world hello=hello.txt world=world.txt

6. Monitor the run from the commandline

      loom show run hello_world --detail

7. Monitor the run in the browser

      loom browser

8. If you want to delete the Loom server

      loom server delete

