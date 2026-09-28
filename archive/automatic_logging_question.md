# Exercise 1 extension: which events are logged automatically?

This question appeared in Part 3 before the activity was changed to focus on animation snapshots. It can be used for independent review of event logging.

Patient 7 arrives at minute 2 and immediately joins the nurse queue. The nurse becomes available at minute 5. Treatment lasts 4 minutes, then the patient leaves.

| Event | Time (minutes) |
| --- | ---: |
| `arrival` | 2 |
| `nurse_wait_begins` | 2 |
| `being_seen_by_nurse` | 5 |
| `nurse_treatment_ends` | 9 |
| `depart` | 9 |

**Question:** Which two events does the nurse store record automatically?

<details>
<summary>Worked answer</summary>

`being_seen_by_nurse` and `nurse_treatment_ends`. The store records when the patient obtains and releases a nurse. Arrival, waiting and departure need explicit logging calls.

</details>
