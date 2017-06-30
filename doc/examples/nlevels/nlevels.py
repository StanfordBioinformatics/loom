import yaml

NUM_LEVELS = 5

template = {"name":"nlevels",
             "fixed_inputs":[{"type":"string","channel":"maininput",
                              "data":{"contents":"0"}},
             ],
             "steps":[],
}

def recursively_add_two_steps(template, level):
    level-=1
    if level == 0:
        # Add leaves
        stepA = {"name":"level%sA" % level,
                 "command":"echo %s" % level,
                 "environment":{"docker_image":"ubuntu"},
                 "resources":{"cores":"1","memory":"1"},
                 "inputs":[{"type":"string", "channel":"maininput"}],
                 "outputs":[{"type":"string",
                             "channel":"outputA",
                             "source":{"stream":"stdout"}}]}
        stepB = {"name":"level%sB" % level,
                 "command":"echo %s" % level,
                 "environment":{"docker_image":"ubuntu"},
                 "resources":{"cores":"1","memory":"1"},
                 "inputs":[{"type":"string", "channel":"maininput"}],
                 "outputs":[{"type":"string",
                             "channel":"outputB",
                             "source":{"stream":"stdout"}}]}

        template["steps"] = [stepA, stepB]
        return
    else:
        stepA = {"name":"level%sA" % level,
                 "inputs":[{"type":"string", "channel":"maininput"}],
                 "steps":[],
        }
        stepB = {"name":"level%sB" % level,
                 "inputs":[{"type":"string", "channel":"maininput"}],
                 "steps":[],
        }
        template["steps"] = [stepA, stepB]
        recursively_add_two_steps(stepA, level)
        recursively_add_two_steps(stepB, level)

recursively_add_two_steps(template, NUM_LEVELS)
with open("nlevels.yaml", "w") as template_file:
    yaml.dump(template, template_file, default_flow_style=False)
