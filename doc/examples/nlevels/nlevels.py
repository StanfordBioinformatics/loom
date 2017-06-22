import yaml

NUM_LEVELS = 3

template = {"name":"nlevels",
             "fixed_inputs":[{"type":"string","channel":"maininput","data":{"contents":"0"}},
             ],
             "outputs":[{"type":"string","channel":"mainoutput"}],
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
                 "outputs":[{"type":"string", "channel":"mainoutput", "source":{"stream":"stdout"}}]}
        stepB = {"name":"level%sB" % level,
                 "command":"echo %s" % level,
                 "environment":{"docker_image":"ubuntu"},
                 "resources":{"cores":"1","memory":"1"},
                 "inputs":[{"type":"string", "channel":"maininput"}],
                 "outputs":[{"type":"string", "channel":"lostoutput", "source":{"stream":"stdout"}}]}

        template["steps"] = [stepA, stepB]
        return
    else:
        stepA = {"name":"level%sA" % level,
                 "inputs":[{"type":"string", "channel":"maininput"}],
                 "outputs":[{"type":"string", "channel":"mainoutput"}],
                 "steps":[],
        }
        stepB = {"name":"level%sB" % level,
                 "inputs":[{"type":"string", "channel":"maininput"}],
                 "outputs":[{"type":"string", "channel":"mainoutput"}],
                 "steps":[],
        }
        template["steps"] = [stepA, stepB]
        recursively_add_two_steps(stepA, level)
        recursively_add_two_steps(stepB, level)

recursively_add_two_steps(template, NUM_LEVELS)
with open("nlevels.yaml", "w") as template_file:
    yaml.dump(template, template_file, default_flow_style=False)
