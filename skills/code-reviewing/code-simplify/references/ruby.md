# Ruby simplification examples

## Clarity over cleverness

```ruby
# Unclear: dense ternary chain
label = new? ? "New" : updated? ? "Updated" : archived? ? "Archived" : "Active"

# Clear: one condition per line
def status_label
  return "New" if new?
  return "Updated" if updated?
  return "Archived" if archived?

  "Active"
end
```

## Manual array building

```ruby
# Before
active = []
users.each do |user|
  active << user if user.active?
end

# After
active = users.select(&:active?)
```

## Nested conditionals

```ruby
# Before
def process(data)
  if data
    if data.valid?
      if data.permitted?
        do_work(data)
      else
        raise PermissionError, "No permission"
      end
    else
      raise ArgumentError, "Invalid data"
    end
  else
    raise TypeError, "Data is nil"
  end
end

# After
def process(data)
  raise TypeError, "Data is nil" unless data
  raise ArgumentError, "Invalid data" unless data.valid?
  raise PermissionError, "No permission" unless data.permitted?

  do_work(data)
end
```

## Tooling

- Test: `bundle exec rspec` or `bin/rails test`, per project.
- Lint: `bundle exec rubocop`
- Autocorrect (Rule of 500): `rubocop -a` is safe. Do not use `-A` (unsafe, can change behavior) without review.

## Design lens

Samples for `philosophy-of-software-design.md` and `pragmatic-programmer.md`.

### Pass-through method

```ruby
# Before: adds a layer, no behavior
def find(id)
  repo.find(id)
end

# After: call repo.find(id) directly, or give #find a real job (cache, authz)
```

### Information leakage

```ruby
# Before: two classes know the key format
cache.write("user:#{id}", user)  # class A
cache.read("user:#{id}")         # class B

# After: one place owns the format
def self.user_key(id)
  "user:#{id}"
end
```

### Pull complexity down

```ruby
# Before: every caller picks a timeout
Client.new(timeout: 5, retries: 3)

# After: defaults inside, keyword arguments only when needed
class Client
  def initialize(timeout: 5, retries: 3)
    # ...
  end
end
Client.new
```

### Special case in a general module

```ruby
# Before: general renderer knows about one caller
def render(report, for_billing: false)
  # ...
end

# After: billing adds its own step
def render(report)
  # ...
end

def billing_summary(report)
  render(report) + billing_footer(report)
end
```
