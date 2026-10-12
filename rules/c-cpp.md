# C and C++ Style

Applies to all C and C++ code written at MCS. Layout is enforced by
`config/.clang-format`, naming by `config/.clang-tidy`. Do not argue with the
formatter, run it.

## Layout

- 4 spaces, no tabs.
- Braces always on their own line (Allman): functions, `if`/`else`, loops,
  `switch`, `class`, `struct`, `enum`, `namespace`.
- Space between the name and `(` in function declarations and definitions:
  `int32_t readState (State *state)`.
- No space between the name and `(` in function calls: `readState(&state)`.
- Space after `if`, `for`, `while`, `switch`: `if (x)`.
- Spaces around binary operators: `a + b`, `x != y`.
- Pointer star and reference ampersand bind to the name: `int *x`,
  `const Foo &foo`.
- Every sub-expression in a condition is parenthesized:
  `if ((a != b) && (c < MAX))`.
- 100 columns at most.

## Naming

| Kind | Style | Example |
|---|---|---|
| Types (class, struct, enum) | PascalCase | `BatteryService` |
| Functions, methods | camelCase | `readState()` |
| Private methods, file-static functions | `_` + camelCase | `_readGauge()` |
| Variables, parameters | lowercase, as short as clear | `soc`, `buf`, `i` |
| Longer variable names | snake_case | `voltage_mv` |
| Private member variables | snake_case + trailing `_` | `last_soc_` |
| Public struct fields | like variables | `voltage_mv` |
| Constants, including local `const` | UPPER_SNAKE | `MAX_JUMP` |
| Enum values | UPPER_SNAKE | `READ_FAILED` |
| Macros, `#define` | UPPER_SNAKE | `BATTERY_MAX` |
| Global object instances | UPPER_SNAKE | `BATTERY_SERVICE` |

A leading underscore is only allowed before a lowercase letter, and only for
private methods and file-static functions. `_Upper` and `__x` are reserved by
the C and C++ standards.

## Control flow

- Every loop has a fixed upper bound visible in its condition:
  `for (i = 0U; ((i < count) && (i < MAX)); i++)`.
- `switch` on an enum covers every value or has a `default` that handles the
  unexpected case explicitly.
- No `goto`.

## Types and casts

- Fixed-width integers (`uint8_t`, `int32_t`) for anything that touches
  hardware, protocols or storage.
- Explicit casts only. In C++ use `static_cast` and friends, no C-style casts.
- `const` by default for reference parameters and for locals that do not
  change.
- `enum class` over plain `enum` in C++.

## Includes

- Each header compiles on its own (include what you use).
- Order: matching header, project headers, third-party, standard library.
- Include guards in every header: `#ifndef FILE_NAME_H` / `#define` /
  `#endif`. `#pragma once` is also fine in new code; do not mix both in one
  file.

## Example

```cpp
#include "batteryService.h"

namespace APP
{

BatteryService BATTERY_SERVICE;

static const uint16_t MAX_JUMP = 50U;

RETURN BatteryService::update (void)
{
    uint16_t soc = 0U;

    if (_readGauge(&soc) != RETURN::SUCCESS)
    {
        return RETURN::FAIL;
    }

    history_.push_back(soc);
    last_soc_ = soc;
    return RETURN::SUCCESS;
}

bool BatteryService::_isPlausible (uint16_t soc) const
{
    uint16_t diff = (soc >= last_soc_) ? (soc - last_soc_) : (last_soc_ - soc);

    return ((soc <= 1000U) && (diff <= MAX_JUMP));
}

} // namespace APP
```
