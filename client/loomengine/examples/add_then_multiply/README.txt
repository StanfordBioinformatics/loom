demonstrates: multistep templates, connecting inputs and outputs, custom interpreter

All the previous examples have involved just one step. Here we show how to define more than one step in a template.

Also, since we are doing math in this example, it is easier to use python than bash, so we introduce the concept of custom interpreters.

Notice how the flow of data is defined using shared channel names between inputs and outputs. On the top-level template “add_then_multiply” we define input channels “a”, “b”, and “c”. These are used by the steps “add” (“a” and “b”) and “multiply” (“c”). There is also an output from “add” called “ab_sum” that serves as an input for “multiply”. Finally, the output from “multiply”, called “result” is passed up to “add_then_multiply” as a top-level output.

-------------------------------------------
loom template import add_then_multiply.yaml

# Run with default input data
loom run start add_then_multiply

# Run with custom input data
loom run start add_then_multiply a=1 b=2 c=3
-------------------------------------------
