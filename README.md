## Submission Details

Participants are requested to create one submission folder inside the IPW3 repository. The folder name should follow the structure:

```text
PID_ORGNAME_SOLVERNAME
```

For example:

```text
010_POLIMO_CHAMPS
```

where:

- `PID` is the participant ID assigned by the IPW3 organizers.
- `ORGNAME` is the participant organization or affiliation.
- `SOLVERNAME` is the solver used to generate the submitted results.


Participants should keep the internal folder structure unchanged unless an additional dataset is required.

## Dataset folders

Inside the participant submission folder, the template contains one dataset folder for each IPW3 test case:

```text
TC_NACA0012_AE3932_D01
TC_NACA0012_AE3933_D01
TC_ONERAM6_D01
```

Participants should use `D01` for their main submission.

If an additional dataset is needed, participants may add another dataset folder using the next sequential identifier:

```text
TC_NACA0012_AE3932_D02
TC_NACA0012_AE3933_D02
TC_ONERAM6_D02
```

Additional datasets should be used only for meaningfully different submissions, for example:

- a different solver,
- a different mesh generation strategy,
- different icing conditions,
- a major change in numerical setup.

Changes in roughness height should remain in the same dataset folder.

## Submission data

The `000_TEMPLATE_SUBMISSION` folder contains the template files that participants should use to prepare their IPW3 submissions. Participants should keep the internal folder structure unchanged.

The expected structure is:

```text
PID_ORGNAME_SOLVERNAME/
├── TC_NACA0012_AE3932_D01/
│   ├── TC_NACA0012_3932_L1_cutData_V1.dat
│   ├── TC_NACA0012_3932_L1_finalIceShape_V1.dat
│   ├── TC_NACA0012_3932_L2_cutData_V1.dat
│   ├── TC_NACA0012_3932_L2_finalIceShape_V1.dat
│   ├── TC_NACA0012_3932_L3_cutData_V1.dat
│   ├── TC_NACA0012_3932_L3_finalIceShape_V1.dat
│   ├── TC_NACA0012_3932_L4_cutData_V1.dat
│   └── TC_NACA0012_3932_L4_finalIceShape_V1.dat
├── TC_NACA0012_AE3933_D01/
├── TC_ONERAM6_D01/
└── gridConvergence_D01_V1.xlsx
```

The file `gridConvergence_D01_V1.xlsx` is used for all grid-convergence-related quantities. Participants should fill in the requested values without changing the column order, row order, sheet names, or file structure. This file is intended to support automated post-processing and comparison of integrated quantities such as aerodynamic coefficients, water mass, ice mass, and evaporated water mass.

Each test-case folder contains Tecplot-formatted `.dat` files for the submitted slice data. The number of slices depends on the test case.

A helper script, `cutTool_ipw3.py`, is provided in the `HELPER_SCRIPTS` folder. This script can be used to extract the required slice data and generate files following the expected IPW3 Tecplot format. See the `HELPER_SCRIPTS/README.md` file for usage instructions and examples.

For more details on how to prepare and submit your data, please consult `SUBMISSION_PROCEDURE`.