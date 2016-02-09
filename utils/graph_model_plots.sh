#!/bin/bash

DEST=~/loom_model_graphs
mkdir -p $DEST
echo "Creating plots in " $DEST

# Workflow models
export GRAPH_MODELS_INCLUDE_MODELS=Workflow,Step,RequestEnvironment,RequestDockerImage,RequestResourceSet,RequestOutputPort,RequestInputPort,RequestDataBinding,RequestDataPipe,RequestDataBindingDestinationPortIdentifier,RequestDataPipeSourcePortIdentifier,RequestDataPipeDestinationPortIdentifier,DataObject

../loom/master/manage.py graph_models -a -g -o $DEST/workflows.png

# DataObject models
export GRAPH_MODELS_INCLUDE_MODELS=DataObject,File,FileArray,FileContents,FileStorageLocation,ServerFileStorageLocation,GoogleCloudStorageLocation

../loom/master/manage.py graph_models -a -g -o $DEST/dataobjects.png

# StepDefinition models
export GRAPH_MODELS_INCLUDE_MODELS=StepDefinition,StepDefinitionInputPort,StepDefinitionOutputPort,StepDefinitionEnvironment,StepDefinitionDockerImage,FileName,DataObject

../loom/master/manage.py graph_models -a -g -o $DEST/stepdefinitions.png

# StepRun models
export GRAPH_MODELS_INCLUDE_MODELS=StepRun,StepResult,StepRunInputPort,StepRunDataBinding,StepRunDataPipe,StepRunDataBindingDestinationPortIdentifier,StepRunDataPipeDestinationPortIdentifier,StepRunDataPipeSourcePortIdentifier

../loom/master/manage.py graph_models -a -g -o $DEST/stepruns.png
