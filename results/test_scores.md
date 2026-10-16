Scored on each test engine's last row (707 engines). The baseline always guesses the average RUL of the training rows (122.3 cycles).

| Dataset | Test engines | Model MAE | Model RMSE | Baseline MAE | Baseline RMSE |
|---|---|---|---|---|---|
| FD001 | 100 | 19.86 | 26.96 | 49.57 | 62.60 |
| FD002 | 259 | 21.40 | 29.79 | 57.33 | 67.71 |
| FD003 | 100 | 27.44 | 39.26 | 50.98 | 62.64 |
| FD004 | 248 | 28.43 | 40.24 | 54.64 | 65.21 |
| All | 707 | 24.50 | 34.84 | 54.39 | 65.43 |

Error by distance to failure, over every cycle of every test engine (104897 cycles), grouped by the true RUL. A positive average means the model predicted more remaining life than there was.

| True RUL (cycles) | Cycles | Model MAE | Average predicted − true |
|---|---|---|---|
| under 25 | 1662 | 9.53 | +7.84 |
| 25-50 | 4609 | 19.56 | +16.90 |
| 50-100 | 16341 | 31.15 | +25.12 |
| 100-150 | 27033 | 35.58 | +21.57 |
| 150-200 | 26271 | 34.12 | +3.11 |
| 200 and above | 28981 | 68.37 | -56.03 |
