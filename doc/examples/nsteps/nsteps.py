import yaml

NUM_STEPS = 100

workflow = {"name":"nsteps",
            "fixed_inputs":[{"type":"string","channel":"maininput","data":{"contents":"0"}},
            ],
            "outputs":[{"type":"string","channel":"mainoutput"}],
            "steps":[],
            }
for i in xrange(NUM_STEPS):
    step = {"name":"step%s" % i,
            "command":"echo %s" % i,
            "environment":{"docker_image":"ubuntu"},
            "resources":{"cores":"1","memory":"1"},
            "inputs":[{"type":"string", "channel":"maininput"}],
            "outputs":[{"type":"string", "channel":"mainoutput", "source":{"stream":"stdout"}}],
            }

    workflow["steps"].append(step)

with open("nsteps.yaml", "w") as workflow_file:
    yaml.dump(workflow, workflow_file, default_flow_style=False)
