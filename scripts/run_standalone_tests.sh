#!/bin/bash
# Copyright The Lightning AI team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# USAGE:
#   ./run_standalone_tests.sh <test_dir_or_file_or_function>

# ENVIRONMENT VARIABLES:
#   NUM_PARALLEL_TESTS        Number of tests to run in parallel per batch (default: 5)
#   TEST_TIMEOUT              Per-test timeout in seconds (default: 1200)
#   BASE_PORT                 Starting port for assigning standalone test ports (default: 12000)
#   PORT_MARGIN               Port increment between successive test slots (default: 20)
#   STANDALONE_ARTIFACTS_DIR  Directory for log files and collected-tests output (default: .)
#   COVERAGE_SOURCE           If set, wraps each test run with `coverage run --source <value>`

set -uo pipefail  # Exit on unset variables and propagate pipe failures.
                  # Intentionally NOT using -e so we can collect all test exit codes
                  # rather than aborting on the first non-zero one.

# =============================================================================
# Helpers
# =============================================================================

# join_path <base> <sub>
#   Joins two path segments with exactly one slash between them,
#   analogous to Python's os.path.join.
join_path() {
    local base="${1%/}"   # strip trailing slash from base
    local sub="${2#/}"    # strip leading slash from sub-path
    echo "${base}/${sub}"
}

# array_contains <needle> <haystack_element>...
#   Returns 0 (success/true) if needle is found in the remaining arguments;
#   returns 1 (failure/false) otherwise.
#
#   NOTE: `0` in return is success, and `1` is failure, which is the opposite of typical boolean logic.
#   Usage:
#     if array_contains "$value" "${my_array[@]}"; then ...
array_contains() {
    local needle="$1"
    shift
    local item
    for item in "$@"; do
        [[ "$item" == "$needle" ]] && return 0
    done
    return 1
}

# get_available_port <preferred_port>
#   Prints an available TCP port.  Tries <preferred_port> first; if it is
#   already bound, falls back to a kernel-assigned ephemeral port.
get_available_port() {
    local preferred_port="$1"
    if nc -z localhost "$preferred_port" 2>/dev/null; then
        # Preferred port is busy — ask the kernel for a free ephemeral port.
        python3 -c "
import socket
s = socket.socket()
s.bind(('', 0))
print(s.getsockname()[1])
s.close()
"
    else
        echo "$preferred_port"
    fi
}

# print_color <color_code> <message>
#   Wraps a message in ANSI escape codes for coloured terminal output.
print_color() {
    local code="$1"
    shift
    printf "\e[${code}m%s\e[0m\n" "$*"
}

# Convenience wrappers used throughout the script.
print_blue()    { print_color 34 "$*"; }
print_green()   { print_color 32 "$*"; }
print_yellow()  { print_color 33 "$*"; }
print_red()     { print_color 31 "$*"; }
print_magenta() { print_color 35 "$*"; }
print_purple()  { print_color 95 "$*"; }

# =============================================================================
# Configuration — all values can be overridden via environment variables
# =============================================================================

# Number of tests that execute simultaneously in each batch.
test_batch_size="${NUM_PARALLEL_TESTS:-5}"

# Per-test timeout (seconds).
test_timeout="${TEST_TIMEOUT:-1200}"

# Port from which sequential allocation begins.
last_used_port="${BASE_PORT:-12000}"

# Gap between successive port allocations (gives headroom for services that
# open multiple sockets, e.g. distributed-training rendezvous).
port_margin="${PORT_MARGIN:-20}"

# Directory that receives log files, the collected-tests list, and coverage data.
artifacts_dir="${STANDALONE_ARTIFACTS_DIR:-.}"

# Optional coverage source package/path.
codecov_source="${COVERAGE_SOURCE:-}"

# =============================================================================
# Argument validation
# =============================================================================

if [[ $# -lt 1 ]]; then
    print_red "ERROR: No test path supplied."
    print_red "Usage: $0 <test_dir_or_file_or_function>"
    exit 1
fi

test_dir="$1"

mkdir -p "$artifacts_dir"

print_magenta "Artifacts directory : $artifacts_dir"
print_magenta "Test target         : $test_dir"
ls -lh .

# =============================================================================
# Build pytest / coverage CLI fragments
# =============================================================================

# If COVERAGE_SOURCE is set, each test is wrapped with `coverage run`.
# The --data-file flag is populated per-test below so parallel runs don't
# clobber each other's .coverage files.
if [[ -n "$codecov_source" ]]; then
    cli_coverage="-m coverage run --source ${codecov_source} --append"
else
    cli_coverage=""
fi

cli_pytest="-m pytest --no-header -v -s --color=yes --timeout=${test_timeout}"

print_magenta "Python flags : ${cli_coverage} ${cli_pytest}"

# =============================================================================
# Test collection
# =============================================================================

collected_tests_file="$(join_path "$artifacts_dir" "collected_tests.txt")"

# Run pytest in collection-only mode.  stdout+stderr are merged so that syntax
# errors (which land on stderr) are captured alongside the collected list.
python -um pytest "${test_dir}" -q --collect-only --pythonwarnings ignore \
    > "$collected_tests_file" 2>&1

if [[ $? -ne 0 ]]; then
    cat "$collected_tests_file"
    print_red "ERROR: test collection failed — check the output above for syntax errors."
    exit 1
fi


# Parse the collected output into an array.
# pytest --collect-only lines that contain "test_" are the individual test IDs.
# Each ID looks like:  <test_dir>/path/to/test_file.py::TestClass::test_method[param]
# We strip the leading <test_dir> fragment then re-attach it to avoid double
# slashes when test_dir itself contains a trailing slash.
tests=()
while IFS= read -r line; do
    if [[ "$line" != *"test_"* ]]; then
        continue
    fi

    # Remove the test_dir prefix (if present) to get the relative portion.
    # Pattern: strip everything up to and including the first occurrence of test_dir.
    relative="${line#*${test_dir}}"

    if [[ -z "$relative" ]]; then
        # The whole line *is* test_dir (single-file invocation).
        tests+=("$test_dir")
    else
        # Re-attach test_dir with a guaranteed single slash.
        tests+=("$(join_path "$test_dir" "$relative")")
    fi
done < "$collected_tests_file"

test_count="${#tests[@]}"

# =============================================================================
# Display collected tests
# =============================================================================

print_blue "================================================================================"
print_blue "COLLECTED ${test_count} TESTS:"
print_blue "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
printf "\e[34m%s\e[0m\n" "${tests[@]}"
print_blue "================================================================================"

if [[ $test_count -eq 0 ]]; then
    print_red "ERROR: no tests found.  Check that the path is correct and tests are discoverable."
    exit 1
elif [[ $test_count -eq 1 ]]; then
    print_yellow "WARNING: only one test found — verify the test path if this looks wrong."
fi

# =============================================================================
# Parallel test execution
# =============================================================================

aggregated_status=0   # Becomes non-zero if any test fails.
report=()             # Human-readable one-liner per completed test.
failed_tests=()       # Indexes (into tests[]) of failed tests.
used_ports=()         # Ports already reserved so we don't assign duplicates.
pids=()               # PIDs of currently-running background tests.
test_ids=()           # tests[] indexes corresponding to pids[].

print_magenta "Running ${test_count} tests in batches of ${test_batch_size}:"

for i in "${!tests[@]}"; do
    test="${tests[$i]}"

    # Build the per-test python invocation.
    if [[ -n "$codecov_source" ]]; then
        # Each parallel run writes its own .coverage file to avoid races.
        cli_test="python ${cli_coverage} --data-file=$(join_path "$artifacts_dir" "run-${i}.coverage") ${cli_pytest}"
    else
        cli_test="python ${cli_pytest}"
    fi

    # --- Port allocation ---
    # Advance the counter and find an unbound port that we haven't used yet.
    (( last_used_port += port_margin ))
    available_port="$(get_available_port "$last_used_port")"

    # If the returned port was already reserved by a previous test in this run,
    # keep incrementing until we find a truly free slot.
    while array_contains "$available_port" "${used_ports[@]+"${used_ports[@]}"}"; do
        (( last_used_port += port_margin ))
        available_port="$(get_available_port "$last_used_port")"
    done

    used_ports+=("$available_port")
    print_magenta "Assigned port ${available_port} for test index ${i}: ${test}"

    test_command="env STANDALONE_PORT=${available_port} ${cli_test} ${test}"
    print_purple "* Launching test $((i+1))/${test_count}: ${test_command}"

    # Run the test in the background; buffer its output to avoid garbled stdout.
    log_file="$(join_path "$artifacts_dir" "parallel_test_output-${i}.txt")"
    $test_command &> "$log_file" &

    pids+=($!)
    test_ids+=($i)

    # --- Batch synchronisation ---
    # Flush the batch when it is full, or when this is the very last test.
    local_batch_idx=$(( i + 1 ))
    if (( local_batch_idx % test_batch_size == 0 || i == test_count - 1 )); then
        print_magenta "Waiting for batch: PIDs ${pids[*]}"

        for j in "${!test_ids[@]}"; do
            batch_test_idx="${test_ids[$j]}"
            batch_pid="${pids[$j]}"
            batch_test="${tests[$batch_test_idx]}"
            batch_log="$(join_path "$artifacts_dir" "parallel_test_output-${batch_test_idx}.txt")"

            print_yellow "? Waiting for ${batch_test} (PID: ${batch_pid}) → ${batch_log}"
            wait "$batch_pid"
            test_exit_status=$?

            report+=("Ran ${batch_test} >> exit:${test_exit_status}")

            if [[ $test_exit_status -ne 0 ]]; then
                failed_tests+=("$batch_test_idx")
                aggregated_status=$test_exit_status
            fi
        done

        print_magenta "Batch done — starting next batch."
        test_ids=()
        pids=()
    fi
done

# =============================================================================
# Coverage combination (only meaningful when all tests have finished)
# =============================================================================

if [[ -n "$codecov_source" ]]; then
    print_magenta "Combining per-test coverage files..."
    # Gather only the per-test data files we wrote above.
    coverage_files=("$(join_path "$artifacts_dir" "run-"*.coverage)")
    if [[ ${#coverage_files[@]} -gt 0 ]]; then
        coverage combine "${coverage_files[@]}"
    fi
fi

# =============================================================================
# Final report
# =============================================================================

print_magenta "================================================================================"
for line in "${report[@]}"; do
    if [[ "$line" == *"exit:0"* ]]; then
        print_green "$line"
    else
        print_red "$line"
    fi
done
print_magenta "================================================================================"

# Print full buffered output for every failed test so CI logs are self-contained.
if [[ ${#failed_tests[@]} -gt 0 ]]; then
    print_blue "FAILED TESTS:"
    for idx in "${failed_tests[@]}"; do
        failed_log="$(join_path "$artifacts_dir" "parallel_test_output-${idx}.txt")"
        print_blue "================================================================================"
        print_blue "=== ${tests[$idx]} ==="
        print_blue "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        echo ""
        cat "$failed_log"
        print_blue "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        print_blue "================================================================================"
        printf "\n\n\n"
    done
else
    print_green "All tests passed!"
fi

# Propagate the worst non-zero exit code so the CI step is marked failed.
exit $aggregated_status
