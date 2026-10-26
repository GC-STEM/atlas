# STEM ATLAS | Development Notes

## Table of Contents <!-- omit from toc -->

1. [GC-STEM Repositories](#gc-stem-repositories)
2. [STEM Computing Baseline](#stem-computing-baseline)
3. [Course Development Environment](#course-development-environment)
4. [CDE Automation Scripts](#cde-automation-scripts)

## GC-STEM Repositories

*Note.* All repositories are public during development.

### GC-STEM/.github

This **{{public | internal}}** repository contains the organization's default community health files, profile/README, and schemas. This is a reference repository only. Users should not fork, clone, or otherwise copy this repository. In fact, there is no need for users to interact with this repository directly.

*Note*. This repository's visibility setting must be set to the broadest visibility setting of other repositories in the organization--public if any organization repo is public or is org profile should be public; internal only if all organization repos are internal and the profile should not be public. Visibility should be set to public, at least until SSO/SAML is fully deployed.

**Visibility Recommendation**. Permanently **public** so org profile can serve networking and marketing purposes. In addition, public visibility required if ATLAS or any individual-course repositories are public.

### GC-STEM/atlas

This **public** (at least during dev) repository contains the ATLAS project, which includes the STEM Computing Baseline (SCB) and course development environment (CDE) automation scripts. All students and faculty in a course that use a GC-sTEM repository should clone this repository to access the common resources. Cloning this repository is only necessary once per device and can be reused throughout a program of study. Users can pull updates from this repository as needed by running `git pull`.

**Visibility Recommendation**. Permanently  **public** so all SNHU can easily access and utilize the ATLAS project resources. Public visibility also eliminates duplicate setup across courses, as well as reduces maintenance overhead. In addition, ATLAS can attract prospective students interested in STEM computing.

### GC-STEM/crs000-faculty

This **private** repository template serves as the foundation for creating course-specific repositories within GC-STEM, providing a standardized structure and essential resources. Maintainers use this template to generate individual `<course>-faculty` repositories.

### GC-STEM/\<course>-faculty

Individual course repositories for faculty created from the `GC-STEM/crs000-faculty` repository for specific courses. These **private** repositories contain all student-facing materials as well as faculty-only content in the `.faculty` directory. Faculty will clone this repository to access answer keys and instructor guides, using a dual-remote setup to pull official updates and save their own local work.

### GC-STEM/\<course>

Student-facing course repositories created automatically from their `GC-STEM/<course>-faculty` repository, less the faculty-only content. These **{{public | private}}** repositories contain student-facing course-specific materials and resources.

**Visibility Recommendation**. Initially **public** until until SSO/SAML is fully deployed, after which the visibility can be reassessed based on the organization's access control requirements. In addition, there might be limits on number of members in GitHub/Entra Teams that would require large courses to remain public (e.g., IT-140).

---

### GC-STEM/crs000

This private repository template serves as the foundation for creating new course-specific repositories within the GC-STEM organization, providing a standardized structure and essential resources. Students and faculty will not have access to this repository directly; it is used solely as a template for creating individual course repositories.

---

## STEM Computing Baseline

## Course Development Environment

## CDE Automation Scripts
