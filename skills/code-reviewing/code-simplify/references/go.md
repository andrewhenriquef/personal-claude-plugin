# Go simplification examples

## Clarity over cleverness

```go
// Unclear: logic hidden in one expression
ok := u != nil && (u.Admin || (u.Active && len(u.Roles) > 0 && u.Roles[0] != "guest"))

// Clear: named predicate
func canAccess(u *User) bool {
	if u == nil {
		return false
	}
	if u.Admin {
		return true
	}
	return u.Active && hasNonGuestRole(u) // len(u.Roles) > 0 && u.Roles[0] != "guest"
}
```

## Redundant boolean return

```go
// Before
func valid(s string) bool {
	if len(s) > 0 && len(s) < 100 {
		return true
	}
	return false
}

// After
func valid(s string) bool {
	return len(s) > 0 && len(s) < 100
}
```

## Nested success path

```go
// Before
func load(id string) (*User, error) {
	u, err := repo.Find(id)
	if err == nil {
		if u.Active {
			return u, nil
		} else {
			return nil, ErrInactive
		}
	}
	return nil, err
}

// After
func load(id string) (*User, error) {
	u, err := repo.Find(id)
	if err != nil {
		return nil, err
	}
	if !u.Active {
		return nil, ErrInactive
	}
	return u, nil
}
```

## Tooling

- Test: `go test ./...`
- Lint: `go vet ./...`, `golangci-lint run`, `gofmt -l .`
- Mechanical rewrites (Rule of 500): `gofmt -r 'pattern -> replacement'`, `gopls rename` for renames.

## Design lens

Samples for `philosophy-of-software-design.md` and `pragmatic-programmer.md`.

### Pass-through method

```go
// Before: adds a layer, no behavior
func (s *UserService) Find(id string) (*User, error) {
	return s.repo.Find(id)
}

// After: callers use the repo directly, or Find gets a real job (cache, authz)
user, err := repo.Find(id)
```

### Information leakage

```go
// Before: two packages know the key format
cache.Set("user:"+id, u)   // package a
cache.Get("user:" + id)    // package b

// After: one place owns the format
func userKey(id string) string { return "user:" + id }
```

### Pull complexity down

```go
// Before: every caller picks a timeout
func NewClient(timeout time.Duration, retries int) *Client

// After: sensible defaults inside, options only when needed
func NewClient(opts ...Option) *Client
```

### Special case in a general module

```go
// Before: general formatter knows about one caller
func Format(r Report, forBilling bool) string

// After: billing adds its own step
func Format(r Report) string
func billingSummary(r Report) string { return Format(r) + billingFooter(r) }
```
