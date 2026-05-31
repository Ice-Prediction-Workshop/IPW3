# GitHub Submission Instructions

This document describes how to upload IPW3 results to GitHub using the web interface. This guide was adapted from the HLPW6 GitHub submission instructions. This procedure uses the GitHub web interface only. Participants who are familiar with Git, GitHub Desktop, or command-line workflows may use those tools instead.

---

## Overview

For IPW3, results will be collected through GitHub. This approach allows participants to submit data in a standardized repository structure and allows the organizers to review, process, and compare submissions more efficiently.

This guide assumes that:

- You already have a GitHub account.
- You are submitting files through the GitHub web interface.
- Alternative workflows, such as command-line Git or GitHub Desktop, may also be used by participants who are familiar with them.

If you do not have a GitHub account, you can create one for free at GitHub.

---

## Accessing the organization

Navigate to the Ice Prediction Workshop GitHub organization.

<img src="figures/ORG_REPOS.png" alt="Ice Prediction Workshop organization page with the Repositories tab highlighted" width="900">

The organization page should display the available repositories. Open the IPW3 repository from the repository list.

<img src="figures/ALL_REPOS.png" alt="Repository list showing the IPW3 repository in the Ice Prediction Workshop organization" width="900">

If your name or organization is not listed and you wish to submit results, please contact the IPW3 organizers to obtain a participant ID.

---

## Repository structure

 The `000_TEMPLATE_SUBMISSION` folder contains the template files and folder structure that participants should copy and rename for their own submission.

---

## Creating your fork

A fork is a personal copy of the repository under your GitHub account. It allows you to prepare and upload your submission files without directly modifying the main workshop repository.

To create a fork:

1. Open the IPW3 submission repository.
2. Click the `Fork` button.
3. Create the fork under your GitHub account.
4. Add your assigned PID to the repository name.

<img src="figures/FORKING.png" alt="IPW3 repository page with the Fork button highlighted" width="900">

On the fork creation page, rename the fork using your assigned participant ID. For example:

```text
000_IPW3
```

<img src="figures/FORKING_DETAILS.png" alt="GitHub create fork page showing the repository name field with a participant ID prefix" width="900">

After creating the fork, GitHub will open your personal copy of the repository. You should see that the repository was forked from:

```text
Ice-Prediction-Workshop/IPW3
```

<img src="figures/REPO.png" alt="Newly created fork of the IPW3 repository showing it was forked from the Ice Prediction Workshop repository" width="900">

---

## Using your fork

After creating your fork, make sure you are working inside your own copy of the repository.

Important buttons on your fork page include:

- `Contribute`: used later to open a pull request and submit your data to the main repository.
- `Sync fork`: used to bring updates from the main repository into your fork.

<img src="figures/CONTRIBUTE_SYNC.png" alt="Forked IPW3 repository page showing the Contribute and Sync fork buttons" width="900">

When your fork contains changes that are not yet submitted to the main repository, GitHub will indicate that your branch is ahead of the original repository. Use `Contribute` and then `Open pull request` to submit your changes.

<img src="figures/FORK_AHEAD.png" alt="Forked IPW3 repository showing the Contribute menu and the Open pull request button" width="900">

---

## Creating your submission folder

GitHub does not provide a direct browser-based copy/paste operation for folders. The following workflow can be used through the web interface.

Participants should download `.zip` version of the repository from:

<img src="figures/DOWNLOAD_FOLDER.png" alt="Download the .zip version of the repository" width="900">

Participants should then copy the submission structure from the template folder:

```text
000_TEMPLATE_SUBMISSION
```

and create their own submission folder using the naming convention:

```text
PID_ORGNAME_SOLVERNAME
```

For example:

```text
010_POLIMO_CHAMPS
```

where:

- `PID` is the participant ID assigned by the IPW3 organizers.
- `ORGNAME` is the organization or affiliation.
- `SOLVERNAME` is the solver used to generate the results.

---

## Preparing submission files

The template submission folder contains the files that participants should fill in for each test case and grid level.

A typical submission structure is:

```text
PID_ORGNAME_SOLVERNAME/
├── TC_NACA0012_AE3932_D01/
├── TC_NACA0012_AE3933_D01/
├── TC_ONERAM6_D01/
└── gridConvergence.xlsx
```

The `gridConvergence.xlsx` file is used for all grid-convergence-related quantities. Participants should fill in the requested values without changing the sheet names, column order, row order, or file structure.

Each test-case folder contains Tecplot-formatted `.dat` files for cut data and ice-shape data. For each grid level, participants should provide files such as:

```text
TC_NACA0012_3932_L1_cutData_V1.dat
TC_NACA0012_3932_L1_finalIceShape_V1.dat
TC_NACA0012_3932_L2_cutData_V1.dat
TC_NACA0012_3932_L2_finalIceShape_V1.dat
TC_NACA0012_3932_L3_cutData_V1.dat
TC_NACA0012_3932_L3_finalIceShape_V1.dat
TC_NACA0012_3932_L4_cutData_V1.dat
TC_NACA0012_3932_L4_finalIceShape_V1.dat
```

The number of slices depends on the test case. For example, the NACA0012 cases use one spanwise slice, while the ONERA M6 case uses multiple spanwise slices. All required slices should be included as Tecplot zones inside the corresponding `.dat` files.

A helper script is provided in:

```text
HELPER_SCRIPTS/cutTool_ipw3.py
```

This script can be used to extract the required slice data and generate files following the expected IPW3 Tecplot format.

---

## Uploading submission files

After preparing your files locally, return to your submission repository inside your fork.

To upload files:

1. Navigate to the appropriate folder in your fork.
2. Click `Add file`.
3. Select `Upload files`.
4. Drag and drop the prepared folder.
5. Add a clear commit message.
6. Click `Commit changes`.

<img src="figures/ADD_FILE.png" alt="Forked IPW3 repository showing the Add file menu with Upload files option" width="900">

Upload the prepared files by dragging the folder into the upload area or by selecting them manually.

<img src="figures/UPLOADING.png" alt="GitHub upload page showing the drag-and-drop file upload area and commit message fields" width="900">

Your files are now uploaded to your fork of the repository.

You may repeat this process to upload files for additional test cases, grid levels, or datasets.

---

## Opening a pull request

Once all required files have been uploaded to your fork:

1. Navigate to the front page of your fork.
2. Click `Contribute`.
3. Click `Open pull request`.

<img src="figures/PR.png" alt="Forked IPW3 repository showing the Open pull request prompt after new commits" width="900">

On the pull request page:

1. Make sure the base repository is the main IPW3 repository.
2. Make sure the head repository is your fork.
3. Add a clear title.
4. Add a short description of the submission.
5. Click `Create pull request`.

<img src="figures/CREATING_PR.png" alt="GitHub pull request creation page showing base repository, head repository, title, and description fields" width="900">

This will notify the IPW3 organizers that your data files are ready for review.

---

## Updating or adding another submission

The same fork can be used for later submissions.

To submit additional data:

1. Sync your fork if the main repository has changed.
2. Add or update the relevant submission files.
3. Commit the changes to your fork.
4. Open a new pull request.

If a new dataset is needed, use the next sequential dataset identifier, for example:

```text
D02
```

Additional datasets should be used for meaningfully different submissions, such as:

- a different solver,
- a different mesh generation strategy,
- a different modeling approach,
- different icing conditions,
- a major change in numerical setup.

Changes in roughness height should remain in the same dataset folder when they correspond to the same solver, grid family, and modeling approach.

---

If you encounter issues during the submission process, please contact the IPW3 organizers.