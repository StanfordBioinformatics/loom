#!/bin/bash

DEST=~/loom_model_graphs
mkdir -p $DEST
echo "Creating plots in " $DEST

# Workflow models
export GRAPH_MODELS_INCLUDE_MODELS=Workflow,Step,RequestedEnvironment,RequestedDockerEnvironment,RequestedResourceSet,WorkflowInput,WorkflowOutput,StepInput,StepOutput

../master/manage.py graph_models -a -g -o $DEST/workflows.png

# DataObject models
export GRAPH_MODELS_INCLUDE_MODELS=DataObject,FileDataObject,DataObjectArray,FileContents,FileStorageLocation,ServerFileStorageLocation,GoogleCloudStorageLocation

../master/manage.py graph_models -a -g -o $DEST/dataobjects.png

# TaskDefinition models
export GRAPH_MODELS_INCLUDE_MODELS=TaskDefinition,TaskDefinitionInput,TaskDefinitionOutput,TaskDefinitionEnvironment,TaskDefinitionDockerEnvironment,DataObject

../master/manage.py graph_models -a -g -o $DEST/taskdefinitions.png


# WorkflowRun models
export GRAPH_MODELS_INCLUDE_MODELS=WorkflowRun,WorkflowRunInput,WorkflowRunOutput,StepRun,StepRunInput,StepRunOutput,TaskRun,TaskRunInput,TaskRunOutput,Channel,Subchannel,TaskDefinition,TaskDefinitionInput,TaskDefinitionOutput

../master/manage.py graph_models -a -g -o $DEST/workflowruns.png
