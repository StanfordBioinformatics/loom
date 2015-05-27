from django.shortcuts import render

# Create your views here.

""" 
Workflow 1: Run Request w/ a specific file, 1 session
Workflow 2: Run Request w/ a specific file, 2 sessions in serial
Workflow 3: Run Request w/ 2 sessions in parallel
Workflow 4: Run Request w/ file upload request

*** SERVER FUNCTIONS ***

Accepting a request from a user:
    - User writes JSON specifying a Request and any required objects that aren't in the database already
    - Validate Request:
        - Request must specify FileRecipe(s) of desired output file(s)
        - All referenced objects are either in the database or in the JSON
    - Add Request and all accompanying objects to database

Returning a list of RunRecipes that are ready to run:
    - Query for all Runs, filter out all those that have a Run pointing to them
    - Can sort by submit datetime for queue

Returning a list of currently running RunRecipes:
    - Query for all Runs, filter out all those that point to RunResults

Returning a list of RunRecipes that completed successfully:
    - Query for all RunResults, filter for RunResult.status = done, get associated RunRecipes

Returning a list of RunRecipes that failed:
    - Query for all RunResults, filter for RunResult.Status = failed, get associated RunRecipes

Updating server with status of Runs:
    - When a new RunRecipe is started, create a new Run pointing to RunRecipe
    - When a Run is completed (successfully or not), create a new RunResult pointing to RunRecipe and point Run to new RunResult

Accepting an ImportRequest from a user:
    - User writes JSON specifying ImportRequest, which points to an ImportRecipe.
        - ImportRecipe specifies source Location and destination Location.
    - ImportRequest and ImportRecipe objects are created and added to the database.

Returning a list of files that need to be imported, and have not been attempted before:
    - Query for all ImportRecipes. Filter out all those that have ImportResults pointing to them.

Returning a list of failed Imports:
    - Query for all ImportResults. Filter for all those that have ImportResult.status = failed.

Method designs:
    - RunRecipe.is_ready():
        - Return True if all Ingredients pointed to by input Bindings satisfy one of the following conditions:
            - Ingredient is a File, OR
            - Ingredient is a FileRecipe AND FileRecipe.is_cooked(), OR
            - Ingredient is a ImportRecipe AND ImportRecipe.is_imported()
        - Otherwise, return False
    - FileRecipe.is_cooked():
        - Returns True if there is a RunResult pointing to this FileRecipe with RunResult.status = done
        - Returns False otherwise
    - FileRecipe.get_cooked_file():
        - Return the File pointed to by the successful RunResult->RunRecipe->Session->Port pointing to this FileRecipe
        - If no such RunResult, return None 
    - ImportRecipe.is_imported():
        - Return True if there is an ImportResult pointing to this ImportRecipe with ImportResult.status = done
        - Return False otherwise
    - ImportRecipe.get_imported_file():
        - Return the File pointed to by the successful ImportResult pointing to this ImportRecipe
        - If no such ImportResult, return None

*** JOB RUNNER FUNCTIONS ***

Importing a file:
    - Get an ImportRecipe from the server that is ready to run
    - Tell server that this ImportRecipe is now currently running
        - Server creates an Import pointing to this ImportRecipe
    - Copy from ImportRecipe.source Location to ImportRecipe.destination Location
    - Tell server that this ImportRecipe failed or succeeded
        - Server creates an ImportResult with appropriate ImportResult.status
        - Server points ImportResult to ImportRecipe and (if successful) resulting File
        - Server points Import to ImportResult

Running a RunRecipe:
    - Get a RunRecipe from the server that is ready to run
        - Server makes sure to include all Bindings
    - Tell server that this RunRecipe is now currently running
        - Server creates a Run pointing to RunRecipe
    - For each Binding:
        - If Binding is a File, copy it to local filesystem from Location
        - If Binding is a FileImport, check if file has been imported by looking for a FileImportResult pointing to FileImport
            - If so, copy File from Location to local filesystem
            - If not, check if file is currently being imported by looking for a FileImportRequest pointing to FileImport
                - If not, create new FileImportRequest pointing to FileImport
        - If Binding is a FileRecipe, check if File has been created already by looking for a RunResult pointing to it
            - If so, copy File from Location to local filesystem
            - If not, recursively resolve its RunRecipe 
    - Construct DAG of Session dependencies and run Session(s) that have all dependencies resolved
    - Tell server that this RunRecipe failed or succeeded
        - Server creates a RunResult with appropriate RunResult.status
        - Server points RunResult to RunRecipe and (if successful) resulting File
        - Server points Run to RunResult

Method designs:
    - FileImport.import_file():
        - Copy the File from remote Location to local Location
        - Add a new File entry
        - Add a new FileImportResult pointing to the new File and this FileImport
    - FileRecipe.cook():
        - Run the RunRecipe pointed to by this FileRecipe

Outstanding issues:
    - How to know whether a Run is currently being processed by workers? How to detect failure? Important for list of Sessions that are ready to run; don't want to dispatch same Session multiple times.
"""


