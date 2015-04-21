'''
database model definitions for an analysis
an analysis is of a pipeline with 1-n sessions which could be running in different environment.
a Session is of several analyzing steps
a Session own its own inputs/outputs which are shared by the analyzing steps within this session.
a File is a URL pointing to persistance location of the data, could be a file path or internet URL and etc

a database entry will be generated automatically by parsing json input, by calling jsonToClass
'''

import json
import copy
from django.db import models
from django.core import serializers
from datetime import datetime
from datetime import timedelta

class File(models.Model):
    fileid = models.CharField(primary_key=True, max_length=30)
    uri = models.CharField(max_length=256)
    remote_url = models.CharField(max_length=256)
    ownerid = models.IntegerField(default=0)
    access = models.IntegerField(default=755)
    # the following fields is reserved for microsoft Azure
    blob = models.CharField(max_length=256, default='')
    container = models.CharField(max_length=256, default='')
    account = models.CharField(max_length=256, default='')
    comment = models.CharField(max_length=256, default='')
    rw = models.CharField(max_length=256, default='r')
    def jsonToClass( self, aux ):
        self.fileid = aux['id']
        # change 'url' to 'local_path', ziliang Qian @April20.2015
        if 'local_path' in aux:
            self.uri= aux['local_path']
        if 'container' in aux:
            self.container = aux['container']
        # change 'blob' to 'blob_id', ziliang Qian @April20.2015
	if 'blob_id' in aux:
            self.blob = aux['blob_id']
        if 'account' in aux:
            self.account = aux['account']
        if 'comment' in aux:
            self.comment= aux['comment']

class Application(models.Model):
    applicationid = models.CharField(max_length=256, primary_key=True)
    docker_image = models.CharField(max_length=256, default='')
    def jsonToClass( self, aux ):
        self.applicationid = aux['id']
        if 'docker_image' in aux:
            self.docker_image = aux['docker_image']

class Resource(models.Model):
    resourceid = models.IntegerField(primary_key=True, default=0)
    diskspace = models.IntegerField(default=1000)
    memory = models.IntegerField(default=1000)
    cores = models.IntegerField(default=1)
    ownerid = models.IntegerField(default=0)
    access = models.IntegerField(default=755)
    comment = models.CharField(max_length=256, default='')
    def jsonToClass( self, aux ):
        self.resourceid = aux['id']
        self.diskspace = aux['disk_space']
        self.memory = aux['disk_space']
        self.cores = aux['cores']

class Step(models.Model):
    stepid = models.CharField(primary_key=True, max_length=256)
    stepname = models.CharField(max_length=30)
    cmd = models.CharField(max_length=256)
    application = models.CharField(max_length=256)
    comment = models.CharField(max_length=256, default='')
    access = models.IntegerField(default=755)
    def jsonToClass( self, aux ):
        self.stepid = aux['id']
        self.comment = aux['comment']
        self.cmd = aux['command']
        self.application = aux['application']
        

class Session(models.Model):
    sessionid = models.CharField(primary_key=True, max_length=256)
    sessionname = models.CharField(max_length=30)
    steps = models.ManyToManyField(Step, related_name = 'step_id')
    importfiles = models.ManyToManyField(File, related_name = 'infile_id')
    savefiles = models.ManyToManyField(File, related_name = 'outfile_id')
    resourceid = models.ForeignKey(Resource, null=True, blank=True)
    comment = models.CharField(max_length=256, default='')
    access = models.IntegerField(default=755)
    def jsonToClass( self, aux ):
        self.sessionid = aux['id']
        self.comment = aux['comment']
    

class Pipeline(models.Model):
    pipelineid = models.CharField(primary_key=True, max_length=256)
    pipelinename = models.CharField(max_length=30)
    sessionids = models.ManyToManyField(Session, related_name = "session_id")
    comment = models.CharField(max_length=256, default='')
    access = models.IntegerField(default=755)
    def jsonToClass( self, query ):
        # files
        file_dict = {'':''}
        if type(query["files"]) is list :
            #remote_file_location
            r_file_loc_dict = {'':''}
            if type(query["remote_file_locations"]) is list :
                for remote_file_entry in query["remote_file_locations"]:
                     r_file_loc_dict[remote_file_entry['id']] = remote_file_entry

            app_dict = {}
            for app_entry in query["applications"]:
                app = Application(applicationid=app_entry['id'], docker_image=app_entry['docker_image'])
                app.save()
                app_dict[app.applicationid] = app

            for file_entry in query["files"]:
                f = File(uri="", fileid="", ownerid=0, comment="")
                f.jsonToClass(file_entry)
                f.save()
                if 'import_from' in file_entry :
                    remote_file = r_file_loc_dict[file_entry['import_from']]
                    f.remote_url = remote_file['url']
                    f.rw = 'r'
                    f.save()
                if 'save_to' in file_entry :
                    remote_file = r_file_loc_dict[file_entry['save_to']]
                    f.blob = remote_file['blob_id']
                    f.account = remote_file['account']
                    f.container = remote_file['container']
                    f.comment = f.comment + "\n" + remote_file['comment']
                    f.rw = 'w'
                    f.save()
                    
                file_dict[file_entry["id"]]=f
            
            # steps
            step_dict = {'':''}
            if type(query["steps"]) is list :
                for step_entry in query["steps"]:
                     s = Step(stepid="")
                     s.jsonToClass( step_entry )
                     s.save()
                     step_dict[step_entry['id']] = s
            
            # sessions
            if type(query["sessions"]) is list :
                for session_entry in query["sessions"]:
                        s = Session(sessionid="", sessionname="", comment="")
                        s.jsonToClass( session_entry )
                        #init foreign keys
                        s.pipelineid = self
                        s.save()
                        for item in session_entry["input_file_ids"]:
                            s.importfiles.add(file_dict[item])
                        for item in session_entry["output_file_ids"]:
                            s.savefiles.add(file_dict[item])
                        for item in session_entry["step_ids"]:
                            s.steps.add(step_dict[item])
                        s.save()
                        self.save()
                        self.sessionids.add(s)


class Analysis(models.Model):
    analysisid = models.CharField(primary_key=True, max_length=256)
    pipelineid = models.ForeignKey(Pipeline, null=False)
    comment = models.CharField(max_length=256)
    ownerid = models.IntegerField(default=0)
    access = models.IntegerField(default=755)
    def prepareJSON(self):
        objs_4_runner = {}
        import_file_objs = []
        export_file_objs = []
        step_objs = []
        for session in self.pipelineid.sessionids.all():
            for file_entry in session.importfiles.all():
                obj_4_runner = {}
                obj_4_runner['input_file_id']=file_entry.fileid
                obj_4_runner['local_path']=file_entry.uri
                obj_4_runner['url']=file_entry.remote_url
                # reserved for Azure, import file do not have blob account
                #obj_4_runner['blob']=file_entry.blob
                #obj_4_runner['account']=file_entry.account
                #obj_4_runner['container']=file_entry.container
                import_file_objs.append(obj_4_runner)
            for file_entry in session.savefiles.all():
                obj_4_runner = {}
                obj_4_runner['output_file_id']=file_entry.fileid
                obj_4_runner['local_path']=file_entry.uri
                # reserved for Azure
                obj_4_runner['blob']=file_entry.blob
                obj_4_runner['account']=file_entry.account
                obj_4_runner['container']=file_entry.container
                export_file_objs.append(obj_4_runner)
            for step in session.steps.all():
                obj_4_runner = {}
                obj_4_runner['docker_image']=Application.objects.get(applicationid=step.application).docker_image
                obj_4_runner['command']=step.cmd
                step_objs.append(obj_4_runner)
        objs_4_runner['files']={'imports':import_file_objs,'exports':export_file_objs}
        objs_4_runner['steps']=step_objs
        return json.dumps(objs_4_runner)


class AnalysisStatus(models.Model):
    statusid = models.CharField(max_length=256, primary_key=True)
    analysis = models.ForeignKey(Analysis, null=True)
    server = models.CharField(max_length=256, default="localhost")
    starttime = models.DateTimeField(default=datetime.now())
    endtime = models.DateTimeField(default=datetime.now())
    retries = models.IntegerField(default=0)
    ramusage = models.IntegerField(default=0)
    coresusage = models.IntegerField(default=1)
    status = models.IntegerField(default=0) #0x0:new, 0x1:running, 0x2:done 
    msg = models.CharField(max_length=256)
    def updateStatus(self, query):
        if 'server' in query: 
            self.server = query['server']
        if 'starttime' in query: 
            self.starttime = query['starttime']
        if 'endtime' in query: 
            self.endtime = query['endtime']
        if 'retries' in query: 
            self.retries = query['retries']
        if 'ramusage' in query: 
            self.ramusage= query['ramusage']
        if 'coreusage' in query: 
            self.coresusage = query['coresusage']
        if 'msg' in query: 
            self.msg = query['msg']
        self.save()



