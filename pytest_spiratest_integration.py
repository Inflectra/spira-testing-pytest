import requests
import json
import datetime
import configparser
import pytest
import os
import sys

'''
The config is only retrieved once
'''
config = None
config_loaded = False  # Track if we've attempted to load config
spira_disabled = False  # Track if Spira is disabled to skip all processing

# Cache for expensive checks
_batch_mode_cache = None  # Cache batch mode result
_spira_enabled_cache = None  # Cache enabled state result

# Store test results for batch posting
test_results_queue = []

# Store class-level test results for aggregation
class_test_results = {}

# Store marker-level test results for aggregation
marker_test_results = {}

# Store module-level test results for aggregation
module_test_results = {}

def log_message(message, level="INFO"):
    """
    Log a message to stderr so it appears in pytest output
    """
    prefix = f"[pytest-spiratest {level}]"
    print(f"{prefix} {message}", file=sys.stderr)

def log_verbose(message, config):
    """
    Log a message only if verbose mode is enabled
    OPTIMIZED: Check verbose flag directly without dict.get()
    """
    # Fast path: check verbose flag directly
    if config.get("verbose", False):
        log_message(message, "DEBUG")


def pytest_addoption(parser):
    """
    Add command-line options for Spira integration
    """
    group = parser.getgroup('spira', 'Spira integration options')
    group.addoption(
        '--spira-disabled',
        action='store_true',
        default=False,
        help='Disable Spira integration (overrides config)'
    )
    group.addoption(
        '--spira-enabled',
        action='store_true',
        default=False,
        help='Enable Spira integration (overrides config)'
    )
    group.addoption(
        '--spira-dry-run',
        action='store_true',
        default=False,
        help='Dry run mode - show what would be posted without actually posting'
    )
    group.addoption(
        '--spira-batch',
        action='store_true',
        default=False,
        help='Enable batch mode - post all results at once (overrides config)'
    )
    group.addoption(
        '--spira-no-batch',
        action='store_true',
        default=False,
        help='Disable batch mode - post results individually (overrides config)'
    )


def pytest_configure(config):
    """
    Configure the plugin with CLI options
    """
    # Store CLI options in config for later use
    config._spira_cli_disabled = config.getoption('--spira-disabled')
    config._spira_cli_enabled = config.getoption('--spira-enabled')
    config._spira_dry_run = config.getoption('--spira-dry-run')
    config._spira_cli_batch = config.getoption('--spira-batch')
    config._spira_cli_no_batch = config.getoption('--spira-no-batch')


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before returning the exit status
    Post batched results if batch mode is enabled and aggregate class-level, marker-level, and module-level results
    """
    global test_results_queue, class_test_results, marker_test_results, module_test_results, spira_disabled
    
    # Early exit: Check CLI flag first before loading config
    if session.config._spira_cli_disabled:
        return
    
    # Early exit: If we've already determined Spira is disabled, skip all processing
    if spira_disabled:
        return
    
    config = getConfig()
    
    # Early exit if disabled
    if not is_spira_enabled(session.config, config):
        return
    
    # Process aggregated marker-level results first
    if marker_test_results:
        log_verbose(f"Processing {len(marker_test_results)} marker-level test results", config)
        for marker_key, marker_data in marker_test_results.items():
            aggregated_run = aggregate_marker_results(marker_data, config)
            if aggregated_run:
                if is_batch_mode_enabled(session.config, config):
                    test_results_queue.append(aggregated_run)
                else:
                    aggregated_run.post(config["url"], config["username"], config["token"], config, session.config)
        marker_test_results = {}
    
    # Process aggregated module-level results
    if module_test_results:
        log_verbose(f"Processing {len(module_test_results)} module-level test results", config)
        for module_key, module_data in module_test_results.items():
            aggregated_run = aggregate_module_results(module_data, config)
            if aggregated_run:
                if is_batch_mode_enabled(session.config, config):
                    test_results_queue.append(aggregated_run)
                else:
                    aggregated_run.post(config["url"], config["username"], config["token"], config, session.config)
        module_test_results = {}
    
    # Process aggregated class-level results
    if class_test_results:
        log_verbose(f"Processing {len(class_test_results)} class-level test results", config)
        for class_key, class_data in class_test_results.items():
            aggregated_run = aggregate_class_results(class_data, config)
            if aggregated_run:
                if is_batch_mode_enabled(session.config, config):
                    test_results_queue.append(aggregated_run)
                else:
                    aggregated_run.post(config["url"], config["username"], config["token"], config, session.config)
        class_test_results = {}
    
    log_verbose(f"pytest_sessionfinish called with {len(test_results_queue)} queued results", config)
    
    if test_results_queue:
        # Check if integration is enabled
        if not is_spira_enabled(session.config, config):
            log_verbose("Integration disabled, not posting batch", config)
            return
        
        # Check if batch mode is enabled
        if is_batch_mode_enabled(session.config, config):
            log_message(f"Posting {len(test_results_queue)} test results in batch mode", "INFO")
            post_batch_results(test_results_queue, config)
            test_results_queue = []
        else:
            log_verbose("Batch mode not enabled, results were already posted individually", config)
    else:
        log_verbose("No queued results to post", config)

def is_spira_enabled(pytest_config, spira_config):
    """
    Determine if Spira integration is enabled based on CLI and config settings
    Priority: CLI --spira-disabled > CLI --spira-enabled > config enabled setting > default (true)
    OPTIMIZED: Result is cached after first call
    """
    global _spira_enabled_cache
    
    # Return cached result if available
    if _spira_enabled_cache is not None:
        return _spira_enabled_cache
    
    # CLI --spira-disabled has highest priority
    if pytest_config._spira_cli_disabled:
        log_verbose("Spira integration disabled via --spira-disabled CLI flag", spira_config)
        _spira_enabled_cache = False
        return False
    
    # CLI --spira-enabled overrides config
    if pytest_config._spira_cli_enabled:
        log_verbose("Spira integration enabled via --spira-enabled CLI flag", spira_config)
        _spira_enabled_cache = True
        return True
    
    # Check config file setting
    if "enabled" in spira_config:
        enabled = spira_config["enabled"]
        log_verbose(f"Spira integration {'enabled' if enabled else 'disabled'} via config file", spira_config)
        _spira_enabled_cache = enabled
        return enabled
    
    # Default: enabled if URL is configured
    result = spira_config.get("url", "") != ""
    _spira_enabled_cache = result
    return result


def is_batch_mode_enabled(pytest_config, spira_config):
    """
    Determine if batch mode is enabled based on CLI and config settings
    Priority: CLI --spira-no-batch > CLI --spira-batch > config batch_mode setting > default (false)
    OPTIMIZED: Result is cached after first call
    """
    global _batch_mode_cache
    
    # Return cached result if available
    if _batch_mode_cache is not None:
        return _batch_mode_cache
    
    # CLI --spira-no-batch has highest priority
    if pytest_config._spira_cli_no_batch:
        log_verbose("Batch mode disabled via --spira-no-batch CLI flag", spira_config)
        _batch_mode_cache = False
        return False
    
    # CLI --spira-batch overrides config
    if pytest_config._spira_cli_batch:
        log_verbose("Batch mode enabled via --spira-batch CLI flag", spira_config)
        _batch_mode_cache = True
        return True
    
    # Check config file setting
    batch_enabled = spira_config.get("batch_mode", False)
    if batch_enabled:
        log_verbose("Batch mode enabled via config file", spira_config)
    else:
        log_verbose("Batch mode disabled (default or config)", spira_config)
    _batch_mode_cache = batch_enabled
    return batch_enabled


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    
    # OPTIMIZATION: Early exit before any processing
    global spira_disabled
    
    # If we've already determined Spira is disabled, exit immediately
    if spira_disabled:
        return
    
    # Check CLI flag before even getting the report
    if hasattr(item.config, '_spira_cli_disabled') and item.config._spira_cli_disabled:
        spira_disabled = True
        return
    
    report = outcome.get_result()
    
    # Only process the actual test call, not setup/teardown
    if report.when != "call":
        return
    
    # Load config only once on first test
    config = getConfig()
    
    # Check if integration is enabled and cache the result
    if not is_spira_enabled(item.config, config):
        spira_disabled = True
        return
    
    # Only do stuff if config is specified
    if config["url"] != "":
        status_id = -1
        current_time = datetime.datetime.utcnow()
        # The function name
        test_name = report.location[2].lower()
        # Handle None stack trace for passing tests
        stack_trace = report.longreprtext if report.longreprtext else ""
        message = ""

        if report.outcome == "passed":
            # 2 is passed
            status_id = 2
            message = "Test Succeeded"
        elif report.outcome == "skipped":
            # 3 is not run
            status_id = 3
            message = "Test Skipped"
        elif report.outcome == "failed":
            #1 is failed
            status_id = 1
            message = ""

        # OPTIMIZATION: Get test case ID and mapping source in one pass
        test_case_id, mapping_source = get_test_case_id_and_source(item, test_name, config)
        
        # Skip logging if no mapping found and no default configured
        if test_case_id is None:
            log_verbose(f"Test '{test_name}' has no mapping and no default configured - skipping Spira logging", config)
            return
        
        log_verbose(f"Test '{test_name}' mapped to Spira test case ID: {test_case_id} (source: {mapping_source})", config)

        # Create the test run
        test_run = SpiraTestRun(
            config["project_id"], 
            test_case_id, 
            test_name, 
            stack_trace, 
            status_id, 
            current_time - datetime.timedelta(seconds=report.duration), 
            current_time,
            message=message, 
            release_id=config["release_id"], 
            test_set_id=config["test_set_id"]
        )
        
        # Aggregate results based on mapping source
        if mapping_source['type'] == 'marker':
            # Marker-level mapping - aggregate all tests with this marker
            global marker_test_results
            marker_key = (mapping_source['marker_name'], test_case_id)
            if marker_key not in marker_test_results:
                marker_test_results[marker_key] = {
                    'marker_name': mapping_source['marker_name'],
                    'test_case_id': test_case_id,
                    'results': [],
                    'project_id': config["project_id"],
                    'release_id': config["release_id"],
                    'test_set_id': config["test_set_id"]
                }
            marker_test_results[marker_key]['results'].append({
                'test_name': test_name,
                'status_id': status_id,
                'stack_trace': stack_trace,
                'message': message,
                'start_time': current_time - datetime.timedelta(seconds=report.duration),
                'end_time': current_time,
                'duration': report.duration
            })
            log_verbose(f"Aggregating marker-level result for: @{mapping_source['marker_name']} - {test_name}", config)
        elif mapping_source['type'] == 'module':
            # Module-level mapping - aggregate all tests in this module
            global module_test_results
            module_key = (mapping_source['module_name'], test_case_id)
            if module_key not in module_test_results:
                module_test_results[module_key] = {
                    'module_name': mapping_source['module_name'],
                    'test_case_id': test_case_id,
                    'results': [],
                    'project_id': config["project_id"],
                    'release_id': config["release_id"],
                    'test_set_id': config["test_set_id"]
                }
            module_test_results[module_key]['results'].append({
                'test_name': test_name,
                'status_id': status_id,
                'stack_trace': stack_trace,
                'message': message,
                'start_time': current_time - datetime.timedelta(seconds=report.duration),
                'end_time': current_time,
                'duration': report.duration
            })
            log_verbose(f"Aggregating module-level result for: {mapping_source['module_name']}.{test_name}", config)
        elif mapping_source['type'] == 'class':
            # Class-level mapping - aggregate all tests in this class
            global class_test_results
            class_key = (item.cls.__name__, test_case_id)
            if class_key not in class_test_results:
                class_test_results[class_key] = {
                    'class_name': item.cls.__name__,
                    'test_case_id': test_case_id,
                    'results': [],
                    'project_id': config["project_id"],
                    'release_id': config["release_id"],
                    'test_set_id': config["test_set_id"]
                }
            class_test_results[class_key]['results'].append({
                'test_name': test_name,
                'status_id': status_id,
                'stack_trace': stack_trace,
                'message': message,
                'start_time': current_time - datetime.timedelta(seconds=report.duration),
                'end_time': current_time,
                'duration': report.duration
            })
            log_verbose(f"Aggregating class-level result for: {item.cls.__name__}.{test_name}", config)
        else:
            # Function-level, spira_id marker, or default - post individually
            if is_batch_mode_enabled(item.config, config):
                # Add to queue for batch posting
                global test_results_queue
                test_results_queue.append(test_run)
                log_verbose(f"Queued test result for batch posting: {test_name}", config)
            else:
                # Post immediately
                test_run.post(config["url"], config["username"], config["token"], config, item.config)


def get_test_case_id_and_source(item, test_name, config):
    """
    OPTIMIZED: Get both test case ID and mapping source in a single pass.
    This avoids duplicate marker lookups which are expensive.
    
    Returns: (test_case_id, mapping_source_dict)
    """
    # Check for spira_id marker (highest priority - no aggregation)
    spira_id_marker = item.get_closest_marker("spira_id")
    if spira_id_marker and spira_id_marker.args:
        return spira_id_marker.args[0], {'type': 'spira_id'}
    
    # Check for other marker mappings (aggregate by marker)
    # OPTIMIZATION: Only check markers that are in config to avoid unnecessary lookups
    if "marker_mappings" in config and config["marker_mappings"]:
        for marker_name, test_case_id in config["marker_mappings"].items():
            marker = item.get_closest_marker(marker_name)
            if marker:
                return test_case_id, {'type': 'marker', 'marker_name': marker_name}
    
    # Check for function-level mapping (no aggregation)
    if test_name in config["test_case_ids"]:
        return config["test_case_ids"][test_name], {'type': 'function'}
    
    # Check for class-level mapping (aggregate by class)
    if item.cls:
        class_name = item.cls.__name__.lower()
        if class_name in config["test_case_ids"]:
            return config["test_case_ids"][class_name], {'type': 'class'}
    
    # Check for module-level mapping (aggregate by module)
    if item.module and "module_mappings" in config and config["module_mappings"]:
        module_name = item.module.__name__.lower()
        log_verbose(f"Checking module mapping for module: '{module_name}' against configured modules: {list(config['module_mappings'].keys())}", config)
        if module_name in config["module_mappings"]:
            return config["module_mappings"][module_name], {'type': 'module', 'module_name': module_name}
    
    # Return default (if configured)
    if "default" in config["test_case_ids"]:
        return config["test_case_ids"]["default"], {'type': 'default'}
    
    # No mapping found and no default - return None to skip logging
    return None, {'type': 'unmapped'}


def aggregate_class_results(class_data, config):
    """
    Aggregate multiple test results from a class into a single test run
    Returns a SpiraTestRun with aggregated results
    """
    results = class_data['results']
    if not results:
        return None
    
    # Determine overall status: fail if any failed, pass if all passed
    overall_status = 2  # Start with passed
    has_failure = False
    has_skip = False
    
    for result in results:
        if result['status_id'] == 1:  # Failed
            has_failure = True
            overall_status = 1
            break
        elif result['status_id'] == 3:  # Skipped
            has_skip = True
    
    # If no failures but has skips, mark as skipped
    if not has_failure and has_skip:
        overall_status = 3
    
    # Aggregate messages and stack traces
    combined_message = f"Class: {class_data['class_name']}\n"
    combined_stack_trace = ""
    
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for result in results:
        if result['status_id'] == 2:
            passed_count += 1
        elif result['status_id'] == 1:
            failed_count += 1
        elif result['status_id'] == 3:
            skipped_count += 1
    
    combined_message += f"Total: {len(results)} tests - "
    combined_message += f"Passed: {passed_count}, Failed: {failed_count}, Skipped: {skipped_count}\n\n"
    
    # Add details for each test
    for result in results:
        status_text = "PASSED" if result['status_id'] == 2 else "FAILED" if result['status_id'] == 1 else "SKIPPED"
        combined_message += f"[{status_text}] {result['test_name']}\n"
        
        if result['stack_trace']:
            combined_stack_trace += f"\n{'='*60}\n"
            combined_stack_trace += f"Test: {result['test_name']}\n"
            combined_stack_trace += f"{'='*60}\n"
            combined_stack_trace += result['stack_trace']
            combined_stack_trace += "\n"
    
    # Use the earliest start time and latest end time
    start_time = min(r['start_time'] for r in results)
    end_time = max(r['end_time'] for r in results)
    
    # Create aggregated test run
    aggregated_run = SpiraTestRun(
        class_data['project_id'],
        class_data['test_case_id'],
        class_data['class_name'],
        combined_stack_trace.strip(),
        overall_status,
        start_time,
        end_time,
        message=combined_message.strip(),
        release_id=class_data['release_id'],
        test_set_id=class_data['test_set_id']
    )
    
    log_verbose(f"Aggregated {len(results)} tests for class {class_data['class_name']} - Status: {overall_status}", config)
    
    return aggregated_run


def aggregate_marker_results(marker_data, config):
    """
    Aggregate multiple test results from a marker into a single test run
    Returns a SpiraTestRun with aggregated results
    """
    results = marker_data['results']
    if not results:
        return None
    
    # Determine overall status: fail if any failed, pass if all passed
    overall_status = 2  # Start with passed
    has_failure = False
    has_skip = False
    
    for result in results:
        if result['status_id'] == 1:  # Failed
            has_failure = True
            overall_status = 1
            break
        elif result['status_id'] == 3:  # Skipped
            has_skip = True
    
    # If no failures but has skips, mark as skipped
    if not has_failure and has_skip:
        overall_status = 3
    
    # Aggregate messages and stack traces
    combined_message = f"Marker: @{marker_data['marker_name']}\n"
    combined_stack_trace = ""
    
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for result in results:
        if result['status_id'] == 2:
            passed_count += 1
        elif result['status_id'] == 1:
            failed_count += 1
        elif result['status_id'] == 3:
            skipped_count += 1
    
    combined_message += f"Total: {len(results)} tests - "
    combined_message += f"Passed: {passed_count}, Failed: {failed_count}, Skipped: {skipped_count}\n\n"
    
    # Add details for each test (limit to first 50 for very large marker groups)
    display_limit = 50
    for i, result in enumerate(results):
        if i >= display_limit:
            remaining = len(results) - display_limit
            combined_message += f"\n... and {remaining} more tests (showing first {display_limit})\n"
            break
        status_text = "PASSED" if result['status_id'] == 2 else "FAILED" if result['status_id'] == 1 else "SKIPPED"
        combined_message += f"[{status_text}] {result['test_name']}\n"
    
    # Add stack traces for failed tests only (to keep it manageable)
    failed_tests = [r for r in results if r['stack_trace']]
    if failed_tests:
        combined_stack_trace += f"Failed tests: {len(failed_tests)}\n"
        for result in failed_tests[:20]:  # Limit to first 20 failures
            combined_stack_trace += f"\n{'='*60}\n"
            combined_stack_trace += f"Test: {result['test_name']}\n"
            combined_stack_trace += f"{'='*60}\n"
            combined_stack_trace += result['stack_trace']
            combined_stack_trace += "\n"
        if len(failed_tests) > 20:
            combined_stack_trace += f"\n... and {len(failed_tests) - 20} more failures (showing first 20)\n"
    
    # Use the earliest start time and latest end time
    start_time = min(r['start_time'] for r in results)
    end_time = max(r['end_time'] for r in results)
    
    # Create aggregated test run
    aggregated_run = SpiraTestRun(
        marker_data['project_id'],
        marker_data['test_case_id'],
        f"@{marker_data['marker_name']}",
        combined_stack_trace.strip(),
        overall_status,
        start_time,
        end_time,
        message=combined_message.strip(),
        release_id=marker_data['release_id'],
        test_set_id=marker_data['test_set_id']
    )
    
    log_verbose(f"Aggregated {len(results)} tests for marker @{marker_data['marker_name']} - Status: {overall_status}", config)
    
    return aggregated_run


def aggregate_module_results(module_data, config):
    """
    Aggregate multiple test results from a module into a single test run
    Returns a SpiraTestRun with aggregated results
    """
    results = module_data['results']
    if not results:
        return None
    
    # Determine overall status: fail if any failed, pass if all passed
    overall_status = 2  # Start with passed
    has_failure = False
    has_skip = False
    
    for result in results:
        if result['status_id'] == 1:  # Failed
            has_failure = True
            overall_status = 1
            break
        elif result['status_id'] == 3:  # Skipped
            has_skip = True
    
    # If no failures but has skips, mark as skipped
    if not has_failure and has_skip:
        overall_status = 3
    
    # Aggregate messages and stack traces
    combined_message = f"Module: {module_data['module_name']}\n"
    combined_stack_trace = ""
    
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for result in results:
        if result['status_id'] == 2:
            passed_count += 1
        elif result['status_id'] == 1:
            failed_count += 1
        elif result['status_id'] == 3:
            skipped_count += 1
    
    combined_message += f"Total: {len(results)} tests - "
    combined_message += f"Passed: {passed_count}, Failed: {failed_count}, Skipped: {skipped_count}\n\n"
    
    # Add details for each test
    for result in results:
        status_text = "PASSED" if result['status_id'] == 2 else "FAILED" if result['status_id'] == 1 else "SKIPPED"
        combined_message += f"[{status_text}] {result['test_name']}\n"
        
        if result['stack_trace']:
            combined_stack_trace += f"\n{'='*60}\n"
            combined_stack_trace += f"Test: {result['test_name']}\n"
            combined_stack_trace += f"{'='*60}\n"
            combined_stack_trace += result['stack_trace']
            combined_stack_trace += "\n"
    
    # Use the earliest start time and latest end time
    start_time = min(r['start_time'] for r in results)
    end_time = max(r['end_time'] for r in results)
    
    # Create aggregated test run
    aggregated_run = SpiraTestRun(
        module_data['project_id'],
        module_data['test_case_id'],
        module_data['module_name'],
        combined_stack_trace.strip(),
        overall_status,
        start_time,
        end_time,
        message=combined_message.strip(),
        release_id=module_data['release_id'],
        test_set_id=module_data['test_set_id']
    )
    
    log_verbose(f"Aggregated {len(results)} tests for module {module_data['module_name']} - Status: {overall_status}", config)
    
    return aggregated_run


def load_env_file(filepath=".env.spira"):
    """
    Load environment variables from a .env.spira file
    Returns a dictionary of key-value pairs
    """
    env_vars = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
    return env_vars


def getConfig():
    global config, config_loaded, spira_disabled
    # Only retrieve config once
    if config is None:
        config_loaded = True
        
        # Model of config object:
        config = {
            "url": "",
            "username": "",
            "token": "",
            "project_id": -1,
            "release_id": -1,
            "test_set_id": -1,
            "test_case_ids": {},
            "marker_mappings": {},
            "module_mappings": {},
            "verbose": False,
            "enabled": True,
            "batch_mode": False,
            "batch_size": BATCH_SIZE_LIMIT
        }
        
        # Quick check: if no config files exist, return minimal config immediately
        if not os.path.exists("spira.cfg") and not os.path.exists(".env.spira"):
            config["enabled"] = False
            spira_disabled = True
            return config
        
        # OPTIMIZATION: Quick check if enabled=false in config before parsing everything
        # This avoids expensive parsing when disabled
        if os.path.exists("spira.cfg"):
            try:
                with open("spira.cfg", 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.lower() == "enabled = false" or line.lower() == "enabled=false":
                            config["enabled"] = False
                            spira_disabled = True
                            return config
            except:
                pass  # If quick check fails, fall through to full parsing
        
        # Load environment variables from .env.spira file
        env_vars = load_env_file()
        
        # Check env var for enabled state before full parsing
        if "SPIRA_ENABLED" in env_vars:
            if env_vars["SPIRA_ENABLED"].lower() not in ("true", "yes", "1", "on"):
                config["enabled"] = False
                spira_disabled = True
                return config
        
        # Parse the config file
        parser = configparser.ConfigParser()
        config_files_read = parser.read("spira.cfg")
        
        # Warn if no config file found and no env vars
        if not config_files_read and not env_vars:
            config["enabled"] = False
            spira_disabled = True
            log_message("No spira.cfg file or .env.spira file found. Spira integration will be disabled.", "WARNING")
            return config

        sections = parser.sections()

        # Process Configs
        for section in sections:
            # Handle credentials and test case mappings differently
            if section == "credentials":
                for (key, value) in parser.items(section):
                    config[key] = value
            elif section == "test_cases":
                for (key, value) in parser.items(section):
                    config["test_case_ids"][key.lower()] = value
            elif section == "markers":
                for (key, value) in parser.items(section):
                    config["marker_mappings"][key.lower()] = value
            elif section == "modules":
                for (key, value) in parser.items(section):
                    config["module_mappings"][key.lower()] = value
            elif section == "settings":
                for (key, value) in parser.items(section):
                    if key.lower() == "verbose":
                        config["verbose"] = value.lower() in ("true", "yes", "1", "on")
                    elif key.lower() == "enabled":
                        config["enabled"] = value.lower() in ("true", "yes", "1", "on")
                    elif key.lower() == "batch_mode":
                        config["batch_mode"] = value.lower() in ("true", "yes", "1", "on")
                    elif key.lower() == "batch_size":
                        try:
                            batch_size = int(value)
                            if batch_size > 0:
                                config["batch_size"] = batch_size
                            else:
                                log_message(f"Invalid batch_size value: {value} (must be positive), using default: {BATCH_SIZE_LIMIT}", "WARNING")
                        except ValueError:
                            log_message(f"Invalid batch_size value: {value} (must be integer), using default: {BATCH_SIZE_LIMIT}", "WARNING")
        
        # Override with environment variables if present
        # Priority: .env.spira > spira.cfg
        if "SPIRA_URL" in env_vars:
            config["url"] = env_vars["SPIRA_URL"]
        if "SPIRA_USERNAME" in env_vars:
            config["username"] = env_vars["SPIRA_USERNAME"]
        if "SPIRA_TOKEN" in env_vars:
            config["token"] = env_vars["SPIRA_TOKEN"]
        if "SPIRA_PROJECT_ID" in env_vars:
            try:
                config["project_id"] = int(env_vars["SPIRA_PROJECT_ID"])
            except (ValueError, TypeError):
                log_message(f"Invalid SPIRA_PROJECT_ID value: {env_vars['SPIRA_PROJECT_ID']}", "WARNING")
        if "SPIRA_RELEASE_ID" in env_vars:
            try:
                config["release_id"] = int(env_vars["SPIRA_RELEASE_ID"])
            except (ValueError, TypeError):
                log_message(f"Invalid SPIRA_RELEASE_ID value: {env_vars['SPIRA_RELEASE_ID']}", "WARNING")
        if "SPIRA_TEST_SET_ID" in env_vars:
            try:
                config["test_set_id"] = int(env_vars["SPIRA_TEST_SET_ID"])
            except (ValueError, TypeError):
                log_message(f"Invalid SPIRA_TEST_SET_ID value: {env_vars['SPIRA_TEST_SET_ID']}", "WARNING")
        if "SPIRA_VERBOSE" in env_vars:
            config["verbose"] = env_vars["SPIRA_VERBOSE"].lower() in ("true", "yes", "1", "on")
        if "SPIRA_ENABLED" in env_vars:
            config["enabled"] = env_vars["SPIRA_ENABLED"].lower() in ("true", "yes", "1", "on")
        if "SPIRA_BATCH_MODE" in env_vars:
            config["batch_mode"] = env_vars["SPIRA_BATCH_MODE"].lower() in ("true", "yes", "1", "on")
        if "SPIRA_BATCH_SIZE" in env_vars:
            try:
                batch_size = int(env_vars["SPIRA_BATCH_SIZE"])
                if batch_size > 0:
                    config["batch_size"] = batch_size
                else:
                    log_message(f"Invalid SPIRA_BATCH_SIZE value: {env_vars['SPIRA_BATCH_SIZE']} (must be positive)", "WARNING")
            except ValueError:
                log_message(f"Invalid SPIRA_BATCH_SIZE value: {env_vars['SPIRA_BATCH_SIZE']} (must be integer)", "WARNING")
        
        # Set spira_disabled flag if config indicates disabled
        if not config["enabled"]:
            spira_disabled = True
        
        # Log configuration summary if verbose
        if config["verbose"]:
            log_message("Spira integration initialized", "INFO")
            log_message(f"  Enabled: {config['enabled']}", "DEBUG")
            log_message(f"  Batch mode: {config['batch_mode']}", "DEBUG")
            log_message(f"  URL: {config['url']}", "DEBUG")
            log_message(f"  Project ID: {config['project_id']}", "DEBUG")
            log_message(f"  Default test case: {config['test_case_ids'].get('default', 'not set')}", "DEBUG")
            if config["release_id"] != -1:
                log_message(f"  Release ID: {config['release_id']}", "DEBUG")
            if config["test_set_id"] != -1:
                log_message(f"  Test Set ID: {config['test_set_id']}", "DEBUG")
            
    return config


# Name of this extension
RUNNER_NAME = "PyTest"

# Maximum number of test runs to post in a single batch
# Spira API has a limit, so we paginate large batches
BATCH_SIZE_LIMIT = 500


def post_batch_results(test_runs, config):
    """
    Post multiple test runs in batch API calls with pagination
    Uses the v7.0 batch endpoint
    Splits large batches into chunks based on configured batch_size to avoid API limits
    """
    if not test_runs:
        return
    
    total_runs = len(test_runs)
    batch_size = config.get("batch_size", BATCH_SIZE_LIMIT)
    
    # If we have more than the batch size limit, paginate
    if total_runs > batch_size:
        log_message(f"Splitting {total_runs} test results into batches of {batch_size}", "INFO")
        
        # Split into chunks
        for i in range(0, total_runs, batch_size):
            batch = test_runs[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_runs + batch_size - 1) // batch_size
            log_message(f"Posting batch {batch_num}/{total_batches} ({len(batch)} test results)", "INFO")
            _post_single_batch(batch, config)
    else:
        # Post all at once
        _post_single_batch(test_runs, config)


def _post_single_batch(test_runs, config):
    """
    Post a single batch of test runs (internal helper function)
    Should not exceed BATCH_SIZE_LIMIT
    """
    if not test_runs:
        return
    
    url = config["url"] + "/Services/v7_0/RestService.svc/" + \
        f"projects/{config['project_id']}/test-runs/record-multiple"
    
    params = {
        'username': config["username"],
        'api-key': config["token"]
    }
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': RUNNER_NAME
    }
    
    # Build array of test run objects
    test_runs_array = []
    for test_run in test_runs:
        body = {
            'TestRunFormatId': 1,
            'StartDate': test_run.start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'EndDate': test_run.end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'RunnerName': RUNNER_NAME,
            'RunnerTestName': test_run.test_name,
            'RunnerMessage': test_run.message,
            'RunnerStackTrace': test_run.stack_trace,
            'TestCaseId': test_run.test_case_id,
            'ExecutionStatusId': test_run.status_id
        }
        
        if test_run.release_id != -1:
            body["ReleaseId"] = int(test_run.release_id)
        if test_run.test_set_id != -1:
            body["TestSetId"] = int(test_run.test_set_id)
        
        test_runs_array.append(body)
    
    log_verbose(f"Posting {len(test_runs_array)} test results in batch to: {url}", config)
    
    try:
        response = requests.post(url, data=json.dumps(test_runs_array), params=params, headers=headers, timeout=120)
        response.raise_for_status()
        log_message(f"Successfully posted {len(test_runs_array)} test results in batch", "INFO")
        log_verbose(f"Response: {response.text}", config)
    except requests.exceptions.Timeout:
        log_message(f"Timeout posting batch of {len(test_runs_array)} test results to Spira", "ERROR")
        log_message(f"  URL: {url}", "ERROR")
    except requests.exceptions.ConnectionError as e:
        log_message(f"Connection error posting batch of {len(test_runs_array)} test results to Spira", "ERROR")
        log_message(f"  URL: {url}", "ERROR")
        log_message(f"  Error: {str(e)}", "ERROR")
    except requests.exceptions.HTTPError as e:
        log_message(f"HTTP error {response.status_code} posting batch of {len(test_runs_array)} test results to Spira", "ERROR")
        log_message(f"  URL: {url}", "ERROR")
        log_message(f"  Response: {response.text}", "ERROR")
    except requests.exceptions.RequestException as e:
        log_message(f"Error posting batch of {len(test_runs_array)} test results to Spira", "ERROR")
        log_message(f"  URL: {url}", "ERROR")
        log_message(f"  Error: {str(e)}", "ERROR")


class SpiraTestRun:
    # The URL snippet used after the Spira URL
    REST_SERVICE_URL = "/Services/v6_0/RestService.svc/"
    # The URL spippet used to post an automated test run. Needs the project ID to work
    POST_TEST_RUN = "projects/%s/test-runs/record"
    '''
    A TestRun object model for Spira
    '''
    project_id = -1
    test_case_id = -1
    test_name = ""
    stack_trace = ""
    status_id = -1
    start_time = -1
    end_time = -1
    message = ""
    release_id = -1
    test_set_id = -1

    def __init__(self, project_id, test_case_id, test_name, stack_trace, status_id, start_time, end_time, message='', release_id=-1, test_set_id=-1):
        self.project_id = project_id
        self.test_case_id = test_case_id
        self.test_name = test_name
        self.stack_trace = stack_trace
        self.status_id = status_id
        self.start_time = start_time
        self.end_time = end_time
        self.message = message
        self.release_id = release_id
        self.test_set_id = test_set_id

    def post(self, spira_url, spira_username, spira_token, config, pytest_config):
        """
        Post the test run to Spira with the given credentials
        """
        # Check for dry-run mode
        if pytest_config._spira_dry_run:
            log_message(f"[DRY RUN] Would post test result for: {self.test_name}", "INFO")
            log_message(f"  Test case ID: {self.test_case_id}", "INFO")
            log_message(f"  Status: {self.status_id} ({'PASSED' if self.status_id == 2 else 'FAILED' if self.status_id == 1 else 'SKIPPED'})", "INFO")
            log_message(f"  Duration: {(self.end_time - self.start_time).total_seconds():.2f}s", "INFO")
            if self.release_id != -1:
                log_message(f"  Release ID: {self.release_id}", "INFO")
            if self.test_set_id != -1:
                log_message(f"  Test Set ID: {self.test_set_id}", "INFO")
            return
        
        url = spira_url + self.REST_SERVICE_URL + \
            (self.POST_TEST_RUN % self.project_id)
        # The credentials we need
        params = {
            'username': spira_username,
            'api-key': spira_token
        }

        # The headers we are sending to the server
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': RUNNER_NAME
        }

        # The body we are sending
        body = {
            # Constant for plain text
            'TestRunFormatId': 1,
            'StartDate': self.start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'EndDate': self.end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'RunnerName': RUNNER_NAME,
            'RunnerTestName': self.test_name,
            'RunnerMessage': self.message,
            'RunnerStackTrace': self.stack_trace,
            'TestCaseId': self.test_case_id,
            # Passes (2) if the stack trace length is 0
            'ExecutionStatusId': self.status_id
        }

        # Releases and Test Sets are optional
        if(self.release_id != -1):
            body["ReleaseId"] = int(self.release_id)
        if(self.test_set_id != -1):
            body["TestSetId"] = int(self.test_set_id)

        log_verbose(f"Posting test result to Spira: {url}", config)
        log_verbose(f"Test case ID: {self.test_case_id}, Status: {self.status_id}", config)

        try:
            response = requests.post(url, data=json.dumps(body), params=params, headers=headers, timeout=30)
            response.raise_for_status()
            log_verbose(f"Successfully posted test result for: {self.test_name}", config)
        except requests.exceptions.Timeout:
            log_message(f"Timeout posting test result to Spira for test: {self.test_name}", "ERROR")
            log_message(f"  URL: {url}", "ERROR")
            log_message(f"  Test case ID: {self.test_case_id}", "ERROR")
        except requests.exceptions.ConnectionError as e:
            log_message(f"Connection error posting test result to Spira for test: {self.test_name}", "ERROR")
            log_message(f"  URL: {url}", "ERROR")
            log_message(f"  Error: {str(e)}", "ERROR")
        except requests.exceptions.HTTPError as e:
            log_message(f"HTTP error {response.status_code} posting test result to Spira for test: {self.test_name}", "ERROR")
            log_message(f"  URL: {url}", "ERROR")
            log_message(f"  Test case ID: {self.test_case_id}", "ERROR")
            log_message(f"  Response: {response.text}", "ERROR")
        except requests.exceptions.RequestException as e:
            log_message(f"Error posting test result to Spira for test: {self.test_name}", "ERROR")
            log_message(f"  URL: {url}", "ERROR")
            log_message(f"  Error: {str(e)}", "ERROR")
