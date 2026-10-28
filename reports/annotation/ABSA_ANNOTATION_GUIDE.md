# Municipal ABSA Annotation Guide

## Purpose

Label the single dominant grievance aspect expressed by each NYC 311 resolution description. These labels are human ground truth for evaluating the domain-transfer ABSA model; do not infer a label from the model prediction.

## Allowed labels

- `Issue Correction`: the underlying problem was not fixed, remains unresolved, or should be reopened.
- `Response Time`: the complaint concerns delay, waiting, lateness, or slow response.
- `Status Updates`: the complaint concerns missing, confusing, inaccurate, or inadequate progress communication.
- `Work Quality`: the completed work was poor, incomplete, improper, or unsatisfactory.
- `Information Intake`: the complaint concerns incorrect or incomplete information attributed to the requester.
- `Other`: none of the five specific categories is supported by the text.

## Annotation rules

1. Label only what is explicitly supported by the text.
2. Choose one label, even when multiple aspects appear; select the primary grievance.
3. Do not use complaint type or borough to infer the label.
4. Treat generic administrative closure language as `Other` unless a specific grievance is stated.
5. Annotators should label independently before discussing disagreements.
6. Use `adjudicated_label` only after disagreements are reviewed.

## Required process

Two annotators independently complete `annotator_1_label` and `annotator_2_label`. A third reviewer or joint adjudication then completes `adjudicated_label`. Run the evaluation script only after all required labels are complete.
