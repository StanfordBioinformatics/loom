What is loom?
=============

Loom is a platform-independent tool to create, execute, track, and share workflows.

Why use Loom?
=============

Ease of use
-----------

Loom runs out-of-the-box locally or in the cloud.

Repeatable analysis
-------------------

Loom makes sure you can repeat your analysis months and years down the road after you've lost your notebook, your data analyst has found a new job, and your server has had a major OS version upgrade.

Loom uses Docker to reproduce your runtime environment, records file hashes to verify analysis inputs, and keeps fully reproducible records of your work.

Traceable results
-----------------

Loom remembers anything you ever run and can tell you exactly how each result was produced.

Portability between platforms
-----------------------------

Exactly the same workflow can be run on your laptop or on a public cloud service.

Open architecture
-----------------

Not only is Loom open source and free to use, it uses an inside-out architecture that minimizes lock-in and lets you easily share your work with other people.

- Write your results to a traditional filesystem or object store and browse them outside of Loom
- Publish your tools as Docker images
- Publish your workflows as simple, human-readable documents
- Collaborate by sharing your workflows and results between Loom servers
- Connect Loom to multiple file stores without creating redundant copies
- Efficient re-use of results for redundant analysis steps

How many times do you really need to run the same analysis on the same inputs? Loom knows which steps in your workflow have already been run and seamlessly integrates previous results with the current run, while still maintaining data provenance and traceability.

Graphical user interface
------------------------

While you may want to automate your analysis from the command line, a graphical user interface is useful for interactively browsing workflows and results.

Security and compliance
-----------------------

Loom is designed with clinical compliance in mind.

Who needs Loom?
===============

Loom is built for the kind of workflows that bioinformaticians run -- multi-step analyses with large data files passed between steps. But nothing about Loom is specific to bioinformatics.

Loom is scalable and supports individual analysts or large institutions.

Get started
===========

Check out our Getting Started Guide and give Loom a try.

http://loom.readthedocs.io/en/latest/installing.html

What is the current status?
===========================

Loom is under active development. To get involved, contact info@loomengine.org

Contributors
============

- Nathan Hammond
- Isaac Liao
