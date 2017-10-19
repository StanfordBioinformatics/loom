demonstrates: nested scatter-gather

Why should we bother differentiating between “gather” and “gather(2)”? This example illustrates why, by showing how to construct a scatter-scatter-gather-gather workflow. On the first gather, we do not fully gather the results into an array, but only gather the last level of nested arrays. This lets us group data for the letters in each word while keeping data for different words separate. On the second gather, we combine the data for each word to get an overall result for the sentence.

------------------------------------------
loom template import sentence_scoring.yaml

# Run with default input data
loom run start sentence_scoring

# Run with custom input data
loom run start sentence_scoring sentence='To infinity and beyond'
------------------------------------------

