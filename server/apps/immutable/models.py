from django.db import models
from django.core.exceptions import ValidationError
import json
import hashlib
from jsonschema import validate

class _Immutable(models.Model):

    # Models that extend _Immutable are used to represent analysis or data objects.
    # They are defined by a JSON object, and their id is a hash of that JSON.
    #
    # Using immutable objects ensures that if an object is changed, old references
    # to that object are unchanged, as they point to the original rather than to the
    # updated object.
    #
    # Using a content-addressable id allows related objects to always maintain links
    # when passed between servers. For example if identical analysis is submitted to one server
    # today and another server tomorrow, the latter run could query connected servers and discover
    # the results even if their existance was unknown to the user.
    #
    # parent/child relationships can be defined on the model but are redundant with the JSON.
    # They are needed to make look-ups fast, especially for retrieving a parent.

    _json = models.TextField(blank=False, null=False) #, TODO validators=[ValidationHelper.validate_and_parse_json])
    _id = models.TextField(primary_key=True, blank=False, null=False)
    _jsonschema = 'schema not setted. will raise error if use this dummy string'

    def __init__(self, *args, **kwargs):
        super(_Immutable, self).__init__(*args, **kwargs)

    @classmethod
    def create(cls, data_json):
        data_obj = json.loads(data_json)
        o = cls(_json=data_json)
        for (key, value) in data_obj.iteritems():
            if isinstance(value, list):
                # ManyToOne relation
                pass
            elif isinstance(value, dict):
                # OneToOne relation
                related_cls = self.get_class_for_key(key)
                child = related_cls.create(value)
                setattr(o, key, child)
            else:
                # if o.'key' is set, and it does not match 'value', raise an error.
                setattr(o, key, value)
        
        # validate json schema
        validate(o._json, o._jsonschema)
        
        # Ensures that ID and JSON do not get out of sync.
        o._json = o._clean_json(o._json)
        o._calculate_and_set_unique_id()
        o.full_clean() #This runs validators
        
        return o

    def save(self):
        super(_Immutable, self).save()
        #raise Exception("can not edit an immutable object!")

    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(_id=id)

    @classmethod
    def _clean_json(cls, dirty_data_json):
        # Validate json, remove whitespace, and sort keys
        try:
            data_obj = json.loads(dirty_data_json)
        except ValueError:
            raise ValidationError("Invalid JSON could not be parsed. %s" % dirty_data_json)

        cleaned_json = json.dumps(data_obj, separators=(',',':'), sort_keys=True)
        return cleaned_json

    def _calculate_unique_id(self):
        data_json = self._json
        return hashlib.sha256(data_json).hexdigest()

    def _calculate_and_set_unique_id(self):
        self._id = self._calculate_unique_id()

    def _validate_unique_id(self):
        if self._id != self._calculate_unique_id():
            raise ValidationError('Content hash %s does not match the contents %s', (self._id))

    def clean(self):        
        # This method validates the model as a whole, and is called by full_clean when the object is saved.
        # If children override this, they should call it as super(ChildClass, self).clean()                                                                                                                
        self.validate_json_schema()
        self._validate_unique_id()

    def validate_json_schema(self):
        # TODO json schema validation
        pass

class FlatModel(_Immutable):
    validation_schema = '{"jsonschema definition goes": "here"}'
    field1 = models.CharField(max_length=256, default=' ')
    field2 = models.CharField(max_length=256, default=' ')

class ParentChildModel(_Immutable):
    _jsonschema = '{"properties":{"files":{"type":"array", "items":{"type":"string"}}}}'
    # a list of children
    # get_class_for_key has not been implemented, call create recursively to create objects
    @classmethod
    def create(cls, data_json):
        data_obj = json.loads(data_json)
        o = cls(_json=data_json)
        direct_children_ids = []
        if isinstance(data_obj, basestring):
            pass
        else:
            for (key, value) in data_obj.iteritems():
                if isinstance(value, list):
                    children = []
                    for entry in value:
                        child = ParentChildModel.create(json.dumps(entry))
                        direct_children_ids.append(child._id)
                        children.append(child)
                    setattr(o, key, children)
    
                elif isinstance(value, dict):
                    children = {}
                    for entry in value:
                        child = ParentChildModel.create(json.dumps(value[entry]))
                        direct_children_ids.append(child._id)
                        children[entry]=child
                    setattr(o, key, children)
                else:
                    setattr(o, key, value)
        
            # add deps into current json file
            # obj_json = json.loads(o._json)
            # obj_json['dependents'] = direct_children_ids
            # o._json=json.dumps(obj_json)

        # validate json schema
        try:
            validate(o._json, o._jsonschema)
        except:
            raise Exception("schema validation failed. schema = " + o._jsonschema + " / json = " +o._json)

        # clean-up and validate the json file
        o._json = o._clean_json(o._json)
        o._calculate_and_set_unique_id()
        o.full_clean()
        #super(_Immutable, o).save()
        return o

 
'''
class File(_Immutable):
    def __init__(self, *args, **kwargs):
        super(Step, self).__init__(*args, **kwargs)

    fileid = models.CharField(max_length=30)
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
        
        # strip id and save json plain-text
        del aux['id']
        self._json = json.dumps(aux)


class Application(_Immutable):
    def __init__(self, *args, **kwargs):
        super(Step, self).__init__(*args, **kwargs)

    applicationid = models.CharField(max_length=256)
    docker_image = models.CharField(max_length=256, default='')
    # hash the content of a file to keep identity, in case the path changes
    def jsonToClass( self, aux ):
        self.applicationid = aux['id']
        if 'docker_image' in aux:
            self.docker_image = aux['docker_image']
        
        # strip id and save json plain-text
        del aux['id']
        self._json = json.dumps(aux)

class Resource(_Immutable):
    resourceid = models.IntegerField(default=0)
    diskspace = models.IntegerField(default=1000)
    memory = models.IntegerField(default=1000)
    cores = models.IntegerField(default=1)
    ownerid = models.IntegerField(default=0)
    access = models.IntegerField(default=755)
    comment = models.CharField(max_length=256, default='')
    def jsonToClass( self, aux ):
        self.resourceid = aux['id']
        if 'disk_space' in aux:
            self.diskspace = aux['disk_space']
        if 'memory' in aux:
            self.memory = aux['memory']
        if 'cores' in aux:
            self.cores = aux['cores']

class Step(_Immutable):
    def __init__(self, *args, **kwargs):
        super(Step, self).__init__(*args, **kwargs)

    stepid = models.CharField(max_length=256)
    stepname = models.CharField(max_length=30)
    cmd = models.CharField(max_length=256)
    application = models.CharField(max_length=256)
    comment = models.CharField(max_length=256, default='')
    access = models.IntegerField(default=755)
    def jsonToClass( self, aux ):
        self.stepname = aux['id']
        if 'comment' in aux:
            self.comment = aux['comment']
        if 'command' in aux:
            self.cmd = aux['command']
        if 'application' in aux:
            self.application = aux['application']
        
        # a step depends on its applications
        dependents = []
        dependents.append(Application.objects.get(applicationid=self.application).application_content_hash)
        # strip id and save json plain-text
        del aux['id']
        self._json = json.dumps(aux)
        

class Session(_Immutable):
    def __init__(self, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)

    sessionid = models.CharField(max_length=256)
    sessionname = models.CharField(max_length=30)
    steps = models.ManyToManyField(Step, related_name = 'step_id')
    importfiles = models.ManyToManyField(File, related_name = 'infile_id')
    savefiles = models.ManyToManyField(File, related_name = 'outfile_id')
    resourceid = models.ForeignKey(Resource, null=True, blank=True)
    comment = models.CharField(max_length=256, default='')
    access = models.IntegerField(default=755)
    def jsonToClass( self, aux, prevous_session_hash_key ):
        self.sessionid = aux['id']
        if 'comment' in aux
            self.comment = aux['comment']
        # a session depends on steps
        dependents = []
        for step_id in aux['steps_ids']:
            dependents.append(Step.objects.get(stepid=step_id))
        # a session depends on previous session
        dependents.append(prevous_session_hash_key)
        # a session depends on the inputs
        for importfile in self.importfiles:
            dependents.append(File.objects.get(fileid=importfile).file_content_hash)
        # strip id and save json plain-text
        del aux['id']
        dependents.sort()
        aux['dependents'] = dependents
        self._json = json.dumps(aux)
        self.save() # call override save function to sync the id and content

class Pipeline(models.Model):
    def __init__(self, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)

    pipelineid = models.CharField(max_length=256)
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
                    if 'comment' in remote_file:
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
                # the save method will take care of the identity
                s.save()
                step_dict[step_entry['id']] = s
          
        # sessions
        session_ids = []
        prevous_session_hash_key = ''
        if type(query["sessions"]) is list :
            for session_entry in query["sessions"]:
                s = Session(sessionid="", sessionname="", comment="")
                s.jsonToClass( session_entry, prevous_session_hash_key )
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
                prevous_session_hash_key = s._id
                session_ids.append(s._id)

        # make unique ids
        # step 1, strip ids, already done during cascading
        # TODO, potential bug, need to remove foreign keys before hashing
        # step 2, collecting hash keys from direct dependents
        if 'id' in aux:
            del aux['id']
        # a pipeline dependents on all the sessions within the pipeline
        session_ids.sort()
        aux['dependent_sessions'] = session_ids
        self._json = json.dumps(aux)

class Analysis(_Immutable):
    analysisid = models.CharField(max_length=256)
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
    status = models.IntegerField(default=0) #0x0:new, 0x1:running, 0x2:done, 0x3, editing, 0x4, updated
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
        if 'status' in query: 
            self.status = query['status']
        self.save()

'''

