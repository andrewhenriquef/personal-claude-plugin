---
name: document-pipelines
description: Write docs/pipelines.md, the guide to a project's quality checks, from the `pipelines` services that build-pipelines added to the compose file. The doc says what each check protects, how to set it up once, how to run one check, all checks, or only the changed files, which secrets and network each needs, and how local differs from CI. It ends with a machine-readable manifest that run-pipelines reads. Every command comes from the compose `x-pipelines` blocks, never invented. Re-runs replace only the managed sections and keep human notes. Calls build-pipelines first when no pipelines services exist. Use when the user asks to document the checks or pipelines, write the pipelines doc, or refresh it after the checks changed.
---

# Document Pipelines

Write one file that tells a developer, and `run-pipelines`, how to set up and run every quality check of the project.

The file is `docs/pipelines.md`. If the user names another path, use it, and say that `run-pipelines` must be told the same path.

This is the third skill of the `continuous-integration` family:

| Skill | Job |
|---|---|
| `scan-pipelines` | Inventory, drift, and gaps. Read-only |
| `build-pipelines` | One compose service per check, with an `x-pipelines` block |
| `document-pipelines` | This skill. Writes `docs/pipelines.md` from those services |
| `run-pipelines` | Runs the checks from `docs/pipelines.md`, on changed files by default |

## Why this process

1. **The compose file is the source of truth.** It is what runs. The doc describes it. A command in the doc that is not in the compose file is a command that does not work.
2. **Two readers.** A developer reads the guide. `run-pipelines` reads the manifest at the end. Both come from the same `x-pipelines` blocks, so they cannot disagree.
3. **Docs rot.** Markers around the generated sections let a re-run replace them and keep what people wrote by hand.

## When to use

- The user asks to document the checks or pipelines, or to write or refresh the pipelines doc.
- `build-pipelines` just changed the services.
- `run-pipelines` finds the doc missing or out of date with the compose file.

## When NOT to use

- The user wants to know what checks exist and no services are built yet, and does not want them built. Use `scan-pipelines`.
- The user wants the checks run. Use `run-pipelines`.

## Rules that never change

- **No invented commands.** Every command in the doc is copied from an `x-pipelines` block, or built from the fixed patterns in the template (`docker compose --profile pipelines run --rm <id> ...`). If a service has no `x-pipelines` block, it is not documented. List it in the report.
- **Secrets by name only.** Write the variable name and where to get it if the compose file or CI says. Never a value.
- **Replace only managed sections.** Text outside the `<!-- pipelines:... -->` markers belongs to people. Keep it as it is.
- **Do not edit the compose file, CI config, or tool configs.** If they look wrong, report it and suggest `build-pipelines`.
- **Do not edit README or CLAUDE.md.** Suggest a link in the report.
- **Do not commit** unless the user asks.

## Process

### Step 0: Find the services

1. Find the compose file: `compose.yaml`, `compose.yml`, `docker-compose.yaml`, `docker-compose.yml`, in that order.
2. Run `docker compose --profile pipelines config --no-interpolate --format json`. This gives the merged services, with anchors and `extends` resolved. `--no-interpolate` keeps `${VAR}` as written, so no secret value from the environment enters the output. If Docker is not available, read the YAML file and resolve anchors and `extends` by hand. Say so in the report.
3. Keep the services with `profiles` containing `pipelines` and an `x-pipelines` block.
4. **None found:** tell the user, then **Claude Code:** call `Skill(skill: "build-pipelines")`. **Cursor:** read and follow the `build-pipelines` skill's `SKILL.md` in full. Start again at step 1 when it is done. If the user declines the build, stop.

### Step 1: Read the existing doc

1. If the doc exists, read it.
2. Find the managed sections by their markers (see the template). Keep every line outside them.
3. If the doc exists with no markers, it was written by hand. Do not overwrite it. Ask the user: write to a new path, or add the managed sections at the end of the existing file.

### Step 2: Collect the facts

For each service, take from the merged config:

- `id`: the service name.
- From `x-pipelines`: `category`, `source`, `ci_version`, `blocking`, `full`, `changed`, `files`, `triggers`, `writes`, `requires`.
- Image or build (Dockerfile path), and the services it depends on.

Then add, by reading only:

- **What it protects:** one line per category. Use the "Protects against" column of the `scan-pipelines` catalog (`../scan-pipelines/references/catalog.md`).
- **Network:** from the "Network" notes in `../build-pipelines/references/tool-images.md`.
- **Local version:** from the image tag or the Dockerfile install line. Compare with `ci_version`.
- **CI-only checks:** read the CI config for checks with no service (for example CodeQL default setup, hosted SaaS checks). Name them in "Runs only in CI". Do not run `scan-pipelines` again for this. Read the CI files directly.

Do not run any check.

### Step 3: Write the doc

Read [references/doc-template.md](references/doc-template.md). Fill every managed section from Step 2, in the template order. Rules:

- Order checks by category group (code, tests, security, data, interfaces, hygiene, the same as the catalog), then by `id`.
- One section per check. Same fields in the same order every time.
- Commands in fenced `sh` blocks, copy-pasteable as they are.
- The manifest is YAML, inside its markers, and lists every documented check with exactly the `x-pipelines` fields plus `id`.
- Write `generated_from` with the compose file path and today's date. `run-pipelines` detects drift by comparing each manifest entry with the `x-pipelines` block of the same service, field by field.
- Short sentences. No marketing words. Present tense.

### Step 4: Verify

1. Every service with `profiles: [pipelines]` and `x-pipelines` has a check section and a manifest entry. No other ids appear.
2. Every command in the doc matches the `x-pipelines` block, character for character, after the `docker compose --profile pipelines run --rm <id>` prefix.
3. The manifest parses as YAML (`python3 -c "import sys,yaml; yaml.safe_load(sys.stdin)"` on the block, or `ruby -ryaml -e 'YAML.load($stdin.read)'`).
4. No secret values. Search the doc for the values of variables named in `requires` if they are set in the environment, and for long random strings.
5. Text outside the markers is unchanged (`git diff` on the doc shows changes only inside them).
6. Relative links resolve.

### Step 5: Report

```
## Pipelines documented: <doc path>

Checks documented: <N>. Runs only in CI: <N>. Not documented: <ids with no x-pipelines, or none>.

### Changes since the last doc (if it existed)
- added / removed / changed: <id>, <field>.

### Gaps found while writing
- <id>: <problem, for example ci_version differs from local, no changed-files support, needs network>.

### Suggestions (not applied)
- Link docs/pipelines.md from README and CLAUDE.md, so people and agents find it.
- <build-pipelines re-run for any compose problem found>.

### Next step
`run-pipelines` reads this doc and runs the checks on the changed files.
```

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The CI step uses a slightly different flag, I will document that one." | Document what the compose file runs. Report the difference as a gap. |
| "This check is obvious, I will add a command for it." | No `x-pipelines` block, no command. Suggest `build-pipelines`. |
| "The old doc has a typo outside the markers, I will fix it." | Human text is not yours. Mention it in the report. |
| "I will run the checks to show example output." | This skill does not run checks. |
| "The manifest repeats the guide, I will drop it." | `run-pipelines` reads it. Keep it. |

## Red flags

- A command in the doc that is not in an `x-pipelines` block.
- A manifest entry with no matching service, or a service with no manifest entry.
- A secret value anywhere in the doc.
- Changed lines outside the markers.
- Compose config read without `--no-interpolate`.
- A changed compose, CI, README, or CLAUDE.md file.

## Verification

- [ ] Services read from the merged compose config (or by hand, stated in the report).
- [ ] Every pipelines service is documented once, with a manifest entry.
- [ ] Commands match the `x-pipelines` blocks.
- [ ] Manifest parses as YAML and has `generated_from`.
- [ ] No secret values.
- [ ] Human text outside the markers is unchanged.
- [ ] Only the doc file was written.
