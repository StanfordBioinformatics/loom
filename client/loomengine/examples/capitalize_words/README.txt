demonstrates: array data, iterating over an array input

This template illustrates the concept of non-scalar data (in this case a 1-dimensional array). The default mode for inputs is “no_gather”, which means that rather than gather all the objects into an array to be processed together in a single task, Loom will iterate over the array and execute the command once for each data object, in separate tasks.

Here we capitalize each word in the array. The output from each task executed is a string, but since many tasks are executed, the output is an array of strings.

Note the use of “as_channel” on the input definition. Since our input channel is an array we named the channel with the plural “words”, but this run executes a separate tasks for each element in the array it may be confusing to refer to “{{words}} inside the command. It improves readability to use “as_channel: word”.

------------------------------------------
loom template import capitalize_words.yaml

# Run with default input data
loom run start capitalize_words

# Run with custom input data
loom run start capitalize_words words=[uno,dos,tres]
------------------------------------------

