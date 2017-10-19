demonstrates: steps in serial and parallel, file inputs

This is a simple example that processes the content of two text files in two parallel steps (it just capitalizes the text) and then concatenates the results in a separate step.

We use Jinja2 notation to substitute the path of filenames, for example "cat {{ hello }} | tr '[a-z]' '[A-Z]' > {{ hello_cap }}".

Two of the inputs ("hello" and "world") are of type "file", and have no default values. We will have to import files and assign these to the input channels when we start a workflow run.

The third input ("punctuation") is of type "string" and has a default value of "!!", so a value is not required to start a run. However, you can override the default by assigning a new string to this channel when starting a run.

----------------------------------------
loom file import hello.txt
loom file import world.txt
loom template import hello_world.yaml
loom run start hello_world hello=hello.txt world=world.txt

# To override the default value for the "punctuation" input:
loom run start hello_world hello=hello.txt world=world.txt punctuation=":)"
----------------------------------------
