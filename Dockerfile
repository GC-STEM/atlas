# syntax=docker/dockerfile:1

# GC-STEM STEM Computing Baseline (SCB)
# Course Reference Environment (CRE) -- Ubuntu container
#
# Source of truth:
#   GC-STEM/atlas/.config/scb_manifest.json
#
# This image contains the SCB only.
# Course-specific requirements belong in downstream CRE images.

ARG UBUNTU_RELEASE=24.04
FROM ubuntu:${UBUNTU_RELEASE}

LABEL org.opencontainers.image.title="GC-STEM SCB"
LABEL org.opencontainers.image.description="Manifest-driven STEM Computing Baseline"
LABEL org.opencontainers.image.source="https://github.com/GC-STEM/atlas"

ARG SCB_PLATFORM=cvd

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    TZ=Etc/UTC \
    SCB_PLATFORM=${SCB_PLATFORM} \
    SCB_MANIFEST=/opt/gc-stem/scb_manifest.json

# Bootstrap dependencies for the manifest-driven installer.
# These are installer prerequisites, not a duplicated SCB package list.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gpg \
        python3 \
    && rm -rf /var/lib/apt/lists/*

# Copy the authoritative SCB manifest from the Atlas build context.
COPY .config/scb_manifest.json /opt/gc-stem/scb_manifest.json

# Resolve and install required SCB components.
RUN python3 - <<'PY'
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

manifest = json.loads(Path(os.environ["SCB_MANIFEST"]).read_text())
platform_id = os.environ["SCB_PLATFORM"]

def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def require(condition, message):
    if not condition:
        raise SystemExit(message)

require(manifest["manifest_type"] == "scb", "Expected SCB manifest")
require(manifest["schema_version"] == "3.0", "Unsupported schema version")

platform = manifest["platforms"][platform_id]
require(platform["enabled"], "Selected platform is disabled")
require(platform["os"]["family"] == "linux", "Expected Linux platform")
require(platform["package_manager"]["adapter_id"] == "apt", "Expected APT")

os_release = dict(
    line.strip().split("=", 1)
    for line in Path("/etc/os-release").read_text().splitlines()
    if "=" in line
)
installed_release = os_release["VERSION_ID"].strip('"')
supported = {
    item["release_id"]
    for item in platform["os"]["releases"]
}
require(installed_release in supported, "Ubuntu release does not match SCB")

architecture = run(
    "dpkg", "--print-architecture",
    capture_output=True, text=True
).stdout.strip()
architecture_map = {"amd64": "x86_64", "arm64": "arm64"}
require(
    architecture_map.get(architecture) in platform["os"]["architectures"],
    "Architecture does not match SCB"
)

capabilities = manifest["capabilities"]
products = manifest["products"]
sources = manifest["software_sources"]
bindings = platform["cde_bindings"]

packages = set()
extensions = set()
required_sources = set()

def check_rule(rule, context):
    require(
        rule.get("comparison", "presence_only") == "presence_only",
        f"Unsupported version rule for {context}: {rule}"
    )

def add_package(definition, context):
    require(
        definition["installer_adapter_id"] == "apt_package",
        f"Unsupported installer for {context}"
    )
    source_id = definition["source_id"]
    require(source_id in sources, f"Unknown source: {source_id}")
    require(
        source_id in platform["package_manager"]["source_ids"],
        f"Source not enabled for platform: {source_id}"
    )
    packages.add(definition["package_identifier"])
    required_sources.add(source_id)

for package_id, definition in platform.get("os_packages", {}).items():
    if not definition.get("required", False):
        continue
    require(
        definition["source_id"] in sources,
        f"Unknown source for {package_id}"
    )
    check_rule(definition.get("version_rule", {}), package_id)
    packages.add(definition["package_identifier"])
    required_sources.add(definition["source_id"])

for capability_id, capability in capabilities.items():
    if capability.get("required", False):
        require(
            capability_id in bindings,
            f"Missing required capability binding: {capability_id}"
        )

for capability_id, definition in bindings.items():
    required = definition.get(
        "required",
        capabilities[capability_id].get("required", False)
    )
    if not required:
        continue

    product_id = definition["product_id"]
    require(product_id in products, f"Unknown product: {product_id}")
    product = products[product_id]

    adapter = definition["installer_adapter_id"]
    if adapter == "apt_package":
        add_package(definition, capability_id)
    elif adapter == "vscode_extension":
        require(
            definition["source_id"] in sources,
            f"Unknown extension source: {capability_id}"
        )
        require(
            product["version_rule"]["comparison"] == "presence_only",
            f"Unsupported extension version rule: {product_id}"
        )
        extensions.add(definition["package_identifier"])
    else:
        raise SystemExit(
            f"Unsupported installer adapter: {adapter}"
        )

# Configure trusted vendor APT repositories only when required.
Path("/etc/apt/keyrings").mkdir(parents=True, exist_ok=True)

def download(url, destination):
    with urllib.request.urlopen(url, timeout=60) as response:
        Path(destination).write_bytes(response.read())

def verify_key(path, fingerprints):
    result = run(
        "gpg", "--show-keys", "--with-colons", str(path),
        capture_output=True, text=True
    )
    require(
        any(fp in result.stdout for fp in fingerprints),
        f"Unexpected repository signing key: {path}"
    )

for source_id in sorted(required_sources):
    source = sources[source_id]
    adapter = source["adapter_id"]
    uri = source["base_uri"].rstrip("/")

    if adapter == "apt_source":
        continue

    require(
        adapter == "apt_vendor_source",
        f"Unsupported repository adapter: {adapter}"
    )

    if source_id == "github_cli_packages":
        require(
            uri == "https://cli.github.com/packages",
            "Unexpected GitHub CLI repository"
        )
        key = "/etc/apt/keyrings/githubcli.gpg"
        download(f"{uri}/githubcli-archive-keyring.gpg", key)
        verify_key(key, {
            "2C6106201985B60E6C7AC87323F3D4EA75716059",
            "7F38BBB59D064DBCB3D84D725612B36462313325",
        })
        Path("/etc/apt/sources.list.d/github-cli.list").write_text(
            f"deb [arch={architecture} signed-by={key}] "
            f"{uri} stable main\n"
        )

    elif source_id == "microsoft_vscode_packages":
        require(
            uri == "https://packages.microsoft.com/repos/code",
            "Unexpected VS Code repository"
        )
        ascii_key = "/tmp/microsoft.asc"
        key = "/etc/apt/keyrings/microsoft.gpg"
        download(
            "https://packages.microsoft.com/keys/microsoft.asc",
            ascii_key
        )
        verify_key(ascii_key, {
            "BC528686B50D79E339D3721CEB3E94ADBE1229CF",
        })
        run("gpg", "--batch", "--yes", "--dearmor",
            "--output", key, ascii_key)
        Path("/etc/apt/sources.list.d/vscode.list").write_text(
            f"deb [arch={architecture} signed-by={key}] "
            f"{uri} stable main\n"
        )

    else:
        raise SystemExit(f"No trusted APT adapter for: {source_id}")

# Install all manifest-selected APT packages.
run("apt-get", "update")
run(
    "apt-get", "install", "-y", "--no-install-recommends",
    *sorted(packages)
)

# Honor the manifest's Python executable verification requirements.
python_binding = bindings.get("programming_language_runtime")
if python_binding and python_binding.get("required", False):
    executables = python_binding.get(
        "verification", {}
    ).get("executable_names", [])

    if "python" in executables and shutil.which("python") is None:
        run(
            "apt-get", "install", "-y", "--no-install-recommends",
            "python-is-python3"
        )

    product = products[python_binding["product_id"]]
    rule = python_binding.get(
        "verification", {}
    ).get("version_rule", product.get("version_rule", {}))

    if rule.get("comparison") == "compatible_range":
        version = sys.version_info[:3]

        for constraint in rule["value"].split(","):
            match = re.fullmatch(
                r"(>=|<=|==|!=|>|<)(\d+(?:\.\d+)*)",
                constraint.strip()
            )
            require(match is not None, "Unsupported Python version rule")
            operator, target = match.groups()
            parts = tuple(map(int, target.split(".")))
            actual = version[:len(parts)]
            comparisons = {
                ">=": actual >= parts,
                "<=": actual <= parts,
                "==": actual == parts,
                "!=": actual != parts,
                ">": actual > parts,
                "<": actual < parts,
            }
            require(
                comparisons[operator],
                f"Python {version} violates {constraint}"
            )
    else:
        check_rule(rule, "Python")

# Verify required installed executables.
for capability_id, definition in bindings.items():
    if not definition.get("required", False):
        continue
    if definition["installer_adapter_id"] != "apt_package":
        continue

    for executable in definition.get(
        "verification", {}
    ).get("executable_names", []):
        require(
            shutil.which(executable) is not None,
            f"Missing executable: {executable}"
        )

# Preserve the resolved extension list for non-root installation.
Path("/opt/gc-stem/extensions.json").write_text(
    json.dumps(sorted(extensions))
)

# Unsupported managed assets must never be silently omitted.
require(
    not manifest.get("managed_assets"),
    "Managed assets require an approved container adapter"
)

run("apt-get", "clean")
shutil.rmtree("/var/lib/apt/lists", ignore_errors=True)

print(
    f"SCB {manifest['baseline']['version']}: "
    f"{len(packages)} APT packages, "
    f"{len(extensions)} VS Code extensions selected"
)
PY

# Use a predictable, non-root account.
RUN groupadd --gid 1000 codio \
    && useradd \
        --uid 1000 \
        --gid 1000 \
        --create-home \
        --shell /bin/bash \
        codio \
    && mkdir -p /workspace \
    && chown codio:codio /workspace

USER codio

# Install required IDE extensions and manifest-managed user settings.
RUN python3 - <<'PY'
import json
import os
import subprocess
from pathlib import Path

manifest = json.loads(Path(os.environ["SCB_MANIFEST"]).read_text())
platform_id = os.environ["SCB_PLATFORM"]
bindings = manifest["platforms"][platform_id]["cde_bindings"]

def run(*args):
    subprocess.run(args, check=True)

extensions = json.loads(
    Path("/opt/gc-stem/extensions.json").read_text()
)

for extension in extensions:
    run("code", "--install-extension", extension, "--force")

installed = subprocess.run(
    ["code", "--list-extensions"],
    check=True, capture_output=True, text=True
).stdout.casefold().splitlines()

for extension in extensions:
    if extension.casefold() not in installed:
        raise SystemExit(f"Missing VS Code extension: {extension}")

settings_ids = set()
for binding in bindings.values():
    if binding.get("required", False):
        settings_ids.update(binding.get("settings_profile_ids", []))

for setting_id in sorted(settings_ids):
    setting = manifest["managed_settings"][setting_id]

    if platform_id not in setting["platform_ids"]:
        continue

    adapter = setting["settings_adapter_id"]
    values = setting["values"]

    if adapter == "git_global_config":
        for key, value in values.items():
            if isinstance(value, bool):
                value = str(value).lower()
            run("git", "config", "--global", key, str(value))

    elif adapter == "vscode_user_settings":
        target = (
            Path.home() / ".config/Code/User/settings.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(values, indent=2) + "\n"
        )

    else:
        raise SystemExit(
            f"Unsupported settings adapter: {adapter}"
        )

print("SCB extensions and user settings configured")
PY

WORKDIR /workspace

# No SSH, privileged execution, or background services.
# Runtime resource and network restrictions belong to docker run.
CMD ["/bin/bash"]
