"""Flash rule: agents never drive a connected device."""

import re

PROBE_TOOLS = re.compile(
    r"(?<![\w./-])("
    r"JLinkExe|JLink\.exe|JLinkGDBServer\w*|JLinkRemoteServer\w*|JFlash\w*|"
    r"openocd|pyocd|probe-rs|nrfjprog|st-flash|STM32_Programmer_CLI"
    r")(?![\w-])",
    re.IGNORECASE,
)
COMMANDER_FLASH = re.compile(r"(?<![\w-])commander(\.exe)?\s+(flash|device\s+(masserase|pageerase|reset))\b", re.I)
DEBUG_CONTAINER = re.compile(r"\bdocker\s+exec\b[^|;&]*\bdebug-tools\b", re.I)
HW_SCRIPTS = re.compile(
    r"(?<![\w-])(flash|erase|run|debug|dev-env)\.(sh|ps1|bat|cmd)\b", re.I
)
BUILD_TARGET = re.compile(
    r"(\bmake\b[^|;&]*\s(flash|erase)\b)|(\bcmake\b[^|;&]*--target\s+(flash|erase)\b)|"
    r"(\bninja\b[^|;&]*\s(flash|erase)\b)",
    re.I,
)
READ_ONLY_PREFIX = re.compile(r"^\s*(cat|less|more|head|tail|grep|rg|git\s+(log|show|diff|blame)|echo|printf|ls|wc|file)\b", re.I)


def _segments(command):
    """Split on shell separators so 'cat x; ./flash.sh' checks both parts."""
    return [s for s in re.split(r"&&|\|\||;|\||\n", command) if s.strip()]


def check(call):
    if call.kind != "shell" or not call.command:
        return None
    for seg in _segments(call.command):
        if READ_ONLY_PREFIX.match(seg):
            continue
        if PROBE_TOOLS.search(seg) or COMMANDER_FLASH.search(seg) or DEBUG_CONTAINER.search(seg):
            return ("flash: agents never drive a connected device (J-Link, OpenOCD, probe tools). "
                    "A human runs this.")
        if HW_SCRIPTS.search(seg):
            return ("flash: flash/erase/run/debug/dev-env scripts drive hardware and are run by a "
                    "human only.")
        if BUILD_TARGET.search(seg):
            return "flash: build targets 'flash' and 'erase' drive hardware and are run by a human only."
    return None
