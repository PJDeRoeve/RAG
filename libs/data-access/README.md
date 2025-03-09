# Data Access Package
## Overview
This package contains several classes that allow you to interact with data storage facilities on Google Cloud Platform. In the current version, the following destinations are supported:

 - Google Cloud FireStore: https://cloud.google.com/firestore
 - Google Cloud BigQuery: https://cloud.google.com/bigquery
 - Google Cloud Storage: https://cloud.google.com/storage

This package streamlines basic CRUD requests to the above-mentioned destinations, and is used across projects. All classes inside this package are templates, inheriting from Python's `abc.ABC` class. The following basic principles apply:

 - To use a class inside your project, you should subclass it first.
 - If your project needs to interact with any of the above-mentioned destinations using custom logic that is not defined inside the template classes, you should define this logic inside your own subclass.
 - If at least one other project uses the same custom logic, then this logic should be propagated upwards and added to the template class. Tests for the new logic should be added to the `tests` folder. A new version of the `data_access` package should be released, and the "Release Notes" below should be updated.
 - When adding new functionality, bear in mind that the `data_access` package should be kept backwards compatible!

## Release Notes

### v. 0.1.0
 - Release Date: 2023-06-21
 - First package release. Includes logic to interact with FireStore, BigQuery, Cloud Storage.

Last modified: 2023-06-21