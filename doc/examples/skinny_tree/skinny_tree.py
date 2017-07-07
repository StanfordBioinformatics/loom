import yaml

NUM_LEVELS = 3

template = {"name":"skinny_tree",
            "inputs":[{"type":"string","channel":"in",
                       "data":{"contents":"0"}}],
            "outputs": [{"type": "string",
                         "channel": "out"}],
            "steps":[],
}

def recursively_add_step(template, level):
    level-=1
    if level == 0:
        # Add leaf
        step = {"name":"level%s" % level,
                "command":'echo "This tree is %s levels tall, '\
                'and the input was {{in}}"' % NUM_LEVELS,
                "environment":{"docker_image":"ubuntu"},
                "resources":{"cores":"1","memory":"1"},
                "inputs":[{"type":"string", "channel":"in"}],
                "outputs":[{"type":"string",
                            "channel":"out",
                            "source":{"stream":"stdout"}}]}
        template["steps"] = [step]
        return
    else:
        step = {"name":"level%s" % level,
                "inputs":[{"type":"string", "channel":"in"}],
                "outputs":[{"type":"string", "channel":"out"}],
                "steps":[],
        }
        template["steps"] = [step]
        recursively_add_step(step, level)

recursively_add_step(template, NUM_LEVELS)

with open("skinny_tree.yaml", "w") as template_file:
    yaml.dump(template, template_file, default_flow_style=False)
