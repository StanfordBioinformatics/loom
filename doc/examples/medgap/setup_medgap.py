#!/usr/bin/env python
import json
import string
import os
import subprocess
import sys
import argparse

INPUT_FILENAME = "chr22-template.json"
OUTPUT_FILENAME = "chr22.json"
HASH_FUNCTION = "md5"

def load_json(filename):
    with open(filename) as infile:
       return json.load(infile) 

def save_json(obj, filename):
    with open(filename, 'w') as outfile:
        json.dump(obj, outfile, indent=4)

def read_file(filename):
    with open(filename) as infile:
        return infile.read()

def add_data_bindings(obj):
    """If a file listed in data_bindings_files is referenced by an input_port, add a binding to data_bindings."""
    for workflow in obj["workflows"]:
        if "data_bindings" not in workflow:
            workflow["data_bindings"] = []
        for filepath in workflow["data_bindings_file_paths"]:
            hash_value = calculate_hash(filepath)
            for step in workflow["steps"]:
                for input_port in step["input_ports"]:
                    if os.path.basename(input_port["file_path"]) == os.path.basename(filepath):
                        new_data_binding = {"destination": {"step": step["name"], "port": input_port["name"]}, "file": {"hash_value": hash_value, "hash_function": HASH_FUNCTION}}
                        workflow["data_bindings"].append(new_data_binding)

def calculate_hash(filepath):
    """Calculate and return hash value of input file using HASH_FUNCTION."""
    if not os.path.exists(filepath):
        print "File not found, using dummy hash value: %s" % filepath
        return "FileNotFound"
    import hashlib
    if HASH_FUNCTION == "md5":
        hashobj = hashlib.md5()
    # Add other desired hashing algorithms here

    with open(filepath) as inputfile:
	print "Hashing %s using %s..." % (filepath, HASH_FUNCTION),
	sys.stdout.flush()
        hashobj.update(inputfile.read())
	hash_value = hashobj.hexdigest()
	print hash_value
    return hash_value

def load_data_bindings(obj, filename):
    """Load data bindings from specified filename into obj."""
    with open(filename) as inputfile:
        inputobj = json.load(inputfile)
    for workflow in obj["workflows"]:
        workflowname = workflow["name"]
        for inputworkflow in inputobj["workflows"]:
            if inputworkflow["name"] == workflowname:
                workflow["data_bindings"] = inputworkflow["data_bindings"]
        if "data_bindings" not in workflow:
            raise Exception("Can't load hashes from destination file; no workflow named %s in %s." % (workflowname, filename))

def upload_data_bindings_files(obj):
    for workflow in obj["workflows"]:
        for filepath in workflow["data_bindings_file_paths"]:
            subprocess.Popen("export RACK_ENV=development && . /opt/xppf/env/bin/activate && /opt/xppf/xppf/bin/xppfupload %s" % filepath, shell=True)

def delete_data_bindings_files(obj):
    """Delete data_bindings_files list since it's not needed any more."""
    for workflow in obj["workflows"]:
        del(workflow["data_bindings_file_paths"])

def check_ports(obj):
    """Make sure filenames across all output ports are unique,
    no two input ports have the same name on the same step,
    and every input port's filename matches an output port or a data binding.
    """
    for workflow in obj["workflows"]:
        
        # Check for duplicate output filenames
        output_filenames = set() 
        for step in workflow["steps"]:
            for output_port in step["output_ports"]:
                if output_port["file_path"] in output_filenames:
                    raise Exception("Duplicate output filename in step %s" % step["name"])
                else:
                    output_filenames.add(output_port["file_path"])

        destinations = set()
        for binding in workflow["data_bindings"]:
            destinations.add((binding["destination"]["step"], binding["destination"]["port"]))
        for step in workflow["steps"]:
            input_port_names = set()
            for input_port in step["input_ports"]:
                # Make sure no input ports have identical names on same step
                if input_port["name"] in input_port_names:
                    raise Exception("More than one input port named \"%s\" in step \"%s\"" % (input_port["name"], step["name"]))
                else:
                    input_port_names.add(input_port["name"])
                # Make sure every input port maps to an output file or a data binding
                if input_port["file_path"] not in output_filenames and \
                   (step["name"], input_port["name"]) not in destinations:
                    raise Exception("Input port \"%s\" in step \"%s\" has no matching data binding destination or output file named \"%s\"" % (input_port["name"], step["name"], input_port["file_path"]))

def add_data_pipes(obj):
    """Build data pipes from output ports to input ports."""
    for workflow in obj["workflows"]:
        data_pipes = []

        # Collect all sources
        sources = {} # Keys are filenames from output ports
        for step in workflow["steps"]:
            for output_port in step["output_ports"]:
                if output_port["file_path"] in sources:
                    raise Exception("Duplicate file_path in output ports")
                sources[output_port["file_path"]] = {"step": step["name"], "port": output_port["name"]}
        
        # Add a data pipe for each destination
        for step in workflow["steps"]:
            for input_port in step["input_ports"]:
                if input_port["file_path"] in sources:
                    new_pipe = {"source": sources[input_port["file_path"]], "destination": {"step": step["name"], "port": input_port["name"]}}
                    data_pipes.append(new_pipe)

        workflow["data_pipes"] = data_pipes

def parse_arguments():
    parser = argparse.ArgumentParser(description='Preprocess template JSON, compute hashvalues of files, and upload files.')
    parser.add_argument('--nohash', action='store_true', default=False, help='Use hashes from destination JSON.')
    parser.add_argument('--noupload', action='store_true', default=False, help='Skip uploading input files.')
    args = parser.parse_args()
    return args 

def main():
    # Parse arguments
    args = parse_arguments()    

    # Get dict of constants
    obj = load_json(INPUT_FILENAME)    
    constants_dict = obj['constants']

    # Substitute constants 
    entire_file_string = read_file(INPUT_FILENAME)
    template = string.Template(entire_file_string)
    substituted_string = template.substitute(constants_dict)
    
    # Convert to Python object, remove constants dict
    obj = json.loads(substituted_string)
    del(obj["constants"])

    # Upload data_bindings files
    if not args.noupload:
        upload_data_bindings_files(obj)

    if args.nohash:
        # Get data_bindings from destination JSON
        load_data_bindings(obj, OUTPUT_FILENAME)
    else:
        # Hash and add files to data_bindings based on data_bindings_files list and input ports
        add_data_bindings(obj)

    # Remove files dict since it's not needed any more
    delete_data_bindings_files(obj)

    # Validation, compute data pipes
    check_ports(obj)
    add_data_pipes(obj)
    save_json(obj, OUTPUT_FILENAME)

if __name__ == "__main__":
    main() 
