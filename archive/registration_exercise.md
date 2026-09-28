# Exercise 1 extension: registration

This optional exercise was removed from the timed Streamlit flow to leave more time for the animation activities. It can be used for independent practice after Exercise 1.

Your original model has registration before the nurse. Complete the receptionist setup and request with fewer hints. Assume `self.logger` already exists.

```python
self.receptionist = CLASS(
    self.env,
    COUNT_ARGUMENT=self.param.num_receptionists,
    logger=LOGGER,
    label="receptionist",
)

with self.receptionist.request(
    entity_id=ENTITY_ID,
    start_event="being_seen_by_receptionist",
    end_event="receptionist_visit_ends",
) as req:
    yield req
    # Existing registration calculation and timeout stay here.
```

Fill in `CLASS`, `COUNT_ARGUMENT`, `LOGGER`, and `ENTITY_ID`. Then decide where arrival and departure belong in the two-stage clinic: around each resource stage, one arrival before registration and one departure after the nurse, or only around registration?

<details>
<summary>Worked answer</summary>

```python
self.receptionist = VidigiStore(
    self.env,
    num_resources=self.param.num_receptionists,
    logger=self.logger,
    label="receptionist",
)

# Inside attend_clinic, before the existing registration work:
self.logger.log_arrival(entity_id=patient.id)
self.logger.log_queue(entity_id=patient.id, event="receptionist_wait_begins")
with self.receptionist.request(
    entity_id=patient.id,
    start_event="being_seen_by_receptionist",
    end_event="receptionist_visit_ends",
) as req:
    yield req
    # Existing registration calculation and timeout

# Nurse waiting and treatment follow here.
# Log departure once, after the nurse stage.
```

Use one arrival before registration and one departure after the nurse. Each resource stage has its own waiting and treatment events.

</details>
