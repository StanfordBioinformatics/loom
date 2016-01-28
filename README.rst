What is loom?
=============

Loom is a tool to create and execute bioinformatics workflows.

We observed that many bioinformaticians are doing analysis in a way that
is not repeatable or traceable, and that cannot be easily migrated to a
new compute environment. For example:

-  Depending on local software installations and environment settings
-  Executing commands manually
-  Failing to record analysis details and results in a database
-  Depending on file names and paths that may change and cannot be verified

Loom is designed as an easy-to-use analysis platform that remedies these
problems to make analysis repeatable, your results traceable, and your
workflows portable to other platforms.

Why use loom?
=============

Make your analysis pipelines portable
-------------------------------------

-  Loom uses Docker to make your pipelines platform-agnostic and to
   avoid using local software installations or environment settings
-  The same pipelines can be run in the cloud, on a local cluster, or on
   your laptop
-  Loom will seamlessly pull data from your local path, a remote file
   server, or an object store

Share your analysis and results
-------------------------------

-  Loom analyses and results are defined as JSON documents that can be
   easily shared by email
-  JSON documents defining analyses and results have the same meaning
   anywhere, with no dependencies on your software configuration, local
   environment settings, or file locations. External references to files
   or applications (Docker images) can always be verified using a
   cryptographic hash of contents

Keep your data secure
---------------------

-  Loom lets you run all your analysis with encryption of data in
   transit and at rest

Make sure your analysis is repeatable
-------------------------------------

-  The same features that make loom sharable help to ensure
   repeatability: input files are verified with a cryptographic hash,
   and applications are stored in Docker containers that can be verified
   by image ID
-  Analyses and results are recorded in a persistent database

Never lose track of how a result was generated
----------------------------------------------

-  When answering questions like “Where did this file come from?”, “What
   software version did we use to produce this result”, or “What
   settings did we use for this?”, you should never be scrambling
   through your notes or digging through output logs. Loom keeps track
   of result provenance and can tell you all the steps that were
   performed from import of the original input data to producing the
   final result.

What is the current status?
===========================

Loom is under active development. To get involved, contact
nhammond@stanford.edu

Contributors
============

-  Nathan Hammond
-  Isaac Liao
