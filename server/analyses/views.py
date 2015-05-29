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

Returning a list of SessionRecipes that are ready to run:
    - Query for all SessionRecipes, filter out all those that have a SessionRun pointing to them
    - Can sort by submit datetime for queue

Returning a list of currently running SessionRecipes:
    - Query for all SessionRuns, filter out all those that point to SessionResults

Returning a list of SessionRecipes that completed successfully:
    - Query for all SessionResults, filter for SessionResult.status = done, get associated SessionRecipes

Returning a list of SessionRecipes that failed:
    - Query for all SessionResults, filter for SessionResult.status = failed, get associated SessionRecipes

Updating server with status of SessionRuns:
    - When a new SesssionRecipe is started, create a new SessionRun pointing to SessionRecipe
    - When a SessionRun is completed (successfully or not), create a new SessionResult pointing to SessionRecipe and point SessionRun to new SessionResult

Accepting an ImportRequest from a user:
    - User writes JSON specifying ImportRequest, which points to an ImportRecipe.
        - ImportRecipe specifies source Location and destination Location.
    - ImportRequest and ImportRecipe objects are created and added to the database.

Returning a list of files that need to be imported, and have not been attempted before:
    - Query for all ImportRecipes. Filter out all those that have ImportResults pointing to them.

Returning a list of failed Imports:
    - Query for all ImportResults. Filter for all those that have ImportResult.status = failed.

Method designs:
    - SessionRecipe.is_ready():
        - Return True if all Ingredients pointed to by input Bindings satisfy one of the following conditions:
            - Ingredient is a File, OR
            - Ingredient is a FileRecipe AND FileRecipe.is_cooked(), OR
            - Ingredient is a ImportRecipe AND ImportRecipe.is_imported()
        - Otherwise, return False
    - FileRecipe.is_cooked():
        - Returns True if there is a SessionResult pointing to this FileRecipe with SessionResult.status = done
        - Returns False otherwise
    - FileRecipe.get_cooked_file():
        - Return the File pointed to by the successful SessionResult->SessionRecipe->Session->Port pointing to this FileRecipe
        - If no such SessionResult, return None 
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

Running a SessionRecipe:
    - Get a SessionRecipe from the server that is ready to run
        - Server makes sure to include all Bindings
    - Tell server that this SessionRecipe is now currently running
        - Server creates a SessionRun pointing to SessionRecipe
    - For each Binding:
        - If Binding is a File, copy it to local filesystem from Location
        - If Binding is a FileImport, check if file has been imported by looking for a FileImportResult pointing to FileImport
            - If so, copy File from Location to local filesystem
            - If not, check if file is currently being imported by looking for a FileImportRequest pointing to FileImport
                - If not, create new FileImportRequest pointing to FileImport
        - If Binding is a FileRecipe, check if File has been created already by looking for a SessionResult pointing to it
            - If so, copy File from Location to local filesystem
            - If not, recursively resolve its SessionRecipe 
    - Construct DAG of Session dependencies and run Session(s) that have all dependencies resolved
    - Tell server that this SessionRecipe failed or succeeded
        - Server creates a SessionResult with appropriate SessionResult.status
        - Server points SessionResult to SessionRecipe and (if successful) resulting File
        - Server points SessionRun to SessionResult

Method designs:
    - FileImport.import_file():
        - Copy the File from remote Location to local Location
        - Add a new File entry
        - Add a new FileImportResult pointing to the new File and this FileImport
    - FileRecipe.run():
        - Run the SessionRecipe pointed to by this FileRecipe

Outstanding issues:
    - How to know whether a SessionRun is currently being processed by workers? How to detect failure? Important for list of Sessions that are ready to run; don't want to dispatch same Session multiple times.
"""


