#!/usr/bin/env python

from argparse import ArgumentParser
import json
import jsonschema
import os
import shutil
import uuid

class ValidationError(Exception):
    pass

class Helper:
    @classmethod
    def get_item_by_name(cls, objectlist, name):
        items = filter(lambda item: item.name == name, objectlist)
        if len(items) != 1:
            raise Exception
        return items[0]

#class FileImportSource:
#    def __init__(self, file_source_spec):
#        # TODO
#        pass

#class FileImport(self, task):
#    def __init__(self, file_import_spec):
#        self.name = file_import_spec.get('name')
#        self.source = FileImportSource(file_import_spec.get('source'))

class File:
    def __init__(self, file_spec):
        self.name = file_spec.get('name')
        self.filename = file_spec.get('filename')
        self.save = file_spec.get('save')
        self.source_task = None

    def set_source_task(self, source_task):
        self.source_task = source_task

class SoftwareSource:
    def __init__(self, software_source_spec):
        # Software source is type Docker, but write this in such
        # a way that Modules Software Env Management could be supported
        # e.g. don't use a Docker image ID outside of this class
        self.type = software_source_spec.get('type')
        self.id = software_source_spec.get('id')

class Software:
    def __init__(self, software_spec):
        self.source = SoftwareSource(software_spec.get('source'))
        self.name = software_spec.get('name')
        self.user_params = software_spec.get('user_params')

class Resources:
    def __init__(self, resources_spec, resources_default):
        if resources_spec is None:
            memory = None
            cores = None
        else:
            memory = resources_spec.get('memory')
            cores = resources_spec.get('cores')
        if memory is None:
            memory = resources_default.get('memory')
        if cores is None:
            cores = resources_default.get('cores')

        self.memory = memory
        self.cores = cores

class Task:
    def __init__(self, task_spec, resources_default, software, files, pipeline_root):
        self.name = task_spec.get('name')
        self.task_root = os.path.join(pipeline_root, 'tasks', self.name)
        self.command = task_spec.get('command')
        self.resources = Resources(task_spec.get('resources'), resources_default)
        self.input_files = []
        if task_spec.get('input_files') is not None:
            for input_file in task_spec.get('input_files'):
                self.input_files.append(Helper.get_item_by_name(files, input_file.get('name')))
        self.output_files = []
        for output_file_spec in task_spec.get('output_files'):
            output_file = Helper.get_item_by_name(files, output_file_spec.get('name'))
            self.output_files.append(output_file)
            output_file.set_source_task(self)

    def prepare(self):
        os.makedirs(self.task_root)
#        self.write_input_filenames_to_env()
#        self.write_output_filenames_to_env()
#        self.parse_command()

#    def write_input_filenames_to_env(self):
#        if self.input_files is not None:
#            for input_file in self.input_files:
#                print input_file.path_and_filename

    def run(self):
        print self.command

class Pipeline:

    JSON_SCHEMA_FILE = './pipeline_schema.json'
    OUTPUT_ROOT_PREFIX = './'

    def __init__(self, jobspecfile):

        self._initialize_jobspec(jobspecfile)
        self._initialize_output_root()
        self._initialize_pipeline_components()

    def _initialize_pipeline_components(self):
        self._initialize_software()
        #TODO file_imports
#        self.file_imports = self._initialize_file_imports(self.jobspec.get('file_imports'))
        self._initialize_files()
        self._initialize_tasks()

        #TODO validate_pipeline
#        self._validate_pipeline()

    def _initialize_jobspec(self, jobspecfile):
        self.jobspecfile = jobspecfile
        self.jobspec = self._getjobspecfromfile(jobspecfile)
        self._validate_jobspec()

    def _getjobspecfromfile(self, jobspecfile):
        with open(jobspecfile) as fspec:
            try:
                jobspec = json.load(fspec)
            except Exception as e:
                raise ValidationError("Job specification is not a valid JSON: %s" %e)
        return jobspec

    def _validate_jobspec(self):
        jobschema = self._getjobschema()
        try:
            jsonschema.validate(self.jobspec, jobschema)
        except Exception as e:
            raise ValidationError("Job specification is not valid. It does not match the schema. %s" %e)

    def _getjobschema(self):        
        jobschemafile = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.JSON_SCHEMA_FILE)
        with open(jobschemafile) as fschema:
            try:
                jobschema = json.load(fschema)
            except Exception as e:
                raise ValidationError("Job schema is not a valid JSON: %s" %e)
        return jobschema

    def _initialize_output_root(self):
        self.output_root = os.path.join(self.OUTPUT_ROOT_PREFIX, self.get_pipeline_run_id())

    def get_pipeline_run_id(self):
        # First initialize pipeline_run_id if not already set
        if not hasattr(self, 'pipeline_run_id'):
            self._initialize_pipeline_run_id()
        if self.pipeline_run_id == None:
            self._initialize_pipeline_run_id()
        return self.pipeline_run_id

    def _initialize_pipeline_run_id(self):
        self.pipeline_run_id = uuid.uuid1().hex

    def _initialize_software(self):
        self.software = []
        for software_spec in self.jobspec.get('software'):
            self.software.append(Software(software_spec))

#    def _initialize_file_imports(self, file_import_specs):
#        self.file_imports = []
#        for file_import_spec in file_import_specs:
#            self.file_imports.append(FileImport(file_import_spec))

    def _initialize_files(self):
        # Files are declared either as 
        #   1) output_files under a task, or 
        #   2) as file_imports. 
        # All input_files under a task must point to one of the above.
        
        self.files = []
        for task_spec in self.jobspec.get('tasks'):
            if task_spec.get('output_files') is None:
                continue
            for output_file in task_spec.get('output_files'):
                self.files.append(File(output_file))

    def _initialize_tasks(self):
        self.tasks = []
        for task_spec in self.jobspec.get('tasks'):
            self.tasks.append(Task(
                task_spec,
                self.jobspec.get('resources_default'),
                self.software,
                self.files,
                self.output_root,
            ))

#    def _validate_pipeline(self):
#        pass

    def run(self):
        self.set_up()
        self.run_tasks()
        self.clean_up()

    def set_up(self):
        os.makedirs(self.output_root)
        shutil.copy(self.jobspecfile, os.path.join(self.output_root, 'job.json'))

    def run_tasks(self):
        for task in self.tasks:
            task.prepare()
            task.run()

    def clean_up(self):
        #TODO
        pass


if __name__=='__main__':
    parser = ArgumentParser("Run the pipeline described in the job specification JSON file")
    parser.add_argument("--jobspec", required=True)
    args = parser.parse_args()
    pipeline = Pipeline(jobspecfile = args.jobspec)
    pipeline.run()
