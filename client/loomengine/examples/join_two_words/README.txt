demonstrates: simplest example, a.k.a. hello world

This example illustrates the minimal set of features in a Loom template: name, command, environment (defined by a docker image), and input/output definitions.

We use the optional “data” field on the inputs to assign default values.

The command “echo {{word1}} {{word2}}” makes use of Jinja2 notation to substitute input values. “{{word1}}” in the command will be substituted with the value provided on the “word1” input channel. For inputs of type “string”, “integer”, “boolean”, and “float”, the value substituted is a string representation of the data. For inputs of type “file”, the filename is substituted. The full set of Jinja2 features may be used, including filters, conditional statements, and loops.

----------------------------------------
loom template import join_two_words.yaml

# Run with default input data
loom run start join_two_words

# Run with custom input data
loom run start join_two_words word1=foo word2=bar
----------------------------------------

