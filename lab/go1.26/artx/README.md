# ARTEX image comparison lab

## Prerequisites

Run commands from the repository root. Use Docker Compose, Python 3.10+, and free loopback ports `18787` and `18788`. The images are pinned by manifest digest in `compose.yaml`: the affected binary reports Go 1.26.3, and the control binary contains Go 1.26.10 build metadata. Start one profile at a time because each ARTEX image is large. The database password is a disposable local-lab value.

## Run

```bash
docker compose -f lab/go1.26/artx/compose.yaml --profile affected up -d
curl --noproxy '*' --retry 30 --retry-all-errors --retry-connrefused --retry-delay 1 --max-time 2 -fsS http://127.0.0.1:18787/api/health
python3 -u poc.py --profile affected
docker compose -f lab/go1.26/artx/compose.yaml --profile affected down -v

docker compose -f lab/go1.26/artx/compose.yaml --profile control up -d
curl --noproxy '*' --retry 30 --retry-all-errors --retry-connrefused --retry-delay 1 --max-time 2 -fsS http://127.0.0.1:18788/api/health
python3 -u poc.py --profile fixed_control
docker compose -f lab/go1.26/artx/compose.yaml --profile control down -v
```

The PoC talks only to the selected loopback HTTP route. Docker commands are operator setup and cleanup, separate from the PoC.

## Expected proof

The affected profile returns HTTP 200 and a fresh `PROOF: uid=0(root) gid=0(root)` line from the application response. The control profile sends the same request to the alternate build and reports HTTP 401 with `PASS:`. A connection failure, unexpected status, or absent identity output returns nonzero.

## Evidence

- [Run 1](../../../docs/evidence/affected-run1.txt) and [run 2](../../../docs/evidence/affected-run2.txt) were captured from fresh affected containers.
- [Fixed control](../../../docs/evidence/fixed-control.txt) records the same HTTP request rejected by the alternate image.
- [Affected VHS tape](../../../docs/demo/artex-affected.tape), [GIF](../../../docs/demo/artex-affected.gif), [MP4](../../../docs/demo/artex-affected.mp4), and [raw output](../../../docs/demo/artex-affected.txt) belong to one live take.
- [Control VHS tape](../../../docs/demo/artex-control.tape), [GIF](../../../docs/demo/artex-control.gif), [MP4](../../../docs/demo/artex-control.mp4), and [raw output](../../../docs/demo/artex-control.txt) belong to a separate live take.

## Scope and limits

This lab proves root command execution inside the affected container through the ordinary HTTP route. It does not demonstrate host compromise. `ruoji6/artex` is an unaffected image from a different lineage, not a documented vendor patch. The comparison supports only these pinned `linux/amd64` digests and the tested configuration.
