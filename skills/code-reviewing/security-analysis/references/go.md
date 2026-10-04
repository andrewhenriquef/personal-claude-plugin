# Go security review

Sinks to trace, with vulnerable and safe samples. A sink is a finding only when untrusted data reaches it and no control blocks the path. Judge the data, not the call. Add the project's own helpers when you find them in Step 2.

## SQL injection (A05)

```go
// Vulnerable: input becomes SQL text
q := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", name)
rows, err := db.Query(q)

// Safe: placeholder, driver sends the value separately
rows, err := db.Query("SELECT * FROM users WHERE name = $1", name)
```

Placeholders cannot hold identifiers. For `ORDER BY` or column names built from input, the safe form is an allowlist:

```go
var sortColumns = map[string]string{"name": "name", "created": "created_at"}

col, ok := sortColumns[req.Sort]
if !ok {
	return ErrBadSort
}
q := "SELECT * FROM users ORDER BY " + col
```

Also check ORM escape hatches (`gorm.Raw`, `Where` with a concatenated string, `sqlx` with `Sprintf`).

## Command injection (A05)

```go
// Vulnerable: shell parses the input
exec.Command("sh", "-c", "convert "+filename+" out.png")

// Safe: no shell, input is one argument
exec.Command("convert", "--", filename, "out.png")
```

Without a shell, input cannot add commands, but it can still add flags. A value that starts with `-` becomes an option. Check for `--` or a prefix check.

## Template injection and XSS (A05)

- `html/template` escapes by context. `text/template` does not. Report `text/template` used to write HTML.
- `template.HTML(x)`, `template.JS(x)`, `template.URL(x)` turn off escaping. Report them when `x` is attacker-controlled.
- Writing request data straight into `w.Write` or `fmt.Fprintf(w, ...)` with `Content-Type: text/html` is XSS.

## Path traversal (A01)

```go
// Vulnerable: Join does not stop ".."
p := filepath.Join(baseDir, userPath)
data, _ := os.ReadFile(p)

// Safe (Go 1.24+): the root cannot be escaped, including by symlinks
root, err := os.OpenRoot(baseDir)
if err != nil {
	return err
}
defer root.Close()
f, err := root.Open(userPath)
```

For older Go versions, clean the path, then check the prefix with a separator (`strings.HasPrefix(p, baseDir+string(os.PathSeparator))`) and consider symlinks. Also check `http.ServeFile` and `http.FileServer` over a wider directory than intended, and `archive/zip` or `archive/tar` entry names (zip slip).

## Authorization (A01)

- Query by ID alone returns another user's row: `WHERE id = $1`. Look for the owner or tenant in the condition: `WHERE id = $1 AND owner_id = $2`.
- A handler wired outside the auth middleware group. Compare it with its neighbors in the router.
- Role or user ID read from the request body or a header the client controls.
- Mass binding: `json.Unmarshal` into a struct that includes `Role`, `IsAdmin`, or `OwnerID`.

## Outbound requests and SSRF (A01)

- `http.Get(userURL)` with an attacker-controlled host or scheme.
- Safe design checks scheme, resolves the host, rejects private, loopback, and link-local addresses (`169.254.169.254`), and checks again at connect time. A check before the request is not enough, because of DNS rebinding and redirects. Look at `CheckRedirect` and a custom `DialContext`.

## Crypto and secrets (A04)

- `math/rand` for tokens, IDs, or password resets. Safe: `crypto/rand`.
- `tls.Config{InsecureSkipVerify: true}` outside tests.
- `md5` or `sha1` for passwords or signatures. Safe: `bcrypt`, `scrypt`, or `argon2`.
- Secret or MAC compared with `==` or `bytes.Equal`. Safe: `subtle.ConstantTimeCompare` or `hmac.Equal`.
- Static key or IV in `cipher.NewGCM` use, or a reused nonce.
- Keys, tokens, or passwords in source, fixtures, or `.env` files that are committed.

## Authentication (A07)

- JWT with `golang-jwt`: the key function must check the signing method.

```go
// Vulnerable: accepts any algorithm the token names
jwt.Parse(tok, func(t *jwt.Token) (any, error) { return key, nil })

// Safe: pin the method
jwt.Parse(tok, func(t *jwt.Token) (any, error) {
	if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
		return nil, fmt.Errorf("unexpected method %v", t.Header["alg"])
	}
	return key, nil
}, jwt.WithValidMethods([]string{"HS256"}))
```

- Cookies without `Secure`, `HttpOnly`, or `SameSite` for session tokens.
- No session rotation on login.

## Exceptional conditions (A10)

- `if err != nil { log; continue }` inside an authorization or validation step. The code fails open.
- Ignored error from a security call: `_ = verify(...)`, `ok, _ := check(...)`.
- Unrecovered `panic` in a goroutine, or `recover` that swallows the error and lets the request proceed.
- Error text with SQL, stack traces, or file paths returned to the client.

## Unsafe and deserialization (A08)

- `unsafe` and cgo handle memory by hand. Review them only where untrusted data reaches them.
- `encoding/gob` and `yaml.Unmarshal` into `interface{}` from untrusted input. Check what types the decoder can create.

## Tooling

Run only the tools the project already uses, or ask first.

- `gosec ./...` (security static analysis, candidates only)
- `govulncheck ./...` (known CVEs in dependencies that the code actually calls)
- `go vet ./...`
- `semgrep --config p/golang` if the project uses Semgrep
- `gitleaks detect` for secrets
