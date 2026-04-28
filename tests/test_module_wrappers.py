import semantic_sift.kernel as kernel_wrapper
import semantic_sift.telemetry as telemetry_wrapper
import semantic_sift.hook as hook_wrapper
import semantic_sift.server as server_wrapper
import semantic_sift.onboarding as onboarding_wrapper
import semantic_sift.hook_injector as hook_injector_wrapper
import semantic_sift.tools as tools_wrapper


def test_kernel_wrapper_exports_expected_function():
    assert hasattr(kernel_wrapper, "perform_semantic_sift")


def test_telemetry_wrapper_exports_expected_function():
    assert hasattr(telemetry_wrapper, "log_telemetry")


def test_hook_wrapper_exports_main():
    assert hasattr(hook_wrapper, "main")


def test_server_wrapper_exports_main():
    assert hasattr(server_wrapper, "main")


def test_onboarding_wrapper_exports_apply_onboarding():
    assert hasattr(onboarding_wrapper, "apply_onboarding")


def test_hook_injector_wrapper_exports_builder():
    assert hasattr(hook_injector_wrapper, "build_runtime_hook_command")


def test_tools_wrapper_exports_register_tools():
    assert hasattr(tools_wrapper, "register_tools")
