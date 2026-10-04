# Ruby and Rails security review

Sinks to trace, with vulnerable and safe samples. A sink is a finding only when untrusted data reaches it and no control blocks the path. Judge the data, not the call. Rails protects by default in many places (parameterized `where` hashes, ERB escaping, CSRF tokens), so check for the escape hatch before you report. Add the project's own helpers when you find them in Step 2.

## SQL injection (A05)

```ruby
# Vulnerable: input becomes SQL text
User.where("name = '#{params[:name]}'")

# Safe: hash or placeholder
User.where(name: params[:name])
User.where("name = ?", params[:name])
```

Also check:

- `order(params[:sort])`, `group`, `pluck`, `select`, `joins` with a string from input. These take raw SQL. Safe: an allowlist of columns, or `order(Arel.sql(...))` only with a checked value.
- `find_by_sql`, `connection.execute`, `exists?("...#{}")`.
- `LIKE` patterns without `sanitize_sql_like`. This is a wildcard issue, usually low impact.

## Command execution and file access (A05)

```ruby
# Vulnerable: shell parses the input
system("convert #{params[:file]} out.png")
`convert #{params[:file]} out.png`

# Safe: array form, no shell
system("convert", "--", params[:file], "out.png")
```

- `Kernel#open(user_input)`, which runs a command when the string starts with `|`. Safe: `File.open`.
- `File.read`, `send_file`, `render file:` with a path from input. Check for `..`. Use `File.basename` or compare the expanded path with the base directory.
- `Tempfile`, uploads: file name from the client used as a path.

## XSS (A05)

- `html_safe`, `raw`, `<%==`, `safe_join` on attacker-controlled strings. ERB escapes everything else.
- `link_to name, params[:url]` allows `javascript:` URLs. Check the scheme.
- `render inline: params[...]`, `ERB.new(user_text).result`: template injection, usually remote code execution.
- Stimulus, Turbo, and `data-*` attributes built with `html_safe`.
- `sanitize` with a wide allowlist (`allowed_tags`, `allowed_attributes`) that adds `script`, `style`, or `on*`.

## Mass assignment (A01)

```ruby
# Vulnerable: attacker sets admin or role
params.require(:user).permit!
params.require(:user).permit(:name, :email, :admin)

# Safe: only fields the user may change
params.require(:user).permit(:name, :email)
```

Check nested attributes (`accepts_nested_attributes_for`) and `update(params)` without strong parameters. Check that role, owner, and tenant fields are not permitted.

## Authorization (A01)

```ruby
# Vulnerable: any user can read any record by ID (IDOR)
@invoice = Invoice.find(params[:id])

# Safe: scope through the owner
@invoice = current_user.invoices.find(params[:id])
```

- Controller actions without `authorize` / `policy_scope` when the neighbors have them. With Pundit, look for `verify_authorized` and `verify_policy_scoped` in `after_action`, and for `skip_authorization`.
- `before_action :authenticate_user!` with `only:` or `except:` lists that leave a new action open. Compare with new routes.
- Policy that checks the role but not the record (`user.admin? || true`, `record.present?`).
- Admin namespace without its own check.
- `skip_before_action`, `skip_forgery_protection`, `protect_from_forgery with: :null_session` on actions that change state.
- GraphQL and API serializers that return fields the caller should not see.

## Open redirect and unsafe dispatch (A01)

- `redirect_to params[:return_to]` sends users to any site. Safe: a path allowlist, or `allow_other_host: false` (default for new Rails 7+ apps through `raise_on_open_redirects`, so check the app's setting).
- `send`, `public_send`, `constantize`, `safe_constantize`, `Object.const_get`, `instance_variable_get` on a param. This reaches any method or class. Safe: map from allowed keys.

## Deserialization (A08)

- `Marshal.load` on data from a cookie, cache, queue, or user upload: code execution.
- `YAML.unsafe_load`, and `YAML.load` on old Ruby (before Psych 4, Ruby 3.1). On current Ruby `YAML.load` limits types, so check the Ruby version before you report. Safe: `YAML.safe_load` with a permitted-class list.
- `JSON.load` with `create_additions`, `Oj.load` in object mode.
- Signed or encrypted cookies: check that `secret_key_base` is not in the repo.

## Outbound requests and SSRF (A01)

- `Net::HTTP`, `Faraday`, `HTTParty`, `open-uri`, `URI.open` with a URL from input. Check scheme, host, and redirects. Block private, loopback, and link-local addresses after DNS resolution.
- Webhook and "import from URL" features are common sources.

## Crypto, secrets, and tokens (A04)

- `rand`, `Random.rand` for tokens or reset codes. Safe: `SecureRandom.hex`, `has_secure_token`.
- `Digest::MD5` or `SHA1` for passwords. Safe: `has_secure_password` (bcrypt).
- Token compared with `==`. Safe: `ActiveSupport::SecurityUtils.secure_compare`.
- Secrets in source, fixtures, `config/*.yml`, or `.env` committed. Safe: `Rails.application.credentials` or the environment.
- `verify_mode = OpenSSL::SSL::VERIFY_NONE`.
- Sensitive params missing from `config.filter_parameters` (logs hold passwords or tokens).

## Authentication (A07)

- Devise or custom login: no lockout or rate limit (`rack-attack`) on login, reset, or OTP.
- Reset token that is guessable, never expires, or is not cleared after use.
- Session not reset on login (`reset_session`), or cookie flags off in production (`secure`, `httponly`, `same_site`).
- JWT decode with `verify = false` or `algorithm: "none"`.

## Exceptional conditions (A10)

- `rescue => e` or `rescue Exception` around an authorization check, then continue. The code fails open.
- `rescue ... ; true` inside a `can?` or `authorized?` method.
- `Rails.env.production?` guards that leave debug pages or `config.consider_all_requests_local` on.
- Error responses with exception messages, SQL, or stack traces.

## Supply chain (A03)

- Gem added from a git source, a branch, or a path with no pin: `gem "x", git: "...", branch: "main"`.
- `Gemfile.lock` removed from the change, or bumped with no matching `Gemfile` change.
- CI workflow that runs `${{ github.event.* }}` input in a `run:` step.

## Tooling

Run only the tools the project already uses, or ask first.

- `bundle exec brakeman -q` (Rails security static analysis, candidates only)
- `bundle exec bundler-audit check --update` (known CVEs in gems)
- `bundle exec rubocop` (with `rubocop-rails` and `rubocop-security` if configured)
- `semgrep --config p/ruby` if the project uses Semgrep
- `gitleaks detect` for secrets
