######################################
Tags and Labels
######################################

Tags and labels are metadata that can be applied to files, templates, and runs. They can be modified or deleted without affecting the target object.

Each tag is unique and can only identify one object of a given type. Labels are not unique, so the same label can be applied to many objects.

***************
Tags
***************

**Creating a tag**

A tag can be added to an existing object as follows:

::

   loom file tag add FILE_ID TAG
   loom template tag add TEMPLATE_ID TAG
   loom run tag add RUN_ID TAG

A tag can also be applied when each of these objects is created, as follows:

::

   loom file import myfile.dat --tag TAG
   loom template import mytemplate.yaml --tag TAG
   loom run start TEMPLATE_ID [INPUT1=VALUE1 [INPUT2=VALUE2 ...]] --tag TAG

Multiple tags can be added at once by repeating the ``--tag`` flag:

::

   loom file import myfile.dat --tag TAG1 --tag TAG2
   loom template import mytemplate.yaml --tag TAG1 --tag TAG2
   loom run start TEMPLATE_ID [INPUT1=VALUE1 [INPUT2=VALUE2 ...]] --tag TAG1 --tag TAG2
   
**Viewing tags**

To view existing tags on all objects of a given type, use one of these commands:

::

   loom file tag list
   loom template tag list
   loom run tag list

To view existing tags on a specific object, use one of these commands:

::
   
   loom file tag list FILE_ID
   loom template tag list TEMPLATE_ID
   loom run tag list RUN_ID

**Referencing an object by its tag**

Just like hashes and UUIDs, tags can be appended to a reference ID string, preceeded by the ":" symbol. The tag name can also be used alone as reference ID. These two statements should return the same file, but the first command will fail if the file tagged as "NEWDATA" does not have UUID "74f5a659-9d03-422b-b5b7-3439465a2455" or filename "myfile.dat".

::
   
   loom file list myfile.dat@74f5a659-9d03-422b-b5b7-3439465a2455:NEWDATA
   loom file list :NEWDATA

The same notation is used for tagged runs and templates.

**Removing a tag**

A tag can be removed with the following commands:

::
   
   loom file tag remove FILE_ID TAG
   loom template tag remove TEMPLATE_ID TAG
   loom run tag remove RUN_ID TAG

Since the tag itself can be used as the reference ID, this command would be one valid way to remove a tag:

::
   
   loom file tag remove :TAG TAG

******
Labels
******

**Creating a label**

A label can be added to an existing object as follows:

::

   loom file label add FILE_ID LABEL
   loom template label add TEMPLATE_ID LABEL
   loom run label add RUN_ID LABEL

A label can also be applied when each of these objects is created, as follows:

::

   loom file import myfile.dat --label LABEL
   loom template import mytemplate.yaml --label LABEL
   loom run start TEMPLATE_ID [INPUT1=VALUE1 [INPUT2=VALUE2 ...]] --label LABEL

Multiple labels can be added at once by repeating the ``--label`` flag.

::

   loom file import myfile.dat --label LABEL1 --label LABEL2
   loom template import mytemplate.yaml --label LABEL1 --label LABEL2
   loom run start TEMPLATE_ID [INPUT1=VALUE1 [INPUT2=VALUE2 ...]] --label LABEL1 --label LABEL2

   
**Viewing labels**

To view existing labels on all objects of a given type, use one of these commands:

::

   loom file label list
   loom template label list
   loom run label list

To view existing labels on a specific object, use one of these commands:

::
   
   loom file label list FILE_ID
   loom template label list TEMPLATE_ID
   loom run label list RUN_ID

**Listing objects by label**

Unlike tags, labels cannot be used in refence ID strings since they are not unique. The ``--label`` flag can be used with a list statement to show all objects of the specified type with a given label:

::
   
   loom file list --label LABEL
   loom template list --label LABEL
   loom run list --label LABEL

If a reference ID is given along with the ``--label`` flag, the object will be shown only if it matches the given label.

::
   
   loom file list --label LABEL FILE_ID
   loom template list --label LABEL TEMPLATE_ID
   loom run list --label LABEL RUN_ID

Multiple ``--label`` flags are allowed. Only objects that match ALL specified labels will be shown.

::

   loom file list --label LABEL1 --label LABEL2
   loom template list --label LABEL1 --label LABEL2
   loom run list --label LABEL1 --label LABEL2

**Removing a label**

A label can be removed with the following commands:

::
   
   loom file label remove FILE_ID LABEL
   loom template label remove TEMPLATE_ID LABEL
   loom run label remove RUN_ID LABEL
