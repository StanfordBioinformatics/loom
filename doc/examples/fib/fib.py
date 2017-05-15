import yaml

NUM_STEPS = 10

workflow = {"name":"fib",
            "fixed_inputs":[{"type":"string","channel":"fib0","data":{"contents":"0"}},
                            {"type":"string","channel":"fib1","data":{"contents":"1"}},
            ],
            "outputs":[{"type":"string","channel":"fib"+str(NUM_STEPS+1)}],
            "steps":[],
            }
for i in xrange(2,NUM_STEPS+2):
    step = {"name":"fib"+str(i),
            "command":"echo $(({{fib%s}}+{{fib%s}}))" % (i-1, i-2),
            "environment":{"docker_image":"ubuntu"},
            "resources":{"cores":"1","memory":"1"},
            "inputs":[{"type":"string", "channel":"fib"+str(i-1)},
                      {"type":"string", "channel":"fib"+str(i-2)},
                    ],
            "outputs":[{"type":"string", "channel":"fib"+str(i), "source":{"stream":"stdout"}}],
            }

    workflow["steps"].append(step)

with open("fib.yaml", "w") as workflow_file:
    yaml.dump(workflow, workflow_file, default_flow_style=False)
