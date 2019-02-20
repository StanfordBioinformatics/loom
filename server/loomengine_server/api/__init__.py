import django.db
from . import test

# Raise a helpful error if attempting to get a setting that is missing
def get_setting(SETTING, required=True):
    from django.conf import settings
    try:
        value = getattr(settings, SETTING)
    except AttributeError:
        if required:
            raise Exception('Setting "%s" is not set' % SETTING)
        else:
            return None
    if value is None and required:
        raise Exception('Setting "%s" is not set' % SETTING)
    return value

def get_storage_settings():
    return {
        'GCE_PROJECT': get_setting('GCE_PROJECT'),
    }

def match_and_update_by_uuid(unsaved_models, field, saved_models):
    for unsaved_model in unsaved_models:
        if not getattr(unsaved_model, field):
            continue
        uuid = getattr(unsaved_model, field).uuid
        match = filter(lambda m: m.uuid==uuid, saved_models)
        assert len(match) == 1, 'Failed to match object by UUID'
        setattr(unsaved_model, field, match[0])
    return unsaved_models

def reload_models(ModelClass, models):
    # bulk_create doesn't give PK's, so we have to reload the models.                    
    # We can look them up by uuid, which is also unique                                  
    uuids = [model.uuid for model in models]
    models = ModelClass.objects.filter(uuid__in=uuids)
    return models

def connect_data_nodes_to_parents(data_nodes, parent_child_relationships):
    params = []
    for parent_uuid, child_uuid in parent_child_relationships:
        child = filter(
            lambda r: r.uuid==child_uuid, data_nodes)[0]
        parent = filter(
            lambda r: r.uuid==parent_uuid, data_nodes)[0]
        params.append((child.id, parent.id))
    if params:
        case_statement = ' '.join(
            ['WHEN id=%s THEN %s' % pair for pair in params])
        id_list = ', '.join(['%s' % pair[0] for pair in params])
        sql = 'UPDATE api_datanode SET parent_id= CASE %s END WHERE id IN (%s)'\
                                                  % (case_statement, id_list)
        with django.db.connection.cursor() as cursor:
            cursor.execute(sql)
