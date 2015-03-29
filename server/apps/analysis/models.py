from django.db import models
import json

class _Immutable(models.Model):

    # _Immutable models are used to represent analysis or data objects.
    # They are defined by a JSON object, and their id is a hash of that JSON.
    #
    # Using immutable objects ensures that when an object is changed, old references
    # to that object are unchanged, as they point to the original rather than to the
    # updated object.
    #
    # This content-based id allows data to be passed between servers without
    # any need to track origin. It is uniquely identifiable by its content.
    #
    # parent/child relationships can be defined on the model but are redundant with the JSON.
    # They are needed to make look-ups fast, especially for retrieving a parent.

    _json = models.TextField(blank=False, null=False) #, validators=[ValidationHelper.validate_and_parse_json])
    _id = models.TextField(primary_key=True, blank=False, null=False)

    def save(self):
        # Ensures that ID and JSON do not get out of sync.
        self._json = self._clean_json(self._json)
        self._calculate_and_set_unique_id()
        self.full_clean() #This runs validators
        super(_Immutable, self).save()

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
        return json.dumps(data_obj, sort_keys=True)

    def _calculate_unique_id(self):
        data_json = self._json
        return hashlib.sha256(data_json).hexdigest()

    def _calculate_and_set_unique_id(self):
        self._id = self._calculate_unique_id()

    def _validate_unique_id(self):
        if self._id != self._calculate_unique_id():
            raise ValidationError('Content hash %s does not match the contents %s', (self._id, self.get_unique_id))

    def clean(self):        
        # This method validates the model as a whole, and is called by full_clean when the object is saved.
        # If children override this, they should call it as super(ChildClass, self).clean()                                                                                                                
        self._validate_unique_id()

class TestModel(_Immutable):
    pass

"""
class Pipeline(models.Model):

    pipeline_schema = schema.PipelineSchema

    data_json = models.TextField()

    @classmethod
    def find_or_create(cls, raw_data_json):
        
        data_json = cls._clean_and_sort_json(raw_data_json)
        #TODO
        return Pipeline(data_json=data_json)

    def has_results(self):
        #TODO
        return False

    @classmethod
    def _clean_and_sort_json(cls, pipeline_json):
        pipeline_data = json.loads(
            pipeline_json, 
            object_pairs_hook=collections.OrderedDict)
        cls._validate_data_json_with_links(pipeline_data)
        cls._resolve_links(pipeline_data)
        cls._apply_constants(pipeline_data)
        cls._strip_ids_and_comments(pipeline_data)
        cls._validate_data_json_with_no_links(pipeline_data)
        pipeline_json = json.dumps(pipeline_data, sort_keys=True, 
                                   indent=4, separators=(',', ': '))
        return data_json

    @classmethod
    def _validate_data_json_with_links(cls, data_json):
        jsonschema.validate(data_json, cls.pipeline_schema.WITH_LINKS)

    @classmethod
    def _validate_data_json_with_no_links(cls, data_json):
        jsonschema.validate(data_json, cls.pipeline_schema.NO_LINKS)

    @classmethod
    def _apply_constants(cls, pipeline_data):
        Substitution.apply_constants(pipeline_data)

    @classmethod
    def _resolve_links(cls, pipeline_data):
        Linker().resolve_links(pipeline_data)

    @classmethod
    def _strip_ids_and_comments(cls, pipeline_data):
        StripKeys.strip_keys(pipeline_data, ['id', 'comments'])

class PipelineRunRequest(models.Model):

    @classmethod
    def find_or_create(cls, pipeline):
        #TODO
        return PipelineRunRequest()

class PipelineResultsRequest(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    pipeline = models.ForeignKey(Pipeline)

    @classmethod
    def create_from_json(cls, raw_data_json):
        results_request=cls()
        results_request.pipeline = Pipeline.find_or_create(raw_data_json)
        results_request._get_results()
        results_request.save()

    def _get_results(self):
        if self.pipeline.has_results():
            self._return_results(pipeline.results)
        else:
            self._request_pipeline_run()
            self._send_receipt()

    def _request_pipeline_run(self):
        self.run_request = PipelineRunRequest.find_or_create(pipeline=self.pipeline)

    def _send_receipt(self):
        #TODO
        return
    
# A request comes in. JSON data is saved raw in PipelineRunRequest.
# Check for inputs. Error if we don't have them.
# Check for pipeline. Create it if it doesn't exist.
# Check for results. Return them if they exist.
# Create a PipelineRunRequest and link PipelineResultsRequest to it.
"""

"""

class Session(models.Model):
    comments = models.CharField()
#    session_resources = models.OneToOneField(SessionResources)

class LocalFile(models.Model):
    comments = models.CharField()
    name = models.CharField()
    path = models.CharField()

class Application(models.Model):
    comments = models.CharField()
    name = models.CharField()
    docker_image = models.CharField()

class LocalFile(models.Model):
    comments = models.CharField()
    name = models.CharField()
    path = models.CharField()

class ExternalFileLocation(models.Model):
    comments = models.CharField()
    path = models.CharField()

class Import(models.Model):
    comments = models.CharField()
    import_file = models.OneToOneField(LocalFile, related_name='import')
    source = models.OneToOneField(ExternalFileLocation)

class Export(models.Model):
    comments = models.CharField()
    export_file = models.OneToOneField(LocalFile, related_name='export')
    destination = models.OneToOneField(ExternalFileLocation)

class SessionResources(models.Model):
    comments = models.CharField()
    disk_space = models.CharField()
    memory = models.CharField()
    cores = models.PositiveIntegerField()

class TaskResources(models.Model):
    comments = models.CharField()
    memory = models.CharField()
    cores = models.PositiveIntegerField()



class _InputData(object):

    def _process_json(self, data_json):
        dirty_nested_data = json.loads(data_json)
        dirty_data = self._flatten(dirty_nested_data)
        data = self._clean(dirty_data)
        return data

    def _flatten(self, data):
        #TODO
        return data

    def _clean(self, data):
        #TODO
        return data


class Step(models.Model):
    comments = models.CharField()
    command = models.CharField()
    application = models.ForeignKey(Application)
    input_files = models.ManyToManyField(LocalFile, related_name = 'input_for_steps')
    output_files = models.ManyToManyField(LocalFile, related_name = 'output_from_step')
    resources = models.OneToOneField(TaskResources)
    session = models.ForeignKey(Session)


"""
