demonstrates: file inputs

Most of these examples use non-file inputs for convenience, but files can be used as inputs and outputs much like other data types.

In this example, the “lorem_ipsum.txt” input file should be imported prior to importing the “search_file.yaml” template that references it.

--------------------------------------------------------
# Import the template along with its dependencies (lorem_ipsum.txt)
loom template import search_file.yaml

# Run with default input data
loom run start search_file

# Run with custom input data
loom file import beowulf.txt
loom run start search_file pattern=we file_to_search=beowulf.txt\$20b8f89484673eae4f121801e1fec28c
--------------------------------------------------------
