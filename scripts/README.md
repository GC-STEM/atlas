<!-- To see this file in a clean, formatted view, select ▼ in the upper-right corner of the editor pane, then select "Markdown Preview".-->

# GC-STEM Atlas Scripts

---

> [!WARNING]
> This page and associated scripts are under active development and may change frequently. They are not ready for student or faculty use

---

{{Welcome and overview}}

The headless Codespaces implementation uses `soe.py` for SOE/CSO resolution,
setup, and verification, `devcontainer_config.py` for editor configuration,
and `launch_codespaces.py` for the selected checkout's launch page. See the
[Codespaces guide](../.devcontainer/README.md). The platform lifecycle files
below remain placeholders; they are not used by the Codespaces hooks.

## Table of Contents <!-- omit from toc -->

1. [Lifecycle Scripts](#lifecycle-scripts)
2. [System Information Scripts](#system-information-scripts)
3. [System Information Script](#system-information-script)

## Lifecycle Scripts

### Setup Script

The purpose of the setup script is to automate the entire repository lifecycle, including preparation, installation, configuration, updates, repairs, and verification of the Standard Operating Environment (SOE) and the specified Course-specific overlay (CSO) based on the SOE and CSO manifest files.

```shell
setup.<ext> <repo>
```

### Preparation Script

The purpose of the preparation script is to set up the environment and prerequisites required for the Standard Operating Environment (SOE) and the specified Course-specific overlay (CSO) before running the setup script.

```shell
prepare.<ext> <repo>
```

### Install Script

The purpose of the install script is to install the the specified Course-specific overlay (CSO) on top of Standard Operating Environment (SOE).

```shell
install.<ext> <repo>
```

### Configure Script

The purpose of the configure script is to configure the Standard Operating Environment (SOE), if not already, and the specified Course-specific overlay (CSO) after installation.

```shell
configure.<ext> <repo>
```

### Update Script

The purpose of the update script is to apply updates allowed by the selected Standard Operating Environment (SOE) and Course-specific overlay (CSO) manifests. The SOE follows current Ubuntu LTS − 1 and that release's default CPython minor version; updates may advance patches within the manifest-selected lines. A different Ubuntu LTS or Python minor version requires a reviewed SOE release rather than an automatic lifecycle update.

```shell
update.<ext> <repo>
```

### Repair Script

The purpose of the repair script is to repair the Standard Operating Environment (SOE) and the specified Course-specific overlay (CSO) if any issues are detected.

```shell
repair.<ext> <repo>
```

### Verify Script

The purpose of this read-only verify script is to verify that the Standard Operating Environment (SOE) and the specified Course-specific overlay (CSO) are installed and configured correctly.

```shell
verify.<ext> <repo>
```

## System Information Scripts

## System Information Script

The purpose of the system information script is to gather and display detailed information about the system environment, including hardware, software, and configuration details relevant to the Standard Operating Environment (SOE) and the specified Course-specific overlay (CSO).

```shell
sysinfo.<ext> <repo>
```
