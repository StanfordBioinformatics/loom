from glob import glob
import os
from loomengine.worker.parsers import OutputParser


class BaseOutput(object):

    def __init__(self, output, runner):
        self.output = output
        self.connection = runner.connection
        self.filemanager = runner.filemanager
        self.settings = runner.settings
        self.runner = runner


class FileOutput(BaseOutput):

    def save(self):
        filename = self.output['source']['filename']
        file_path = os.path.join(
	    self.settings['WORKING_DIR'], filename)
        self.filemanager.import_result_file(self.output, file_path)
        

class FileListScatterOutput(BaseOutput):

    def save(self):
        filename_list = self.output['source']['filename']
        file_path_list = [
            os.path.join(
	        self.settings['WORKING_DIR'], filename)
            for filename in filename_list]
        self.filemanager.import_result_file_list(
            self.output, file_path_list)
        

class FileContentsOutput(BaseOutput):

    def save(self):
        filename = self.output['source']['filename']
        text = self._read_file(filename)
        self.output.update({'data': {'contents': text}})
	self.connection.update_task_attempt_output(
            self.output['uuid'],
            self.output)

    def _read_file(self, filename):
        file_path = os.path.join(
	    self.settings['WORKING_DIR'], filename)
        with open(file_path, 'r') as f:
            text = f.read()
        return text


class FileContentsScatterOutput(FileContentsOutput):

    def save(self):
        filename = self.output['source']['filename']
        parser = OutputParser(self.output)
        text = self._read_file(filename)
        contents_list = parser.parse(text)
        self.output.update({'data': {'contents': contents_list}})
	self.connection.update_task_attempt_output(
            self.output['uuid'],
            self.output)


class FileListContentsScatterOutput(FileContentsOutput):

    def save(self):
        filename_list = self.output['source']['filename']
        contents_list = []
        for filename in filename_list:
            file_path = os.path.join(
	        self.settings['WORKING_DIR'], filename)
            contents_list.append[self._read_file(file_path)]
        self.output.update({'data': {'contents': contents_list}})
        self.connection.update_task_attempt_output(
            self.output['uuid'],
            self.output)

        
class StreamOutput(BaseOutput):

    def save(self):
        stream = self.output['source']['stream']
        assert stream in ['stdout', 'stderr']
        if self.output['source']['stream'] == 'stdout':
            text = self._get_stdout()
        else:
            text = self._get_stderr()
        self.output.update({'data': {'contents': text}})
	self.connection.update_task_attempt_output(
            self.output['uuid'],
            self.output)

    def _get_stdout(self):
        return self.runner._get_stdout()

    def _get_stderr(self):
        return self.runner._get_stderr()


class StreamScatterOutput(StreamOutput):
    
    def save(self):
        parser = OutputParser(self.output)
        stream = self.output['source']['stream']
        assert stream in ['stdout', 'stderr']
        if self.output['source']['stream'] == 'stdout':
            text = self._get_stdout()
        else:
            text = self._get_stderr()
        parser = OutputParser(self.output)
        contents_list = parser.parse(text)
        self.output.update({'data': {'contents': contents_list}})
	self.connection.update_task_attempt_output(
            self.output['uuid'],
            self.output)

class GlobScatterOutput(BaseOutput):

    def save(self):
        globstring = self.output['source']['glob']
        file_path_list = glob(globstring)
        self.filemanager.import_result_file_list(
            output, file_path_list)


class GlobContentsScatterOutput(FileContentsOutput):

    def save(self):
        globstring = self.output['source']['glob']
        file_path_list = glob(globstring)
        contents_list = []
        for file_path in file_path_list:
            contents_list.append[self._read_file(file_path)]
        self.output.update({'data': {'contents': contents_list}})
	self.connection.update_task_attempt_output(
            self.output['uuid'],
            self.output)


def _get_output_info(output):
    assert 'type' in output, 'invalid output: "type" is missing'
    assert 'mode' in output, 'invalid output: "mode" is missing'
    assert 'source' in output, 'invalid output: "source" is missing'
    data_type = output['type']
    assert data_type in ['file', 'boolean', 'string', 'integer', 'float'], \
        'output has invalid type "%s"' % data_type
    mode = output['mode']
    assert mode in ['scatter', 'no_scatter'], \
        'output has invalid mode "%s"' % mode
    filename_source = output['source'].get('filename')
    glob_source = output['source'].get('glob')
    stream_source = output['source'].get('stream')
    assert sum([bool(filename_source), bool(glob_source), bool(stream_source)]) == 1, \
               'exactly one type of source is required: "%s"' % output['source']
    if glob_source:
        source_type = 'glob'
    elif stream_source:
        source_type = 'stream'
    elif filename_source:
        if isinstance(output['source'].get('filename'), list):
            source_type = 'file_list'
        else:
            source_type = 'filename'
    return (data_type, mode, source_type)

def TaskAttemptOutput(output, runner):
    """Returns the correct Output class for a given
    data type, source type, and scatter mode
    """

    (data_type, mode, source_type) = _get_output_info(output)

    if data_type == 'file':
        if mode == 'scatter':
            assert source_type in ['file_list', 'glob'], \
                'source type "%s" not allowed' % source_type
            if source_type == 'file-list':
                return FileListScatterOutput(output, runner)
            return GlobScatterOutput(output, runner)
        else:
            assert mode == 'no_scatter'
            assert source_type == 'filename', \
                'source type "%s" not allowed' % source_type
            return FileOutput(output, runner)
    else: # data_type is non-file
        if mode == 'scatter':
            assert source_type in ['filename', 'file-list', 'glob', 'stream'], \
                'source type "%s" not allowed' % source_type
            if source_type == 'filename':
                return FileContentsScatterOutput(output, runner)
            if source_type == 'file_list':
                return FileListContentsScatterOutput(output, runner)
            if source_type == 'glob':
                return GlobContentsScatterOutput(output, runner)
            assert source_type == 'stream'
            return StreamScatterOutput(output, runner)
        else:
            assert mode=='no_scatter'
            assert source_type in ['filename', 'stream'], \
                'source type "%s" not allowed' % source_type
            if source_type == 'filename':
                return FileContentsOutput(output, runner)
            assert source_type == 'stream'
            return StreamOutput(output, runner)
