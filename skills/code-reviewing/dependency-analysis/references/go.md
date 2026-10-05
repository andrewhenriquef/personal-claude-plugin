# Go dependency analysis

Commands, exposure mapping, and traps for `dependency-analysis`. The project's own policies and tool config win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

- `go.mod` (module path, `go` and `toolchain` directives, `require`, `replace`, `retract`, `exclude`, and in Go 1.24 and later `tool`) and `go.sum` (checksums).
- `go.work` and `go.work.sum` for a multi-module workspace. A `replace` in `go.work` applies to the workspace.
- A `vendor/` directory, and whether CI builds with `-mod=vendor`.
- Dev tools declared in a `tools.go` file with a `//go:build tools` tag, or with the `tool` directive. These are build-time dependencies.
- Update bots and scanners: `.github/dependabot.yml`, `renovate.json`, a `govulncheck` or `osv-scanner` step in CI, `osv-scanner.toml`.
- The Go version in `go.mod`, in the CI workflow, and in the Dockerfile base image. They can differ.
- Private modules: `GOPRIVATE`, `GONOSUMDB`, `GOPROXY`, and `GOFLAGS` in `Makefile`, CI, and `go env` settings.

## Commands

All of these read only, except the update commands in the last table.

### Inventory and changes

| Goal | Command |
|---|---|
| What changed in the dependency files | `git diff main...HEAD -- go.mod go.sum go.work`, plus `git diff -- go.mod go.sum` for uncommitted changes (use `master` if the repo has no `main`) |
| All modules in the build | `go list -m all` |
| Direct dependencies only | `go list -m -f '{{if not .Indirect}}{{.Path}} {{.Version}}{{end}}' all` |
| Outdated, deprecated, and retracted | `go list -m -u all` (an available update is in brackets, and the output marks `(deprecated)` and `(retracted)`) |
| The same, as JSON | `go list -m -u -json all` (fields `Deprecated`, `Retracted`, `Update`, `Replace`) |
| Unused or missing requirements (Go 1.23 and later) | `go mod tidy -diff` (prints what `tidy` would change and does not edit files) |

### Chains: why is this module here

| Goal | Command |
|---|---|
| The path from your code to a module | `go mod why -m <module>` |
| Which modules require it | `go mod graph \| grep <module>` (the lines are `parent child`) |
| Is a package linked into the binary | `go list -deps ./cmd/<name> \| grep <module path>` |

### Vulnerabilities

| Goal | Command |
|---|---|
| Call-graph scan of the source | `govulncheck ./...` |
| Scan a built binary | `govulncheck -mode=binary <path>` |
| More detail | `govulncheck -show verbose ./...` |
| Machine output | `govulncheck -format json ./...` |
| With OSV-Scanner, if the project has it | `osv-scanner scan -r .` |

Notes:

- `govulncheck` uses call-graph analysis. It reports **called** vulnerabilities with a call stack, and **imported but not called** ones as informational. Treat "called" as high priority. Treat "not called" as lower, not as safe.
- It reports standard-library vulnerabilities when the Go version in use is old. The fix is a Go version update, not a module update.
- It needs the vulnerability database from the network. If it cannot connect, say so. Do not claim "clean".
- Scan the packages that ship. A scan of `./...` also covers tests and tools.

### Integrity

| Goal | Command |
|---|---|
| Module cache matches `go.sum` | `go mod verify` |
| Fail when `go.mod` needs changes | `GOFLAGS=-mod=readonly` (the default since Go 1.16) |
| Module settings in effect | `go env GOPROXY GOSUMDB GOFLAGS GOPRIVATE GONOSUMDB` |

### Update commands (Fix mode only)

| Goal | Command |
|---|---|
| Update one module to an exact version | `go get <module>@v1.2.3` |
| Then clean up | `go mod tidy` |
| Patch updates for one module and its dependencies | `go get -u=patch <module>` |
| Build and test after | `go build ./... && go test ./... && go vet ./...` |

Do not run `go get -u ./...`. It updates everything to the latest minor or patch.

## Read a module without running it

```
go mod download -json <module>@<version>
```

The JSON gives the directory in the module cache, the checksum, and the origin. Read the files there. `go mod download` fetches and verifies but does not build or run the code. Check: the `go.mod` of the module (its own dependencies and its `go` directive), any `cgo` files (`import "C"`), `go:generate` lines (they run only when someone runs `go generate`), and `init()` functions that do network, process, or file work. Do not run `go generate`, `go run`, or `go test` inside the downloaded module.

## Exposure mapping

Go has no install scripts, and importing a package runs its `init()` functions at program start. A linked package runs with the program's rights.

1. Linked into the shipped binary: `go list -deps ./cmd/<name>` for each main package. A module whose packages appear here is **runtime**.
2. Linked only in tests: compare with `go list -deps -test ./...`. Packages that appear only with `-test` are **build and test**.
3. Build-time tools: modules in a `tools.go` file or a `tool` directive are **build and test**. They run on developer and CI machines.
4. For the runtime ones, find the import sites: `grep -rn '"<module path>' --include='*.go' .`. Sort them by directory: `cmd/`, `internal/http`, `handlers`, `middleware`, and workers are **request path** or **internal runtime**.

## Go traps

- **`replace` directives.** A `replace` to a fork, a local path, or a different module changes what code runs. Check why it exists, who owns the fork, and that it is not a leftover. A `replace` to a local path in a committed `go.mod` breaks other machines. A `replace` only applies in the main module, so the dependencies of your dependencies are not affected.
- **Pseudo-versions.** `v0.0.0-20240101000000-abcdef123456` pins an untagged commit. Ask why there is no release. Check that the commit is on the upstream default branch.
- **`go` directive bumps.** Updating a dependency can raise the `go` line (and add a `toolchain` line) in `go.mod`. That forces a newer Go for the whole project, CI, and Docker builds. Report it as a finding on its own.
- **Major versions are different paths.** `example.com/mod/v2` is another module from `example.com/mod`. A major update changes every import path. Both can appear in the build.
- **Retracted and deprecated.** `go list -m -u all` shows both. A retracted version should not be used. A deprecated module has a note that names the replacement.
- **Private modules and confusion.** Check that `GOPRIVATE` covers your internal module paths, so they never go to the public proxy or the public checksum database. A missing entry can leak module names, and a typo-squat on a public path can shadow an internal one.
- **Checksum database off.** `GONOSUMDB`, `GOFLAGS=-insecure`, `GONOSUMCHECK`, or `GOSUMDB=off` in committed config removes tamper detection. Report it.
- **`go.sum` changes.** A `go.sum` change with no `go.mod` change, or with extra lines for old versions, needs an explanation. Run `go mod tidy -diff` (Go 1.23 and later).
- **Vendoring.** If `vendor/` is committed, a scanner of `go.mod` can disagree with the vendored code. Check `vendor/modules.txt` against `go.mod`.
- **cgo.** Packages that use cgo link C libraries that `govulncheck` does not cover. Note it under "Not covered".
- **Base images.** The Go toolchain and OS packages in the Dockerfile have their own advisories. Note them under "Not covered" unless the user asks.

## Tests

After a fix, run the build and the project's test command. Run `govulncheck ./...` again. Compare the module list before and after with `go list -m all`.
