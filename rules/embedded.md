# Embedded Firmware Rules

Applies to firmware running on the device (ARM Cortex-M, no exceptions, no
RTTI, fixed memory budget). Rules are MISRA-inspired, not a MISRA compliance
claim. Source: FW-Build `Docs/Standards/constitution.md` v1.1.0 and
`agent_behavior.md`.

## Determinism and memory

- **No dynamic allocation after init.** No `malloc`, `free`, `new`, `delete`
  outside system initialization. Runtime allocation fragments a small heap and
  makes timing unbounded.
- **ETL over STL over raw arrays.** Use `etl::vector<T, N>`, `etl::string<N>`,
  `etl::map<K, V, N>`, `etl::queue_spsc_atomic<T, N>`. The capacity is part of
  the type. If ETL has no fitting type, use `std::array<T, N>`. Raw C arrays
  only at C interfaces.
- When porting older code, port the behaviour and keep the ETL container. Do
  not regress to raw arrays because the old code used them.
- Bounded execution time beats theoretical throughput.

## Safety

- No recursion. Stack depth must be statically boundable.
- No dead code: no commented-out blocks, no `#if 0`, no unused functions.
- Check every return value. Ignoring a `RETURN`, status code or HAL result is
  a bug. If ignoring is intended, cast to `(void)` and comment why.
- Smallest possible scope for every variable.
- Every loop that waits on hardware has a timeout or retry cap.

## Fault tolerance

- Validate all external input: sensor readings, BLE payloads, config values,
  flash contents, parameter bounds.
- Assertions are for programming errors that must never happen, not for
  runtime conditions.
- Hardware and software watchdogs are in place.
- Every peripheral has a defined safe state for critical failure.

## Interrupts and concurrency

- Interrupt handlers stay short: set a flag or post an event, do the work in
  the event handler. No logging, no allocation, no blocking calls in an ISR.
- State shared between ISR and task is `volatile` or atomic and protected.

## Hardware boundary

- AI agents may build and run host-side unit tests inside the project
  containers.
- **Flashing, erasing, resetting, J-Link, SEGGER, OpenOCD and any command that
  drives a connected device are done by a human only.** The guard in this
  repository blocks these commands for agents.
- Changes that touch a HAL implementation, driver or end-to-end data path need
  an on-device test before merge. Host tests alone are not enough there.

## Vendored code and submodules

- SDKs, ETL, LVGL, nanopb, Dhara, FreeRTOS and every git submodule (including
  this conventions repository) are read-only.
- Do not run git commands inside a submodule. Inspect from the parent with
  `git submodule status` or `git -C <path> log --oneline -1`.
- Submodule pointer bumps go in their own commit on their own branch.
- Bugs in vendored code are reported, not patched in place.
