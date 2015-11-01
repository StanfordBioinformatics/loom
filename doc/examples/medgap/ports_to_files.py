#!/usr/bin/env python
import json

with open("chr22-template.json") as inputfile:
    obj = json.load(inputfile)

for workflow in obj["workflows"]:
    for step in workflow["steps"]:
        step["input_files"] = []
        for input_port in step["input_ports"]:
            step["input_files"].append(input_port["file_path"]) 
        del(step["input_ports"])
        step["output_files"] = []
        for output_port in step["output_ports"]:
            step["output_files"].append(output_port["file_path"]) 
        del(step["output_ports"])

with open("chr22-template-simplified.json", 'w') as outputfile:
    json.dump(obj, outputfile)
