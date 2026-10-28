"""Resolve and provision the headless Codespaces SOE and course overlays."""

from __future__ import annotations

import argparse
import copy
import json
import os
import platform as host_platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from packaging.specifiers import SpecifierSet
from packaging.version import Version

CATALOGS = (
    "capabilities",
    "products",
    "software_sources",
    "provider_profiles",
    "platforms",
    "deployment_profiles",
    "lifecycle_workflows",
    "managed_settings",
    "managed_assets",
    "obsolete_components",
    "box_artifacts",
    "launch_profiles",
)
PACKAGE = re.compile(r"[a-z0-9][a-z0-9+.-]*(?::(?:amd64|arm64))?\Z")
EXTENSION = re.compile(r"[A-Za-z0-9-]+\.[A-Za-z0-9._-]+\Z")
PIP_PACKAGE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SOURCES = {
    "ubuntu_archive": "https://archive.ubuntu.com/ubuntu",
    "github_cli_packages": "https://cli.github.com/packages",
    "pypi": "https://pypi.org/simple",
    "vscode_marketplace": "https://marketplace.visualstudio.com",
    "github_codespaces": "https://github.com/features/codespaces",
}


class ConfigurationError(ValueError):
    """A configuration cannot be executed safely or completely."""


def require(condition, message):
    if not condition:
        raise ConfigurationError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(
        Path(path).read_text(encoding="utf-8-sig"),
        object_pairs_hook=unique_object,
    )


def validate(data, schema, definition=None):
    contract = schema
    if definition:
        contract = {"$ref": f"#/$defs/{definition}", "$defs": schema["$defs"]}
    errors = sorted(
        Draft202012Validator(
            contract, format_checker=FormatChecker()
        ).iter_errors(data),
        key=lambda error: str(error.json_path),
    )
    require(
        not errors,
        "Schema validation failed: "
        + "; ".join(
            f"{error.json_path}: {error.message}" for error in errors[:4]
        ),
    )


def inside(root, path):
    resolved = Path(path).resolve()
    require(
        resolved.is_relative_to(root.resolve()),
        f"Path escapes workspace: {path}",
    )
    return resolved


def merge_new(target, additions, label):
    for key, value in additions.items():
        require(key not in target, f"Duplicate catalog ID: {label}/{key}")
        target[key] = copy.deepcopy(value)


def pointer_parent(document, pointer):
    keys = pointer.lstrip("/").split("/")
    node = document
    for key in keys[:-1]:
        require(
            isinstance(node, dict) and key in node,
            f"Missing override target: {pointer}",
        )
        node = node[key]
    require(keys[-1] in node, f"Missing override target: {pointer}")
    return node, keys[-1]


def compose(soe, course, schema):
    validate(soe, schema)
    require(soe["manifest_type"] == "soe", "Expected an SOE manifest")
    resolved = copy.deepcopy(soe)
    resolved.pop("$schema", None)
    permissions = resolved.pop("override_permissions")
    resolved["manifest_type"] = "resolved"
    resolved["configuration_kind"] = "soe"
    if course is None:
        return resolved
    validate(course, schema)
    require(
        course["manifest_type"] == "course", "Expected a CSO course manifest"
    )
    require(
        course["baseline"]["baseline_id"] == soe["baseline"]["baseline_id"],
        "CSO baseline identity mismatch",
    )
    additions = course["additions"]
    for catalog in CATALOGS:
        merge_new(
            resolved.setdefault(catalog, {}),
            additions.get(catalog, {}),
            catalog,
        )
    for platform_id, extension in additions.get(
        "platform_extensions", {}
    ).items():
        require(
            platform_id in resolved["platforms"],
            f"Unknown platform: {platform_id}",
        )
        for catalog, entries in extension.items():
            merge_new(
                resolved["platforms"][platform_id][catalog],
                entries,
                f"platforms/{platform_id}/{catalog}",
            )
    targets = []
    for override in course["overrides"]:
        target = override["target"]
        require(
            not any(
                target == old
                or target.startswith(old + "/")
                or old.startswith(target + "/")
                for old in targets
            ),
            "Overlapping CSO overrides",
        )
        permission = permissions.get(override["permission_id"])
        require(
            permission and permission["target"] == target,
            f"Unauthorized CSO override: {target}",
        )
        require(
            soe["control"]["status"] == "approved",
            "Draft SOE cannot authorize CSO overrides",
        )
        allowlist = permission.get("allowed_course_ids")
        require(
            allowlist is None or course["course"]["course_id"] in allowlist,
            "Course is not eligible for override",
        )
        pointer_parent(soe, target)
        parts = target.lstrip("/").split("/")
        if len(parts) >= 2:
            require(
                parts[1] not in additions.get(parts[0], {}),
                "CSO addition overlaps override",
            )
        if len(parts) == 4 and parts[0] == "platforms":
            require(
                parts[3]
                not in additions.get("platform_extensions", {})
                .get(parts[1], {})
                .get(parts[2], {}),
                "CSO platform extension overlaps override",
            )
        parent, key = pointer_parent(resolved, target)
        parent[key] = copy.deepcopy(override["value"])
        targets.append(target)
    resolved["configuration_kind"] = "cso"
    resolved["course"] = copy.deepcopy(course["course"])
    resolved["baseline_release"] = copy.deepcopy(soe["baseline"])
    resolved["baseline"] = copy.deepcopy(course["baseline"])
    resolved["baseline_control"] = copy.deepcopy(soe["control"])
    resolved["control"] = copy.deepcopy(course["control"])
    resolved["course_environments"] = copy.deepcopy(
        course.get("course_environments", {})
    )
    if "student_distribution" in course:
        resolved["student_distribution"] = copy.deepcopy(
            course["student_distribution"]
        )
    return resolved


def applies(entry, profile_id, profile, platform_id):
    if "platform_ids" in entry and platform_id not in entry["platform_ids"]:
        return False
    selector = entry.get("applies_to", {})
    return all(
        actual in selector[key]
        for key, actual in (
            ("deployment_profile_ids", profile_id),
            ("deployment_kinds", profile["deployment_kind"]),
            ("session_types", profile["session_type"]),
        )
        if key in selector
    )


def scan_selectors(node, profiles):
    if isinstance(node, dict):
        for profile_id in node.get("applies_to", {}).get(
            "deployment_profile_ids", []
        ):
            require(
                profile_id in profiles,
                f"Unknown applicability profile: {profile_id}",
            )
        for value in node.values():
            scan_selectors(value, profiles)
    elif isinstance(node, list):
        for value in node:
            scan_selectors(value, profiles)


def version_ok(version, rule):
    comparison = rule.get("comparison", "presence_only")
    if comparison in {"presence_only", "managed_latest"}:
        return True
    value = rule["value"]
    if comparison == "exact":
        value = "==" + value
    elif comparison == "minimum":
        value = ">=" + value
    return Version(version) in SpecifierSet(value)


def version_rules(product, binding):
    return [
        rule
        for rule in (
            product.get("version_rule"),
            binding.get("version_rule_override"),
            binding.get("verification", {}).get("version_rule"),
        )
        if rule
    ]


def environment_path(workspace, definition):
    template = definition["path"]
    require(
        template.startswith("${COURSE_ROOT}/"),
        "Course environment requires COURSE_ROOT",
    )
    result = inside(
        workspace, workspace / template.removeprefix("${COURSE_ROOT}/")
    )
    require(
        result != workspace.resolve(),
        "Course environment cannot replace workspace",
    )
    return result


def make_plan(resolved, schema, workspace, profile_id):
    profiles = resolved["deployment_profiles"]
    scan_selectors(resolved, profiles)
    require(profile_id in profiles, f"Unknown deployment: {profile_id}")
    profile = profiles[profile_id]
    platform_id = profile["platform_id"]
    require(platform_id in resolved["platforms"], "Unknown deployment platform")
    platform = resolved["platforms"][platform_id]
    for source_id, expected_uri in SOURCES.items():
        source = resolved["software_sources"].get(source_id)
        require(
            source and source["base_uri"].rstrip("/") == expected_uri,
            f"Unsupported source configuration: {source_id}",
        )
    require(
        profile["enabled"] and platform["enabled"],
        "Deployment or platform is disabled",
    )
    require(
        profile_id == "github_codespaces"
        and profile.get("profile_adapter_id") == "codespaces_devcontainer",
        "This adapter implements the Codespaces deployment only",
    )
    require(
        profile["deployment_kind"] == "container"
        and platform["os"]["family"] == "linux",
        "Expected Linux container deployment",
    )
    references = [
        p for p in profiles.values() if p["enabled"] and p["reference_profile"]
    ]
    require(
        len(references) == 1,
        "Exactly one primary reference deployment is required",
    )
    reference_platforms = [
        key
        for key, p in resolved["platforms"].items()
        if p["enabled"] and p["reference_platform"]
    ]
    require(
        reference_platforms == [references[0]["platform_id"]],
        "Reference platform/deployment mismatch",
    )
    for workflow_id in profile["allowed_workflow_ids"]:
        workflow = resolved["lifecycle_workflows"].get(workflow_id)
        require(
            workflow and profile_id in workflow["deployment_profile_ids"],
            "Workflow authorization mismatch",
        )
        require(
            workflow.get("interaction_mode") == "noninteractive",
            "Codespaces lifecycle must be noninteractive",
        )
    for action in ("runtime_initial_install", "runtime_verify"):
        require(
            action in profile["allowed_workflow_ids"],
            f"Missing workflow: {action}",
        )
    resolved["selected_deployment_profile_id"] = profile_id
    validate(resolved, schema, "resolvedConfiguration")

    def selected(entry):
        return applies(entry, profile_id, profile, platform_id)

    capabilities = {
        key: value
        for key, value in resolved["capabilities"].items()
        if selected(value)
    }
    bindings = {}
    for key, binding in platform["capability_bindings"].items():
        require(
            key in resolved["capabilities"],
            f"Unknown capability binding: {key}",
        )
        if (
            key in capabilities
            and selected(binding)
            and (binding["required"] or capabilities[key]["required"])
        ):
            require(
                binding["required"],
                f"Required capability disabled by binding: {key}",
            )
            bindings[key] = binding
    for key, capability in capabilities.items():
        require(
            not capability["required"] or key in bindings,
            f"Missing required capability: {key}",
        )
    packages, extensions, environments = [], [], {}
    for key, definition in platform["os_packages"].items():
        if definition["required"] and selected(definition):
            require(
                definition["source_id"] == "ubuntu_archive",
                f"Unsupported OS package source: {key}",
            )
            require(
                PACKAGE.fullmatch(definition["package_identifier"]),
                f"Invalid APT identifier: {key}",
            )
            require(
                definition.get("version_rule", {}).get(
                    "comparison", "presence_only"
                )
                in {"presence_only", "managed_latest"},
                "Versioned support packages need an implementation",
            )
            packages.append(definition["package_identifier"])
    for key, binding in bindings.items():
        for dependency in set(
            capabilities[key].get("depends_on", [])
            + binding.get("dependencies", [])
        ):
            require(
                dependency in bindings,
                f"Missing applicable dependency: {key} -> {dependency}",
            )
        require(
            binding["product_id"] in resolved["products"],
            f"Unknown product: {key}",
        )
        product = resolved["products"][binding["product_id"]]
        for rule in version_rules(product, binding):
            version_ok("3.10.0", rule)
        require(
            key in product["capability_roles"],
            f"Product does not implement capability: {key}",
        )
        require(
            binding["source_id"] in resolved["software_sources"],
            f"Unknown source: {key}",
        )
        if "provider_profile_id" in binding:
            require(
                binding["provider_profile_id"] in resolved["provider_profiles"],
                f"Unknown provider: {key}",
            )
            authentication = resolved["provider_profiles"][
                binding["provider_profile_id"]
            ]["authentication"]
            require(
                not authentication["interactive"],
                "Codespaces provisioning cannot initiate interactive login",
            )
        for setting_id in binding.get("settings_profile_ids", []):
            require(
                setting_id in resolved["managed_settings"],
                f"Unknown settings profile: {setting_id}",
            )
        adapter = binding["installer_adapter_id"]
        if adapter == "apt_package":
            require(
                binding["product_id"] == "python"
                or all(
                    rule["comparison"] in {"presence_only", "managed_latest"}
                    for rule in version_rules(product, binding)
                ),
                f"Unsupported versioned APT component: {key}",
            )
            require(
                binding["source_id"]
                in platform["package_manager"]["source_ids"],
                f"APT source not enabled: {key}",
            )
            require(
                binding["source_id"]
                in {"ubuntu_archive", "github_cli_packages"},
                f"Unsupported APT source: {key}",
            )
            require(
                PACKAGE.fullmatch(binding["package_identifier"]),
                f"Invalid APT identifier: {key}",
            )
            packages.append(binding["package_identifier"])
        elif adapter == "devcontainer_extension":
            extension = binding["package_identifier"]
            require(
                binding["source_id"] == "vscode_marketplace"
                and EXTENSION.fullmatch(extension),
                "Invalid extension source or ID",
            )
            require(
                all(
                    rule["comparison"] == "presence_only"
                    for rule in version_rules(product, binding)
                ),
                "Versioned editor extensions need a supported adapter",
            )
            extensions.append(extension)
        elif adapter == "codespaces_editor":
            require(
                binding["installation_scope"] == "provider_managed"
                and binding["source_id"] == "github_codespaces",
                "Invalid managed editor binding",
            )
        elif adapter == "python_venv_package":
            require(
                binding["source_id"] == "pypi"
                and PIP_PACKAGE.fullmatch(binding["package_identifier"]),
                "Only named PyPI packages are supported",
            )
            environment_id = binding["environment_id"]
            definition = resolved.get("course_environments", {}).get(
                environment_id
            )
            require(
                definition and selected(definition),
                f"Missing applicable course environment: {environment_id}",
            )
            require(
                definition["runtime_capability_id"]
                == "programming_language_runtime",
                "Course environments require the selected Python runtime",
            )
            require(
                definition["runtime_capability_id"] in bindings,
                "Missing course interpreter capability",
            )
            environments[environment_id] = str(
                environment_path(workspace, definition)
            )
        else:
            raise ConfigurationError(
                f"Unsupported Codespaces installer: {adapter}"
            )
    require(
        len(set(environments.values())) == len(environments),
        "Course environments cannot share directories",
    )
    for asset in resolved["managed_assets"].values():
        require(
            not selected(asset),
            "Applicable managed assets need a supported Codespaces adapter",
        )
    require(
        not any(
            selected(item) for item in resolved["obsolete_components"].values()
        ),
        "Applicable removal operations need a supported Codespaces adapter",
    )
    settings = []
    setting_keys = set()
    for setting in resolved["managed_settings"].values():
        if selected(setting) and setting["scope"] == "workspace":
            require(
                setting["settings_adapter_id"] == "vscode_workspace_settings",
                "Unsupported workspace settings adapter",
            )
            require(
                setting["target_path"].startswith("${WORKSPACE_ROOT}/"),
                "Invalid workspace settings path",
            )
            destination_path = inside(
                workspace,
                workspace
                / setting["target_path"].removeprefix("${WORKSPACE_ROOT}/"),
            )
            for key in setting["values"]:
                destination = (str(destination_path), key)
                require(
                    destination not in setting_keys,
                    "Conflicting managed workspace settings",
                )
                setting_keys.add(destination)
            settings.append(setting)
    return {
        "configuration_kind": resolved["configuration_kind"],
        "workspace": str(workspace.resolve()),
        "deployment": profile_id,
        "platform": platform_id,
        "profile": profile,
        "packages": sorted(set(packages)),
        "extensions": sorted(set(extensions)),
        "bindings": bindings,
        "environments": environments,
        "settings": settings,
        "resolved": resolved,
    }


def load_plan(
    atlas_root, workspace, mode="auto", profile_id="github_codespaces"
):
    atlas_root, workspace = atlas_root.resolve(), workspace.resolve()
    schema = read_json(atlas_root / ".config/manifest.schema.json")
    soe = read_json(atlas_root / ".config/soe_manifest.json")
    course_path = workspace / ".config/cso_manifest.json"
    if mode == "auto":
        mode = "cso" if course_path.is_file() else "soe"
        require(
            mode == "cso"
            or (workspace / ".config/soe_manifest.json").is_file(),
            "Course checkout requires .config/cso_manifest.json; "
            "choose --mode soe explicitly for an SOE-only workspace",
        )
    course = read_json(course_path) if mode == "cso" else None
    return make_plan(
        compose(soe, course, schema), schema, workspace, profile_id
    )


def run(args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def check_host(plan):
    require(sys.platform == "linux", "Provisioning requires a Linux container")
    facts = dict(
        line.split("=", 1)
        for line in Path("/etc/os-release").read_text().splitlines()
        if "=" in line
    )
    require(facts.get("ID", "").strip('"') == "ubuntu", "Expected Ubuntu")
    require(
        facts["VERSION_ID"].strip('"') == plan["profile"]["os_release_id"],
        "Ubuntu release does not match deployment",
    )
    architecture = {"amd64": "x86_64", "aarch64": "arm64"}.get(
        host_platform.machine(), host_platform.machine()
    )
    require(
        architecture == plan["profile"]["architecture"],
        "Architecture does not match deployment",
    )


def apt_installed(package):
    result = subprocess.run(
        ["dpkg-query", "-W", "-f=${Status}", package],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout == "install ok installed"


def install_system(plan):
    check_host(plan)
    require(os.geteuid() == 0, "System installation requires root")
    missing = [
        package for package in plan["packages"] if not apt_installed(package)
    ]
    if missing:
        run(["apt-get", "update"])
        run(
            ["apt-get", "install", "-y", "--no-install-recommends", *missing],
            env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"},
        )


def interpreter(environment):
    return Path(environment) / "bin/python"


def pip_requirement(plan, binding):
    requirements = []
    product = plan["resolved"]["products"][binding["product_id"]]
    for rule in version_rules(product, binding):
        comparison = rule["comparison"]
        if comparison in {"presence_only", "managed_latest"}:
            continue
        value = rule["value"]
        requirements.append(
            {"minimum": ">=", "exact": "=="}.get(comparison, "") + value
        )
    return binding["package_identifier"] + ",".join(requirements)


def installed_package_version(python, binding):
    query = (
        "import importlib.metadata,sys; "
        "print(importlib.metadata.version(sys.argv[1]))"
    )
    result = subprocess.run(
        [str(python), "-c", query, binding["package_identifier"]],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return None
    return result.stdout.strip()


def package_satisfied(python, binding, plan):
    installed = installed_package_version(python, binding)
    if installed is None:
        return False
    product = plan["resolved"]["products"][binding["product_id"]]
    return all(
        version_ok(installed, rule) for rule in version_rules(product, binding)
    )


def merge_settings(target, values):
    for key, value in values.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            merge_settings(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def contains_settings(actual, expected):
    return isinstance(actual, dict) and all(
        key in actual
        and (
            contains_settings(actual[key], value)
            if isinstance(value, dict)
            else actual[key] == value
        )
        for key, value in expected.items()
    )


def verify_course_interpreter(plan, environment):
    python = interpreter(environment)
    require(python.is_file(), "Missing course environment")
    version = run(
        [python, "-c", "import platform; print(platform.python_version())"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    runtime = plan["bindings"]["programming_language_runtime"]
    product = plan["resolved"]["products"][runtime["product_id"]]
    require(
        all(
            version_ok(version, rule)
            for rule in version_rules(product, runtime)
        ),
        "Course interpreter is incompatible; rebuild its venv explicitly",
    )


def setup(plan, workspace, atlas_root, mode):
    check_host(plan)
    require(os.geteuid() != 0, "Course setup must run as the development user")
    if any(not apt_installed(package) for package in plan["packages"]):
        run(
            [
                "sudo",
                "-n",
                sys.executable,
                Path(__file__).resolve(),
                "install-system",
                "--atlas-root",
                atlas_root,
                "--workspace",
                workspace,
                "--mode",
                mode,
            ]
        )
    verify(plan, editor=False, course_packages=False)
    for environment in plan["environments"].values():
        require(
            not Path(environment).is_symlink(),
            "Course environment cannot be a symlink",
        )
        if not interpreter(environment).exists():
            run(["/usr/bin/python3", "-m", "venv", environment])
        require(
            inside(workspace, environment) == Path(environment),
            "Invalid environment directory",
        )
        verify_course_interpreter(plan, environment)
    for binding in plan["bindings"].values():
        if binding["installer_adapter_id"] == "python_venv_package":
            python = interpreter(
                plan["environments"][binding["environment_id"]]
            )
            if not package_satisfied(python, binding, plan):
                require(
                    installed_package_version(python, binding) is None,
                    "Existing course package is incompatible; "
                    "resolve the conflict explicitly before setup",
                )
                run(
                    [
                        python,
                        "-m",
                        "pip",
                        "install",
                        "--disable-pip-version-check",
                        "--index-url",
                        "https://pypi.org/simple/",
                        pip_requirement(plan, binding),
                    ]
                )
    for setting in plan["settings"]:
        target = inside(
            workspace,
            workspace
            / setting["target_path"].removeprefix("${WORKSPACE_ROOT}/"),
        )
        if target.exists() and setting["merge_policy"] == "create_if_missing":
            continue
        values = read_json(target) if target.exists() else {}
        merge_settings(values, setting["values"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8")
    verify(plan, editor=False)


def verify(plan, editor=False, course_packages=True):
    check_host(plan)
    if course_packages:
        for environment in plan["environments"].values():
            verify_course_interpreter(plan, environment)
    for setting in plan["settings"]:
        if not course_packages:
            continue
        workspace = Path(plan["workspace"])
        target = inside(
            workspace,
            workspace
            / setting["target_path"].removeprefix("${WORKSPACE_ROOT}/"),
        )
        require(target.is_file(), "Missing managed workspace settings")
        if setting["merge_policy"] != "create_if_missing":
            require(
                contains_settings(read_json(target), setting["values"]),
                "Managed workspace settings do not match requirements",
            )
    for package in plan["packages"]:
        require(apt_installed(package), f"Missing APT package: {package}")
    for key, binding in plan["bindings"].items():
        adapter = binding["installer_adapter_id"]
        product = plan["resolved"]["products"][binding["product_id"]]
        if adapter == "apt_package":
            commands = binding["verification"].get("executable_names", [])
            require(
                not commands
                or any(shutil.which(command) for command in commands),
                f"Missing executable: {key}",
            )
            if product["product_kind"] == "programming_runtime":
                require(
                    binding["product_id"] == "python",
                    "Unsupported runtime verification",
                )
                result = run(
                    [
                        "/usr/bin/python3",
                        "-c",
                        "import platform; print(platform.python_version())",
                    ],
                    capture_output=True,
                    text=True,
                )
                require(
                    all(
                        version_ok(result.stdout.strip(), rule)
                        for rule in version_rules(product, binding)
                    ),
                    "Python version does not satisfy the selected requirements",
                )
            else:
                require(
                    all(
                        rule["comparison"]
                        in {"presence_only", "managed_latest"}
                        for rule in version_rules(product, binding)
                    ),
                    f"Unsupported component version verification: {key}",
                )
        elif adapter == "python_venv_package" and course_packages:
            python = interpreter(
                plan["environments"][binding["environment_id"]]
            )
            require(python.is_file(), f"Missing course environment: {key}")
            require(
                package_satisfied(python, binding, plan),
                f"Missing/incompatible course package: {key}",
            )
    if editor:
        require(
            shutil.which("code"),
            "Managed VS Code CLI is not available; attach the editor first",
        )
        installed = (
            run(["code", "--list-extensions"], capture_output=True, text=True)
            .stdout.casefold()
            .splitlines()
        )
        for extension in plan["extensions"]:
            require(
                extension.casefold() in installed,
                f"Missing editor extension: {extension}; "
                "regenerate the devcontainer and rebuild",
            )
    print(
        f"Verified {plan['configuration_kind'].upper()} runtime: "
        "Ubuntu 22.04, Python 3.10; "
        + (
            "editor extensions verified."
            if editor
            else "editor extensions are checked separately after attachment."
        )
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("plan", "install-system", "setup", "verify", "devcontainer"),
    )
    parser.add_argument(
        "--atlas-root",
        type=Path,
        default=Path(
            os.environ.get("ATLAS_ROOT", Path(__file__).resolve().parents[1])
        ),
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument(
        "--mode", choices=("auto", "soe", "cso"), default="auto"
    )
    parser.add_argument("--deployment", default="github_codespaces")
    parser.add_argument("--editor", action="store_true")
    parser.add_argument(
        "--image", help="Published SOE image for a course devcontainer"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check generated devcontainer for drift",
    )
    args = parser.parse_args(argv)
    try:
        plan = load_plan(
            args.atlas_root, args.workspace, args.mode, args.deployment
        )
        if args.action == "plan":
            print(
                json.dumps(
                    {
                        key: value
                        for key, value in plan.items()
                        if key != "resolved"
                    },
                    indent=2,
                )
            )
        elif args.action == "install-system":
            install_system(plan)
        elif args.action == "setup":
            setup(
                plan,
                args.workspace.resolve(),
                args.atlas_root.resolve(),
                plan["configuration_kind"],
            )
        elif args.action == "verify":
            verify(plan, args.editor)
        elif args.action == "devcontainer":
            from devcontainer_config import configuration

            generated = configuration(plan, image=args.image)
            target = args.workspace / ".devcontainer/devcontainer.json"
            if args.check:
                require(
                    read_json(target) == generated,
                    "devcontainer.json differs from SOE/CSO; regenerate it",
                )
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    json.dumps(generated, indent=2) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
    except (
        ConfigurationError,
        OSError,
        ValueError,
        KeyError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"SOE: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
