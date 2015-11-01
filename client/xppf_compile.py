#!/usr/bin/env python
import argparse
import hashlib
import json
import os
import re
import string
import subprocess
import sys
import warnings

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

def step_files_to_ports(obj):
    """Convert input_files and output_files to input_ports and output_ports in each step.
    Automatically generates port names from step names and filenames.
    """
    for workflow in obj["workflows"]:
        for step in workflow["steps"]:
            step["input_ports"] = []
            for input_file in step["input_files"]:
                step["input_ports"].append({"name": "%s_%s_in" % (step["name"], input_file),"file_path": input_file})
            del(step["input_files"])
            step["output_ports"] = []
            for output_file in step["output_files"]:
                step["output_ports"].append({"name": "%s_%s_out" % (step["name"], output_file),"file_path": output_file})
            del(step["output_files"])

def add_data_bindings(obj, hashes):
    """If a workflow input file is referenced by an input_port, add a binding to data_bindings."""
    for workflow in obj["workflows"]:
        if "data_bindings" not in workflow:
            workflow["data_bindings"] = []
        for filepath in workflow["imports"]:
            hash_value = hashes[workflow["name"]][filepath]
            for step in workflow["steps"]:
                for input_port in step["input_ports"]:
                    if os.path.basename(input_port["file_path"]) == os.path.basename(filepath):
                        new_data_binding = {"destination": {"step": step["name"], "port": input_port["name"]}, "file": {"hash_value": hash_value, "hash_function": HASH_FUNCTION}}
                        workflow["data_bindings"].append(new_data_binding)

def calculate_hashes(obj):
    """Calculate hashes for workflow input files and return results indexed by workflow name and filepath."""
    hashes = {}
    for workflow in obj["workflows"]:
        workflowname = workflow["name"]
        hashes[workflowname] = {}
        for filepath in workflow["imports"]:
            hash_value = calculate_hash(filepath)
            hashes[workflowname][filepath] = hash_value
    return hashes

def calculate_hash(filepath):
    """Calculate and return hash value of input file using HASH_FUNCTION."""
    if not os.path.exists(filepath):
        warnings.warn("File not found, using dummy hash value: %s" % filepath)
        return "FileNotFound"
    if HASH_FUNCTION == "md5":
        hashobj = hashlib.md5()
    # Add other desired hashing algorithms here

    print "Hashing %s using %s..." % (filepath, HASH_FUNCTION),
    sys.stdout.flush()
    for chunk in chunks(filepath, chunksize=hashobj.block_size*1024):
        hashobj.update(chunk)
    hash_value = hashobj.hexdigest()
    print hash_value
    return hash_value

def chunks(filepath, chunksize):
    """Generator that sequentially reads and yields <chunksize> bytes from a file."""
    with open(filepath, 'rb') as fp:
        chunk = fp.read(chunksize)
        while(chunk):
            yield chunk
            chunk = fp.read(chunksize)
    
def upload_imports(obj):
    vcf = re.compile("\.vcf$")
    bam = re.compile("\.bam$")
    for workflow in obj["workflows"]:
        # Split input files into VCF's and BAM's vs. other files.
        datafiles = []
        otherfiles = []
        for filepath in workflow["imports"]:
            if re.search(vcf, filepath) or re.search(bam, filepath):
                datafiles.append(filepath)
            else:
                otherfiles.append(filepath)
        # Upload VCF's and BAM's first so that index files are newer.
        dataprocesses = []
        otherprocesses = []
        for filepath in datafiles:    
            process = subprocess.Popen("export RACK_ENV=development && . /opt/xppf/env/bin/activate && /opt/xppf/xppf/bin/xppfupload %s" % filepath, shell=True)
            dataprocesses.append(process)
        for process in dataprocesses:
            process.wait()
        for filepath in otherfiles:
            process = subprocess.Popen("export RACK_ENV=development && . /opt/xppf/env/bin/activate && /opt/xppf/xppf/bin/xppfupload %s" % filepath, shell=True)
            otherprocesses.append(process)
        for process in otherprocesses:
            process.wait()

def delete_workflow_imports(obj):
    """Delete imports dicts from workflows since they're not needed any more."""
    for workflow in obj["workflows"]:
        del(workflow["imports"])

def check_ports(obj):
    """Make sure filenames across all output ports are unique within each workflow,
    input/output port names are unique within each step, 
    no two data_bindings have the same destination,
    and every input port's filename matches an output port or a data binding.
    """
    for workflow in obj["workflows"]:
        
        #Collect output filenames, and check for duplicates in each workflow
        output_filenames = set() 
        for step in workflow["steps"]:
            # Check for duplicate output port names in each step
            output_port_names = set()
            for output_port in step["output_ports"]:
                if output_port["name"] in output_port_names:
                    raise Exception("More than one output port named \"%s\" in step \"%s\"" % (output_port["name"], step["name"]))
                else:
                    output_port_names.add(output_port["name"])

                if output_port["file_path"] in output_filenames:
                    raise Exception("Duplicate output filename in step %s" % step["name"])
                else:
                    output_filenames.add(output_port["file_path"])

        # Collect destinations of data_bindings and check for duplicates
        destinations = set()
        for binding in workflow["data_bindings"]:
            new_binding = (binding["destination"]["step"], binding["destination"]["port"])
            if new_binding in destinations:
                raise Exception("More than one data_binding for step %s, port %s" % (new_binding[0], new_binding[1]))
            else:
                destinations.add(new_binding)

        for step in workflow["steps"]:
            # Check for duplicate input port names within each step
            input_port_names = set()
            for input_port in step["input_ports"]:
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
    parser.add_argument('inputfilename')
    parser.add_argument('--updatehashes', action='store_true', default=False, help='Force recalculating hashes.')
    parser.add_argument('--upload', action='store_true', default=False, help='Upload input files using xppfcompile.')
    parser.add_argument('-o', '--outputfilename', help='Output filename. Defaults to <inputfileroot>-compiled.json.')
    args = parser.parse_args()
    return args 

def substitute_constants(inputfilename):
    # Get dict of constants
    obj = load_json(inputfilename)    
    constants_dict = obj['constants']

    # Substitute constants 
    entire_file_string = read_file(inputfilename)
    template = string.Template(entire_file_string)
    substituted_string = template.substitute(constants_dict)
    
    # Convert to Python object, remove constants dict
    obj = json.loads(substituted_string)
    del(obj["constants"])

    return obj

def remove_extensions(filepath):
    """Return the filename without extensions."""
    root,ext = os.path.splitext(filepath)
    if ext == '':
        return root
    else:
        return remove_extensions(root)

def generate_filenames(args):
    root = remove_extensions(args.inputfilename)
    ext = os.path.splitext(args.inputfilename)[1]
    hashesfilename = root + "-hashes" + ext
    if args.outputfilename is None:
        outputfilename = root + "-compiled" + ext
    else:
        outputfilename = args.outputfilename
    return hashesfilename, outputfilename

def get_hashes(obj, hashesfilename, updatehashes):
    """Generate and save hashes, or load from file if exists."""
    if updatehashes or not os.path.exists(hashesfilename):
        hashes = calculate_hashes(obj)
        save_json(hashes, hashesfilename)
    else:
        hashes = load_json(hashesfilename)
    return hashes

def main():
    args = parse_arguments()    
    hashesfilename, outputfilename = generate_filenames(args)

    # Load input JSON file, substitute constants, convert to Python object
    obj = substitute_constants(args.inputfilename)

    # Generate hashes for all imports, or load from file
    hashes = get_hashes(obj, hashesfilename, args.updatehashes)

    # Convert input_files and output_files in all steps into ports
    step_files_to_ports(obj)

    # Add files to data_bindings based on workflow input files and step input files 
    add_data_bindings(obj, hashes)

    if args.upload:
        upload_imports(obj)

    #  Remove imports dicts from workflows since they're not needed any more
    delete_workflow_imports(obj)

    # Validation, compute data pipes
    check_ports(obj)
    add_data_pipes(obj)
    save_json(obj, outputfilename)

if __name__ == "__main__":
    main() 
