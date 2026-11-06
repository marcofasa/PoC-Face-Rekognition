# Setup and troubleshooting

The default entry point is an interactive experiment. It creates a session, waits for an operator to complete an external camera challenge, and retrieves results once. Reading the source and running the mocked tests require no AWS access.

## Local installation

Use Python 3.11 for the validated baseline. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`. The remaining Python commands are the same.

`requirements.txt` pins direct and transitive dependencies for this snapshot. Re-evaluate dependency versions before reusing it in an active application.

## Live experiment prerequisites

1. An AWS account authorized to use Rekognition and a region supporting Face Liveness. Check the [current service endpoints](https://docs.aws.amazon.com/general/latest/gr/rekognition.html) rather than assuming every Rekognition region supports liveness.
2. A configured AWS CLI and a local **`default`** profile with a region and credentials. The script explicitly uses `boto3.Session(profile_name='default')`; it does not accept profile arguments or an `.env` file.
3. Permissions for the three operations in [script-policy.json](../iam/script-policy.json).
4. A separate camera application using a supported Face Liveness component, with permission to start streaming. Follow the [Amplify integration guide](https://ui.docs.amplify.aws/react/connected-components/liveness).
5. Your own authorized JPEG portrait saved locally as `photo.jpg` in the repository root. Use a single clear face. The file is intentionally excluded from Git.
6. A local desktop image viewer for Pillow's `Image.show()`.

Keep credentials in your AWS configuration outside the repository. Prefer an approved temporary credential or IAM Identity Center workflow. Boto3 documents its supported options in the [credentials guide](https://docs.aws.amazon.com/boto3/latest/guide/credentials.html). Match the profile name to the script and authenticate it before running.

Verify your profile locally:

```bash
aws sts get-caller-identity --profile default
aws configure get region --profile default
```

The first command can display account and identity details. Keep that output private. These commands are manual setup instructions and are not part of automated testing.

### IAM policy scope

`script-policy.json` allows only `CreateFaceLivenessSession`, `GetFaceLivenessSessionResults`, and `CompareFaces`. `capture-policy.json` separately allows `StartFaceLivenessSession` for the external capture client. The JSON files are permissions examples, not role trust policies or deployment templates.

These operations use `Resource: "*"` because they do not provide resource-level ARN scoping in the [Rekognition service authorization reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_rekognition.html). Keep the action list narrow and review any applicable organization policies and region conditions for your environment. No S3 or collection access is needed for this script's byte-based flow.

## Complete the interactive flow

```bash
python run.py
```

1. The script prints a newly created `SessionId` and waits at the Enter prompt.
2. Supply that ID to your separate capture client. Use the same AWS region and account context. Configure the client to use this existing session rather than creating a different one.
3. Complete the camera challenge and wait for the client's analysis-complete callback.
4. Return to the terminal and press Enter. The script fetches results, opens any returned reference image, and compares it with `photo.jpg`.
5. Inspect status, liveness confidence, and returned face matches. No application acceptance decision is made.

AWS specifies a three-minute expiry for session IDs and associated liveness data. Complete capture and result retrieval promptly; start a fresh session after expiry. See [CreateFaceLivenessSession](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_CreateFaceLivenessSession.html).

The script does not publish an API endpoint to transfer the ID or receive callbacks. That step is manual. Running it without an external capture client leaves the liveness process incomplete.

### Optional source-level controls

The existing `__main__` block exposes two variables for local experiments:

| Variable | Default | Effect |
| --- | --- | --- |
| `just_create_session_id` | `False` | Set to `True` to create a session and exit. |
| `session_id` | `None` | Supply an existing session locally to retrieve it after the Enter prompt. Never commit a real ID. |

For liveness-only inspection, `get_session_results(session_id, do_compare_faces=False)` skips comparison but still displays a returned reference image. Invoking this function requires importing `run`, which constructs an AWS client immediately.

## Known limitations

This snapshot preserves the original exploratory control flow. In particular:

- Result retrieval is a single request. It does not poll for completion or implement application retries.
- Confidence formatting assumes a numeric value. `CREATED`, `IN_PROGRESS`, failure responses or incomplete data can lack it and cause an exception.
- Comparison is attempted whenever reference bytes exist, without enforcing `SUCCEEDED` or a minimum liveness confidence.
- A missing portrait or invalid image raises an exception. There is no command-line input validation.
- `Image.show()` may create temporary files and open an external viewer. The script does not control viewer retention or work headlessly by default.
- The module constructs its AWS client on import. It requires local profile configuration outside the mocked tests.
- SDK exceptions propagate to the operator. The script has no application authentication, session-to-user binding, persistence, or business decision policy.

These constraints are reasons to evaluate the script as an integration PoC. They need explicit handling before it can support an application.

## Troubleshooting

| Symptom | Likely cause and action |
| --- | --- |
| `ProfileNotFound` | Configure and authenticate the `default` profile. |
| `NoRegionError` or unsupported operation | Set a supported liveness region in that profile and use the same region in the capture client. |
| `AccessDeniedException` | Check the relevant script or capture action, role permissions, permission boundaries and organization controls. |
| `CREATED` / `IN_PROGRESS`, or confidence formatting error | Finish the capture and wait for analysis before retrieving results. The script does not poll. |
| Expired or missing session | Create a new session and repeat the capture promptly. |
| `FileNotFoundError: photo.jpg` | Supply your own portrait at the expected local path, or use liveness-only inspection. |
| No comparison matches | No face exceeded the configured similarity threshold; this is not an authentication verdict. |
| No image window | Use a desktop environment with a configured image viewer. |

## Cleanup

Remove local portraits, close the viewer and review any temporary files it created. Delete any independently configured storage or deployed resources under your own retention policy. The script creates no S3 bucket, collection, database, or hosted compute resource. AWS processing and service-side handling remain subject to your AWS configuration and service terms.
