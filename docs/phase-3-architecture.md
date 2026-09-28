# Phase 3 Architecture

```text
Training Program
      |
      v
Enrollment -----> Attendance
      |
      v
Assessment -----> Assessment Result
      |
      v
Completion + Passed Requirements
      |
      v
Certificate ---------> Certificate Verification
      |
      +-----------------> Skill Evidence
      |
      +-----------------> Certification Career Event

Learner
   |
   +--> 3-month outcome check-in
   +--> 6-month outcome check-in
   +--> 12-month outcome check-in
   |
   v
Career Timeline
```

## Design rules

- Certificates use an internal UUID plus a separate human-readable certificate number.
- Public verification uses a random verification code and does not require APAAR ID.
- Raw APAAR IDs are never returned by Phase 3 certificate or outcome APIs.
- Certificate-derived proficiency is a secondary evidence signal and never overwrites a stronger learner proficiency score.
- Outcome check-ins are marked `SELF_REPORTED` until later employer or document verification is implemented.
- Phase 4 can attach employer verification to the same longitudinal outcome records without redesigning the learner identity model.
