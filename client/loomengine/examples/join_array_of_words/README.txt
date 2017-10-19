demonstrates: array data, gather mode on an input

Earlier we saw how to join two words, each defined on a separate input. But what if we want to join an arbitrary number of words?

This example has a single input, whose default value is an array of words. By setting the mode of this input as “gather”, instead of iterating as in the last example we will execute a single task that receives the full list of words as an input.

In this example we merge the strings and output the result as a string.

---------------------------------------------
loom template import join_array_of_words.yaml

# Run with default input data
loom run start join_array_of_words

# Run with custom input data
loom run start join_array_of_words wordarray=[uno,dos,tres]
---------------------------------------------
