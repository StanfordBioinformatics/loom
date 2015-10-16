#!/usr/bin/env python
from xppf_compile import *

args = parse_arguments()
obj = substitute_constants(args.inputfilename)
upload_data_bindings_files(obj)
