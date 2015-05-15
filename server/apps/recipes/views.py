from django.shortcuts import render

# Create your views here.

""" General workflow
    - User writes JSON specifying a Request
    - Request must specify FileRecipe(s) of desired output file(s)
    - Recursively resolve each FileRecipe:
        - FileRecipe must specify the RunRecipe and the output Port of Session that generates the file
        - Server checks if this RunRecipe has already been run before by looking for a RunResult pointing to this RunRecipe
            - If so, return the File pointed to by RunResult
        - Prepare RunRecipe to run:
            - For each input Binding in RunRecipe:
                - If Binding is a File, go to next Binding
                - If Binding is a FileImport, check if file is imported
                    - If not, import it
                - If Binding is a FileRecipe, recurse 
        - Run the RunRecipe
            - Submit Session(s) and input Binding(s) to resource manager
            - After Session(s) are complete, add new RunResult and File(s) to database

Methods:
    - RunRecipe.Ready()
        - For each Ingredient pointed to by input Bindings, return True if:
            - Ingredient is a File, OR
            - Ingredient is a FileRecipe AND FileRecipe.Cooked(), OR
            - Ingredient is a FileImport AND FileImport.Imported()
        - Otherwise, return False
    - FileRecipe.Cook():
        - Run the RunRecipe pointed to by this FileRecipe
    - FileRecipe.Cooked():
        - Returns True if there is a RunResult pointing to this FileRecipe
        - Returns False otherwise
    - FileRecipe.GetCookedFile():
        - Return the File pointed to by the RunResult->RunRecipe->Session->Port pointing to this FileRecipe
        - If no such RunResult, return None or raise an exception
    - FileImport.Imported():
        - Return True if there is a FileImportResult pointing to this FileImport
        - Return False otherwise
    - FileImport.ImportFile():
        - Copy the File from remote Location to local Location
        - Add a new File entry
        - Add a new FileImportResult pointing to the new File and this FileImport
"""

""" Workflow 1: Run Request w/ a specific file, 1 session
"""

""" Workflow 2: Run Request w/ a specific file, 2 sessions in serial
"""

""" Workflow 3: Run Request w/ 2 sessions in parallel
"""

""" Workflow 4: Run Request w/ file upload request
"""
