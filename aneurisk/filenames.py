#   Copyright (C) 2024, Iago L. de Oliveira. All rights reserved.
#   See LICENSE file for details.

#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.

import os
import pandas as pd
from typing import Union

dataDirName = "data"
refPointsFileName = "referencepoints.csv"
casesFileName = "cases.csv"
patientsFileName = "patients.csv"

def gen_case_label(case_id: int):

    return "C" + str(case_id).rjust(4, "0")

def _get_aneurisk_database_path():

    return os.path.abspath(
               os.path.join(
                   os.path.realpath(__file__),
                   "..",
                   ".."
               )
           )

def _get_multiple_ia_cases() -> dict:

    # I should write a list of the cases only, after wall the Aneurisk
    # repository won't change
    return {
               cid: [gen_case_label(cid) + "a",
                     gen_case_label(cid) + "b"]
               for cid in [28, 57, 74, 88]
           }

def _validate_case_label(case_label: Union[str,int]) -> str:

    if type(case_label) is int and case_label > 0 and case_label < 100:

        if case_label in _get_multiple_ia_cases().keys():
            raise ValueError(
                      "Case ID {} has multiple aneurysms."\
                      "Choose one of {}".format(
                          case_label,
                          _get_multiple_ia_cases()[case_label]
                      )
                  )

        else:
            return gen_case_label(case_label)

    elif type(case_label) is str:

        hasFourDigits = sum(c.isdigit() for c in case_label) == 4

        if case_label.startswith("C") and hasFourDigits:

            # Get case ID
            caseId = int("".join(d for d in case_label if d.isdigit()))

            if caseId > 0 and caseId < 100 and \
               caseId in _get_multiple_ia_cases().keys() and \
               not case_label in [label
                                  for list_ in _get_multiple_ia_cases().values()
                                  for label in list_]:

                raise ValueError(
                          "Case ID {} has multiple aneurysms."\
                          "Choose one of {}".format(
                              caseId,
                              _get_multiple_ia_cases()[caseId]
                          )
                      )

            else:
               return case_label

        else:
            raise ValueError(
                      "Wrong label format. Should be: 'C00__[a,b,..]' "\
                      "where the underline is an integer digit sequence."
                  )

    else:
        raise ValueError(
                  "Wrong label format. Should be: 'C00__[a,b,..]' "\
                  "where the underline is an integer digit sequence or "\
                  "an integer in the interval [1,99]."
              )

def path_to_vascular_model_file(
        case_id: Union[str, int]
    ) -> str:

    return os.path.join(
               _get_aneurisk_database_path(),
               "models",
               _validate_case_label(case_id),
               "surface",
               "model.vtp"
           )

def path_to_model_centerline_file(
        case_id: Union[str, int]
    ) -> str:

    return os.path.join(
               _get_aneurisk_database_path(),
               "models",
               _validate_case_label(case_id),
               "morphology",
               "centerlines.vtp"
           )

def path_to_cfd_model_file(
        case_id: Union[str, int]
    ) -> str:

    return os.path.join(
               _get_aneurisk_database_path(),
               "models",
               _validate_case_label(case_id),
               "surface",
               "model_cfd.stl"
           )

def path_to_healthy_model_file(
        case_id: Union[str, int]
    ) -> str:

    return os.path.join(
               _get_aneurisk_database_path(),
               "models",
               _validate_case_label(case_id),
               "surface",
               "model_healthy_vessel.vtp"
           )

def path_to_aneurysm_file(
        case_id: Union[str, int],
        mode: str
    ) -> str:

    return os.path.join(
               _get_aneurisk_database_path(),
               "models",
               _validate_case_label(case_id),
               "surface",
               "aneurysm_" + mode + ".vtp"
           )

def path_to_hull_file(
        case_id: Union[str, int],
        mode: str
    ) -> str:

    return os.path.join(
               _get_aneurisk_database_path(),
               "models",
               _validate_case_label(case_id),
               "surface",
               "hull_" + mode + ".vtp"
           )

def path_to_ostium_file(
        case_id: Union[str, int],
        mode: str
    ) -> str:

    return os.path.join(
               _get_aneurisk_database_path(),
               "models",
               _validate_case_label(case_id),
               "surface",
               "ostium_" + mode + ".vtp"
           )

def load_cases_data(
        cases_ids: list=None,
        between_ids: tuple=None
    ):
    """Pass range or list of cases to load data.

    If both cases and range are passed, the range will be ignored. If no cases
    are passed, return all cases.
    """

    cases = pd.read_csv(
                os.path.join(
                    _get_aneurisk_database_path(),
                    dataDirName,
                    casesFileName
                ),
                index_col="id"
            )

    # Load patients data too
    patients = pd.read_csv(
                   os.path.join(
                       _get_aneurisk_database_path(),
                       dataDirName,
                       patientsFileName
                   ),
                   index_col="id"
               )

    # Update code of lateral and terminal aneurysms
    cases["aneurysmType"].loc[
        cases.loc[:, "aneurysmType"] == "LAT"
    ] = "lateral"

    cases["aneurysmType"].loc[
        cases.loc[:, "aneurysmType"] == "TER"
    ] = "bifurcation"

    # Add sex and age of patient
    cases["sex"] = [patients.loc[pid, "sex"]
                    for pid in cases["patient_id"]]

    cases["age"] = [patients.loc[pid, "age"]
                    for pid in cases["patient_id"]]

    # Load reference points coordinates
    points = pd.read_csv(
                 os.path.join(
                     _get_aneurisk_database_path(),
                     dataDirName,
                     refPointsFileName
                 ),
                 index_col="id"
             )

    cases = pd.concat(
                [cases, points],
                axis=1
            )

    # Get series to identify case by integer (cases with 2 aneurysms get the
    # same index so they be included in the indexing)
    casesIds = cases.index.str.strip("Cab").astype(int)

    # Add numerical ID
    cases["numericalId"] = casesIds

    if cases_ids:
        # cases_ids = sorted(cases_ids)

        if min(cases_ids) < 1 or max(cases_ids) > 99:
            raise ValueError(
                  "Cases IDs should be between 1 and 99."
              )

        return cases.loc[casesIds.isin(cases_ids)]

    elif between_ids:
        minCase = min(between_ids)
        maxCase = max(between_ids)

        if minCase < 1 or maxCase > 99:
            raise ValueError(
                  "Range between 1 and 99."
              )

        return cases.loc[(casesIds >= minCase) & (casesIds <= maxCase)]

    else:
        return cases

def get_ref_bif_point(
        case_id: Union[str, int]
    ) -> tuple:

    casesData = load_cases_data()

    return tuple(
                casesData.loc[
                    _validate_case_label(case_id),
                    ["ICABifPoint0",
                     "ICABifPoint1",
                     "ICABifPoint2"]
                ]
            )

def get_dome_point(
        case_id: Union[str, int]
    ) -> tuple:

    casesData = load_cases_data()

    return tuple(
                casesData.loc[
                    _validate_case_label(case_id),
                    ["DomePoint0",
                     "DomePoint1",
                     "DomePoint2"]
                ]
            )
