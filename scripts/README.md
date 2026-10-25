<!-- To see this file in a clean, formatted view, select ▼ in the upper-right corner of the editor pane, then select "Markdown Preview".-->

# GC-STEM Atlas Scripts

---

> [!WARNING]
> This page and associated scripts are under active development and may change frequently. They are not ready for student or faculty use

---

{{Welcome and overview}}

## Table of Contents <!-- omit from toc -->

1. [Lifecycle Scripts](#lifecycle-scripts)
2. [System Information Scripts](#system-information-scripts)
3. [System Information Script](#system-information-script)

## Lifecycle Scripts

### Setup Script

The purpose of the setup script is to automate the entire repository lifecycle, including preparation, installation, configuration, updates, repairs, and verification of the STEM Computing Baseline (SCB) and the specified Course Development Environment (CDE) based on the SCB and CDE manifest files.

```shell
setup.<ext> <repo>
```

### Preparation Script

The purpose of the preparation script is to set up the environment and prerequisites required for the STEM Computing Baseline (SCB) and the specified Course Development Environment (CDE) before running the setup script.

```shell
prepare.<ext> <repo>
```

### Install Script

The purpose of the install script is to install the the specified Course Development Environment (CDE) on top of STEM Computing Baseline (SCB).

```shell
install.<ext> <repo>
```

### Configure Script

The purpose of the configure script is to configure the STEM Computing Baseline (SCB), if not already, and the specified Course Development Environment (CDE) after installation.

```shell
configure.<ext> <repo>
```

### Update Script

The purpose of the update script is to update the STEM Computing Baseline (SCB) and the specified Course Development Environment (CDE) to the latest versions.

```shell
update.<ext> <repo>
```

### Repair Script

The purpose of the repair script is to repair the STEM Computing Baseline (SCB) and the specified Course Development Environment (CDE) if any issues are detected.

```shell
repair.<ext> <repo>
```

### Verify Script

The purpose of this read-only verify script is to verify that the STEM Computing Baseline (SCB) and the specified Course Development Environment (CDE) are installed and configured correctly.

```shell
verify.<ext> <repo>
```

## System Information Scripts

## System Information Script

The purpose of the system information script is to gather and display detailed information about the system environment, including hardware, software, and configuration details relevant to the STEM Computing Baseline (SCB) and the specified Course Development Environment (CDE).

```shell
sysinfo.<ext> <repo>
```
