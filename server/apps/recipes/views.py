from django.shortcuts import render

# Create your views here.

""" 
Workflow 1: Run Request w/ a specific file, 1 session
Workflow 2: Run Request w/ a specific file, 2 sessions in serial
Workflow 3: Run Request w/ 2 sessions in parallel
Workflow 4: Run Request w/ file upload request

Accepting a request from a user:
    - User writes JSON specifying a Request and any required objects that aren't in the database already
    - Validate Request:
        - Request must specify FileRecipe(s) of desired output file(s)
        - All referenced objects are either in the database or in the JSON
    - Add Request and all accompanying objects to database

Returning a list of RunRecipes that are ready to run:
    - Query for all Runs, filter out all those that have a Run pointing to them

Returning a list of currently running RunRecipes:
    - Query for all Runs, filter out all those that point to RunResults

Returning a list of RunRecipes that completed successfully:
    - Query for all RunRecipes, filter out all those that don't have RunResults pointing to them, filter for RunResult.status = done

Returning a list of RunRecipes that failed:
    - Query for all RunRecipes, filter out all those that don't have RunResults pointing to them, filter for RunResult.status = failed

Running a RunRecipe:
    - Check if RunRecipe has already completed successfully by looking for a RunResult pointing to RunRecipe
    - Get all Sessions and Bindings in the RunRecipe
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
    - Update server with status of Run

Updating server with status of Runs:
    - When a new RunRecipe is started, create a new Run pointing to RunRecipe
    - When a Run is completed (successfully or not), create a new RunResult pointing to RunRecipe and point Run to new RunResult

Accepting a FileImportRequest from a user:

Returning a list of files that need to be imported:

Required methods:
    - RunRecipe.is_ready():
        - For each Ingredient pointed to by input Bindings, return True if:
            - Ingredient is a File, OR
            - Ingredient is a FileRecipe AND FileRecipe.Cooked(), OR
            - Ingredient is a FileImport AND FileImport.Imported()
        - Otherwise, return False
    - FileRecipe.is_cooked():
        - Returns True if there is a RunResult pointing to this FileRecipe
        - Returns False otherwise
    - FileRecipe.get_cooked_file():
        - Return the File pointed to by the RunResult->RunRecipe->Session->Port pointing to this FileRecipe
        - If no such RunResult, return None 
    - FileImport.is_imported():
        - Return True if there is a FileImportResult pointing to this FileImport
        - Return False otherwise

Job runner responsibilities:
    - FileImport.import_file():
        - Copy the File from remote Location to local Location
        - Add a new File entry
        - Add a new FileImportResult pointing to the new File and this FileImport
    - FileRecipe.cook():
        - Run the RunRecipe pointed to by this FileRecipe

Outstanding issues:
    - How to know whether a Run is currently being processed by workers? How to detect failure? Important for list of Sessions that are ready to run; don't want to dispatch same Session multiple times.
    - What kinds of status can be stored in a Run object? "Ready", "running", "done"? "Failed"?
"""


