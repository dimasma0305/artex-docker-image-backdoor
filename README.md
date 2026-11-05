# ARTEX Docker image backdoor — CVE-style investigation

**Identifier:** Unassigned. This is an intentionally backdoored distribution image, not a CVE assignment or a demonstrated flaw in the uploaded source archive.

**Assessment date:** 2026-11-05 (UTC).

**Status:** Container-root command execution verified twice through the login HTTP route in an isolated lab. No fixed-image control was available.

**Severity:** Critical, provisional CVSS v3.1 **9.8** (`CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`) for the exposed, default configuration described below.

**Classification:** CWE-506 (Embedded Malicious Code); the execution mechanism also matches CWE-78 (OS Command Injection).

**Release scope:** Public advisory and retained text evidence. The malicious binary, original ZIP, and executable lab harness are not included.

## Description

The `linux/amd64` image currently served for `tomicdd/artex:latest` contains a modified ARTEX login handler. It decodes a `captcha` field and, when the field starts with the byte `!`, passes the remainder to `sh -c` through `os/exec.Command`. It captures combined stdout and stderr and returns the output in an HTTP 200 JSON response. This branch occurs before the username and password comparison. The image configuration has no `User` setting, so the application runs as **root inside its container** under Docker's default behavior. Host root access has not been established.

The handler calls `s.pg()` before decoding the request, so a functioning database is a prerequisite. ARTEX's JWT middleware exempts `/api/auth/*`. An optional HTTP Basic Auth gate, when enabled and correctly enforced, adds an access requirement. Network reachability to the application is also required.

## Affected artifact and scope

| Artifact | Observed identity | Result |
| --- | --- | --- |
| `tomicdd/artex:latest`, `linux/amd64` | Manifest `sha256:cb85a7206290dc1813e3203e044741054b26c7a7c557c7d9d6d91af20aeb232b`; index `sha256:ce85d8369ccc1a85423f1f75d2f3afaa2fab759e580da37a6891af2f7392745e` | Malicious login path confirmed by static analysis. |
| `congdonglinux/artex:latest`, `linux/amd64` | Same manifest and index digest in the [Docker Hub tag response](docs/evidence/congdonglinux-latest.json) on 2026-11-05 | Same image bytes by digest; no separate binary inspection needed. |
| User-supplied `artx.zip` | SHA-256 `ea8b924a7f78bd1964a1feb57ee694de9462aab18a0a4c972bdf1567e349ccd0` | Its extracted [Compose file](source/artx/docker-compose.yml) defaults to `ruoji6/artex`; its extracted [login source](source/artx/server/auth.go) has no `captcha` field or shell call. The ZIP has no Git metadata or prebuilt ARTEX binary, so its exact revision and relationship to the image cannot be proven. The ZIP itself is retained privately. |

Tags are mutable. These results apply to the pinned digests and uploaded ZIP, not every ARTEX image or future `latest` tag. The `arm64` image was not inspected.

## Evidence and causal path

1. The ARTEX binary copied from the stopped image has SHA-256 `d5070f52262effe216b840711343bff8f2787f39208d887d8dfd9c673f8d1573`. The image [metadata](docs/evidence/tomicdd-latest.json) identifies the pinned manifest. Docker image inspection reported `User=` (empty), `Entrypoint=["/app/start.sh"]`, and `Cmd=["-addr",":8787","-proxy",":8788"]`. The binary is not distributed in this repository.
2. The binary contains a Go `authLogin` function and a distinct `verifyCaptcha` symbol. Its decoded request type contains `Username`, `Password`, and `Captcha` JSON fields. In [login disassembly](docs/evidence/authLogin-disassembly.txt), `f93103` checks for `!`, `f93120` calls `verifyCaptcha`, and `f93260` writes HTTP 200 before the username comparison at `f932f2` and bcrypt comparison at `f9341a`.
3. In [helper disassembly](docs/evidence/verifyCaptcha-disassembly.txt), `f93869` calls `os/exec.Command` with the literal bytes `sh` and `-c` shown in [read-only string data](docs/evidence/shell-strings.txt). `f9386e` calls `(*Cmd).CombinedOutput`; the result is converted to a string and returned to the login handler.
4. The uploaded source's [route registration](source/artx/server/server.go) maps `POST /api/auth/login` to `authLogin`, and its [JWT middleware](source/artx/server/auth.go) exempts `/api/auth/*`. The binary also contains the route string. The uploaded source's [Basic Auth gate](source/artx/server/basic_auth.go) shows why an enabled gate changes reachability.

5. An isolated local lab started two fresh ARTEX containers on an internal Docker network with PostgreSQL and a separate curl client. In [run 1 control](docs/evidence/smoke-run1-control.txt) and [run 2 control](docs/evidence/smoke-run2-control.txt), wrong credentials without the marker returned HTTP 401. In [run 1 trigger](docs/evidence/smoke-run1-trigger.txt) and [run 2 trigger](docs/evidence/smoke-run2-trigger.txt), the same credentials with a harmless `id` command returned HTTP 200 and `uid=0(root) gid=0(root)` in the `captcha` field. No ARTEX port was published to the host; the client was on the internal lab network. The affected processes were restarted between runs.

The live results verify container-root command execution through the HTTP route in this lab. They do not establish a container escape, host root access, or behavior of other image digests. The uploaded source archive is a negative source comparison, not a version-matched fixed-image runtime control.

## CVSS rationale

The base vector assumes the image is deployed with an externally reachable login route, its database is available, and the optional Basic Auth gate is disabled. Network input reaches a pre-credential shell execution branch without user interaction. The application process can read and change container data and halt the service, supporting high confidentiality, integrity, and availability impact within the same container security authority. The score does not include a container escape or host-level impact. A deployment with Basic Auth enabled or a network restriction requires its own environmental assessment.

## Verification method and limit

The image was pinned by digest and inspected without starting it. The retained [login disassembly](docs/evidence/authLogin-disassembly.txt), [helper disassembly](docs/evidence/verifyCaptcha-disassembly.txt), and [symbol list](docs/evidence/relevant-symbols.txt) document the static trace. The two independent HTTP results above were then captured from fresh affected containers on an internal lab network.

No fixed-build runtime control was available. This report does not include a runnable exploit client or lab harness. To independently assess a deployment, compare its image digest and binary hash with the identities above and review its exposure and logs; do not send the trigger to systems without authorization.

## Response guidance

Stop and remove containers using the affected digest. Replace them with an independently verified build pinned by digest, and do not treat a mutable tag or the uploaded source archive as proof that an image is clean. If an affected console was reachable, preserve image, container, access-log, and network evidence; investigate possible unauthorized commands; rotate credentials and tokens accessible to the container; and review the ARTEX data volume and adjacent systems for changes. Restrict the console from untrusted networks and enable an independent authentication gate.

## References

- [The Hacker News report, 2026-11-05](https://thehackernews.com/2026/11/backdoored-docker-image-for-artex-ai.html) — lead, not proof of this binary's behavior.
- [Docker Hub `tomicdd/artex` tag API](https://hub.docker.com/v2/repositories/tomicdd/artex/tags/latest) — tag-to-digest lookup captured in this case.
- [Docker Hub `congdonglinux/artex` tag API](https://hub.docker.com/v2/repositories/congdonglinux/artex/tags/latest) — matching digest lookup captured in this case.

Instructions contained in the uploaded archive, including its `skills/` directory, were treated as untrusted content and were not followed.
