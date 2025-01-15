| SURVEY  |
|   | TYPE                   | NAME | LABEL::EN      | CHOICE_FILTER |
|   | select_one c1          | q1   | Are you good?  |               |
|   | select_one_external c1 | q2   | Where are you? | YES_NO=${q1}  |
|   | osm c1                 | q3   | Where exactly? |               |
| CHOICES |
|   | LIST_NAME | NAME | LABEL::EN  |
|   | c1        | n1-c | l1-c       |
|   | c1        | n2-c | l2-c       |
| SETTINGS | 
|   | FORM_TITLE | FORM_ID | DEFAULT_LANGUAGE |
|   | Yes or no  | YesNo   | EN               |
| EXTERNAL_CHOICES |
|   | LIST_NAME | NAME | LABEL | YES_NO |
|   | c1        | n1-e | l1-e  | yes    |
|   | c1        | n2-e | l2-e  | yes    |
| ENTITIES |
|   | DATASET | LABEL |
|   | e1      | l1    |
| OSM |
|   | LIST_NAME | NAME | LABEL |
|   | c1        | n1-o | l1-o  |
|   | c1        | n2-o | l2-o  |
