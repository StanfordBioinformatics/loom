demonstrates: reusing templates

Let’s look at another way to write the previous workflow. The “add” and “multiply” steps can be defined as stand-alone workflows. After they are defined, we can create a template that includes those templates as steps.

---------------------------------------------------------------
# Import child templates before the parent that references them
loom template import add.yaml
loom template import multiply.yaml
loom template import building_blocks.yaml

# Run with default input data
loom run start building_blocks

# Run with custom input data
loom run start building_blocks a=1 b=2 c=3
---------------------------------------------------------------
