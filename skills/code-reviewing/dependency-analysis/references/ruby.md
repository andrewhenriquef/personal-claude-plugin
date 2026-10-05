# Ruby and Rails dependency analysis

Commands, exposure mapping, and traps for `dependency-analysis`. The project's own policies and tool config win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

- `Gemfile`, `Gemfile.lock`, and for a gem or engine, `*.gemspec`.
- Gem groups in the `Gemfile` (`:development`, `:test`, `:production`, custom groups). A gem in only the development and test groups is **build and test**.
- The Ruby version: `.ruby-version`, `.tool-versions`, the `ruby` line in the `Gemfile`, and `RUBY_VERSION` in the Dockerfile or CI.
- The Rails version in `Gemfile.lock`, and whether the Rails series still gets security fixes. Look up the support dates. Do not rely on memory.
- Bundler config: `.bundle/config`, and `BUNDLE_*` variables in CI and Docker. Look for frozen or deployment mode.
- Lockfile checksums: a `CHECKSUMS` section in `Gemfile.lock` (Bundler 2.6 and later).
- Update bots and scanners: `.github/dependabot.yml`, `renovate.json`, a `bundler-audit` step in CI, `.bundler-audit.yml`, `brakeman` (app code, covered by `security-analysis`).
- Gem sources: `source` lines, `git:`, `github:`, `path:` options, and `source "..." do` blocks.

Run Ruby tools through Bundler (`bundle exec`) so the pinned versions load.

## Commands

All of these read only, except the update commands in the last table.

### Inventory and changes

| Goal | Command |
|---|---|
| What changed in the dependency files | `git diff main...HEAD -- Gemfile Gemfile.lock '*.gemspec'`, plus `git diff -- Gemfile Gemfile.lock` for uncommitted changes (use `master` if the repo has no `main`) |
| All installed gems | `bundle list` |
| Details of one gem (version, path, source) | `bundle info <gem>` |
| Outdated gems | `bundle outdated` (reads the registry, so it needs the network) |
| Outdated, only gems named in the `Gemfile` | `bundle outdated --only-explicit` |

Check the exact flags with `bundle outdated --help` on the installed Bundler.

### Chains: why is this gem here

| Goal | Command |
|---|---|
| Which gems depend on it (reverse dependencies) | `bundle exec gem dependency <gem> --reverse-dependencies` |
| What it depends on | `bundle exec gem dependency <gem>` |
| The Gemfile line that names it | `grep -n "<gem>" Gemfile` (no line means it is transitive) |

### Vulnerabilities

| Goal | Command |
|---|---|
| Check the lockfile, updating the advisory database first | `bundle exec bundle-audit check --update` |
| Check offline, with the cached database | `bundle exec bundle-audit check --no-update` |
| JSON output | `bundle exec bundle-audit check --format json` |

Notes:

- `bundler-audit` reads `Gemfile.lock` and the `ruby-advisory-db`. It reports vulnerable gem versions, and insecure sources that use `http://` or `git://`.
- `check --update` fetches the advisory database from the network. If it cannot connect, say so. Do not claim "clean".
- `bundler-audit` does not look at Ruby itself, the Rails app code, or whether the vulnerable method is used. Reachability is your job: map the exposure (below).
- The ignore list is `.bundler-audit.yml`. Read it, and report entries with no reason or no expiry. Do not add entries.

### Integrity

| Goal | How |
|---|---|
| Are checksums on? | Look for a `CHECKSUMS` section in `Gemfile.lock` |
| Do checksums match the change? | A version bump should change the checksum line of that gem. A checksum change with no version change is a red flag |
| Add checksums to a lockfile (changes the file, Fix mode or by request) | `bundle lock --add-checksums` |
| Frozen installs | Look for `BUNDLE_FROZEN` or `BUNDLE_DEPLOYMENT` in CI and Docker, or `bundle config set frozen true` |

Bundler verifies the `.gem` file against the recorded checksum before it installs, and refuses a mismatch. Bundler 4 includes checksums in new lockfiles by default. Existing lockfiles get them only on request.

### Update commands (Fix mode only)

| Goal | Command |
|---|---|
| Update one gem and as little else as possible | `bundle update --conservative <gem>` |
| Patch-level update for one gem | `bundle update --patch <gem>` |
| Then check what changed | `git diff Gemfile.lock` |
| Test after | the project's test command (`bundle exec rspec`, `bin/rails test`), then `bundle exec rubocop` |

Do not run a bare `bundle update`. It updates every gem. Check the flags with `bundle update --help` on the installed Bundler.

## Read a gem without running it

```
gem fetch <gem> -v <version>
gem unpack <gem>-<version>.gem --target <temp dir>
```

`gem fetch` downloads the `.gem` file. `gem unpack` extracts it. Neither runs the gem's code. Use a temporary directory outside the repository. Do not use `bundle install` or `gem install` for a gem you have not reviewed: gems with native extensions run `extconf.rb` at install, and that is arbitrary code.

Read: the gemspec (its `extensions`, `executables`, `post_install_message`, `dependencies`, and `metadata`), any `ext/` directory and `extconf.rb`, the files that run on `require`, and network, process, or file access. Check the gemspec metadata for `rubygems_mfa_required`: it shows whether the owner requires multi-factor sign-in to publish. Treat its absence as a small signal, not a finding.

## Exposure mapping

1. **Groups.** A gem only in `:development` or `:test` is **build and test**. The default group and `:production` gems load in production. `require: false` only delays the load. The gem still ships.
2. **Autoloaded gems.** `Bundler.require` loads every gem in the groups for the environment. A Rack middleware or a Rails engine gem can add itself to the request path at boot. Check `config/application.rb`, `config/initializers`, and `config.middleware`.
3. **Import sites.** `grep -rn "<ConstantName>\|require ['\"]<gem>" app lib config` finds explicit use. Sort by directory: `app/controllers`, `app/views`, `config/routes.rb`, middleware, and webhook handlers are **request path**. `app/jobs`, `app/services`, `lib/tasks`, and workers are **internal runtime**.
4. **Gems with no import site.** A gem that nothing references can be an indirect dependency, or an unused one. Check `bundle exec gem dependency <gem> --reverse-dependencies`.

## Ruby traps

- **Git, path, and branch sources.** `gem "x", git: "...", branch: "main"` follows a moving branch. The lockfile pins the commit in its `GIT` section, but the next `bundle update` moves it. A `path:` source works on one machine only. Check that production code does not depend on them. Prefer a tag or a `ref:`.
- **Insecure sources.** `source "http://..."` and `git://` URLs can be tampered with. `bundler-audit` reports them.
- **Multiple global sources.** More than one top-level `source` line lets a gem name resolve from any of them. This is the setup for dependency confusion. Private gems belong in a `source "..." do ... end` block, or in a `path:` or `git:` option.
- **Native extensions.** A new gem with `extensions` in its gemspec runs code at install. Review it as you would review code that runs in your build.
- **Loose constraints.** A bare `gem "x"` with a lockfile is normal for an application. An open range in a gemspec (`>= 1`) means every user resolves differently.
- **Tight pins.** `gem "x", "= 1.2.3"` or an upper cap (`< 2`) can block a security fix. Check why the pin exists.
- **Lockfile changes.** A `Gemfile.lock` with a different Bundler version in `BUNDLED WITH`, or new platforms (`PLATFORMS`), is usually harmless, but it explains diffs. A change in `CHECKSUMS` with no matching version change is not harmless.
- **Ruby and Rails support.** Look up the support status of the Ruby version and the Rails series. An unsupported Ruby or Rails gets no security fixes. This often blocks gem updates too, because newer gems drop old Ruby versions.
- **Rails and its parts.** `rails`, `actionpack`, `activerecord`, `activesupport`, `activestorage`, `actionmailer`, `railties`, and the other Rails gems should resolve to the same version. A mismatch is a problem.
- **Dev tools in production.** A development gem (`pry`, `web-console`, `better_errors`, `rack-mini-profiler`) that is in the default group runs in production. Report it.
- **Yanked gems.** A version that RubyGems yanked may still sit in the lockfile of a machine that cached it. Check that it still installs from the registry.

## Tests

After a fix, run the project's test command and `bundle exec rubocop` if the project uses it. Run `bundle exec bundle-audit check --update` again. Compare `Gemfile.lock` before and after with `git diff Gemfile.lock`.
