# XPPF

XPPF is a platform for creating and running analysis pipelines that can be easily executed in a variety of environments (local, HPC cluster, cloud) without any changes to the pipeline, while ensuring reproducibility of results.

It also provides a convenient means of exactly describing an analysis performed, the executables used, and the input files used, such that an analysis can be shared with others for review.

Direct access to the storage system for inputs and outputs is not required to run an analysis. Rather, data and analyses are published through a web interface. This allows XPPF to handle access controls and access logging, useful for regulatory compliance and for reducing the chance of accidental data loss from human error. 

Analysis records allows you to check provenance of each result, and built-in environment control and version management ensure reproducibility as long as the underlying applications are deterministic.

Runtime environment management is fully automated and reproducible, requiring no intervention from the pipeline operator.

The result is an extremely convenient way to develop pipelines that can be easily moved or shared, and that generate data in such a way that it can be easily tracked, queried, and shared.

## Feature highlights
### Data security 
* encrypted data transmission
* encrypted data storage
* user access management

### Traceability
* access logging
* analysis logs
* data provenance tracking

## Repeatability
* enforces consistency of processing environment and installed apps
* version management

## Portability/configurability
* processing may be configured as local, cloud, or job scheduler
* storage may be configured as local or cloud
* backend web server may be run locally or remotely, including cloud
* database may be MySQL or SQLite and can be local or remote, including cloud solutions
* the same pipeline can can be run on any of the above without modification, by changing the configuration

# Project status
XPPF is a work in progress. A working alpha version is expected September 2015.

# Get involved
XPPF is an open source project. If you share our vision of making analysis pipelines portable, repeatable, and verifiable, get involved! Contact nhammond@stanford.edu.

# Contributors
* Nathan Hammond
* Isaac Liao
* Ziliang Qian
