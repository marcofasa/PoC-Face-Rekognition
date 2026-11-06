# Security and data handling

This repository is a sanitized portfolio snapshot of an AWS integration experiment. It includes source code, policy examples, original vector artwork, documentation and tests with fabricated byte strings. It includes no portraits, camera recordings, identity documents, real session IDs, credentials, account identifiers, or original company presentations.

## Credentials and permissions

The script uses a local AWS `default` profile. Configure credentials outside the checkout and prefer temporary access. The IAM examples separate backend-style session and comparison actions from the capture client's streaming action. They are examples to review in your environment, not provisioned access controls.

Never include AWS credentials, access tokens, real session IDs, private endpoints, or identity output in commits, issues, screenshots or terminal recordings. `.gitignore` reduces accidental additions; it does not inspect file contents or prevent forced additions. If a credential is exposed, revoke or rotate it before addressing Git history.

## Biometric data flow

The PoC reads a local portrait, receives reference-image bytes from Rekognition, opens the reference with Pillow, and sends portrait and reference bytes to Rekognition for comparison. The snapshot removes the original full-response print to avoid dumping image bytes and response metadata to terminal logs. It still prints session IDs and scores during live experiments, so terminal output is sensitive.

`Image.show()` may write temporary image files and invoke another application. Manage those files and the viewer's retention separately. The absence of application-managed S3 storage does not mean that no sensitive data leaves the machine or that AWS performs no service-side processing or retention.

## Scope and decisions

Use only images you are authorized to process. This experiment does not establish consent, implement retention or deletion workflows, bind sessions to authenticated users, calibrate thresholds, or evaluate demographic performance. It does not constitute a production identity system or evidence of regulatory compliance.

## Reporting an issue

Describe reproducible code or documentation issues without including credentials, portraits or real session output. For sensitive findings, use GitHub private vulnerability reporting if available for this repository, or another established private contact channel. Do not post sensitive evidence in public issues.
