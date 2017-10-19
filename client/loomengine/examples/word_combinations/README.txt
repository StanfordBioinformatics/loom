demonstrates: scatter-gather, input groups, output mode gather(n)

When a template step has two inputs rather than one, iteration can be done in two ways:

collated iteration: [a,b] + [c,d] => [a+c,b+d]
combinatorial iteration: [a,b] + [c,d] => [a+c, a+d, b+c, b+d]
With more than two inputs, we could employ some combination of these two approaches.

“groups” provide a flexible way to define when to use collated or combinatorial iteration. Each input has an integer group ID (the default is 0). All inputs with a common group ID will be combined with collation. Between groups, combinatorial iteration is used.

In this example, we iterate over two inputs, one with an array of adjectives and one with an array of nouns. Since the inputs have different group IDs, we iterate over all possible combinations of word pairs (combinatorial).

-------------------------------------------
loom template import word_combinations.yaml

# Run with default input data
loom run start word_combinations

# Run with custom input data
loom run start word_combinations adjectives=[little,green] nouns=[men,pickles,apples]
-------------------------------------------
