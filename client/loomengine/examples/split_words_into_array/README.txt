demonstrates: array data, scatter mode on an output, output parsers

This example is the reverse of the previous example. We begin with a scalar string of space-separated words, and split them into an array.

To generate an array output from a single task, we set the output mode to “scatter”.

We also need to instruct Loom how to split the text in stdout to an array. For this we use a parser that uses the space character as the delimiter and trims any extra whitespace characters from the words.

------------------------------------------------
loom template import split_words_into_array.yaml

# Run with default input data
loom run start split_words_into_array

# Run with custom input data
loom run start split_words_into_array text="one two three"
------------------------------------------------
