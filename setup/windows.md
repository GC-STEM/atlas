<!-- markdownlint-disable-file MD041 -->

---
> [!WARNING]
> This page is under construction. Please check back later for faculty-specific guidance and resources.

---

Welcome to *SOE Setup on Windows*! This document provides step-by-step instructions for setting up the STEM Standard Operating Environment (SOE) on Windows using [**Windows Terminal**](https://learn.microsoft.com/windows/terminal/) and [**PowerShell**], a command-line shell.

Follow these steps to set up the SOE on Windows:

1. [Prepare for the SOE](#prepare-for-the-soe)
2. [Install the SOE](#install-the-soe)
3. [Clone the Atlas repository](#clone-the-atlas-repository)
4. [Configure the SOE](#configure-the-soe)
5. [Verify the SOE](#verify-the-soe)
6. [Help and Support](#help-and-support)

## Prepare for the SOE

1. **Switch out of S mode**, if enabled. [How to check?](https://github.com/GC-STEM/atlas/wiki/Troubleshoot-Win#verification-check-for-s-mode) [How to switch?](https://support.microsoft.com/windows/experience/platform-variants/switching-out-of-s-mode-in-windows)

   **Expected Output**.

   **Troubleshooting**.

1. **Create a restore point** and label it, `Before SOE install`. [How?](https://support.microsoft.com/windows/experience/backup-recovery/system-protection) This step is optional but recommended in case you need to revert your system to its previous state.

1. **Open a terminal window**. [What's this?](https://learn.microsoft.com/windows/terminal/)
   **Procedure**.
   1. Open the Windows Power User Menu.
      - *Keyboard*. Press **Windows key (⊞)** + **X**.
      - *Mouse*. Right-click on **Start (⊞)** icon.
   1. Select **Terminal** or **PowerShell**, depending on your Windows version.

   **Expected Output**.

   **Troubleshooting**.

1. **Verify WinGet is installed** [What's this?](https://learn.microsoft.com/windows/package-manager/)

   **Procedure**. Type the following command exactly as it appears below and press **Enter**.

   <!-- ci:command-test id=verify-winget fixture=empty-repos expect=repo -->
   ```powershell
   winget -v
   ```

   **Expected Output**. A version number in the format `vX.Y.Z`, such as `v1.29.380`. Your version number will be different, which is expected and does not indicate an error. The key indicator of success is that WinGet displays a version number. If it does, continue to the next step.

   **Troubleshooting**. If the command does not display the expected output, follow [{{SME TODO}}](). Do **NOT** continue with the remaining setup tasks until this command produces the expected output.

1. **Update WinGet sources**. [What's this?](https://learn.microsoft.com/windows/package-manager/winget/source)

   **Procedure**. Type, or copy and paste, the following command into the terminal and press **Enter**.

   ```powershell
   winget source update
   ```

   **Expected Output**. You should see messages indicating that all sources were updated followed by **`Done`** for each source. Key indicator of success is that each source shows as **Done**.

   **Troubleshooting**. If the command does not display the expected output, follow [{{SME TODO}}](). Do **NOT** continue with the remaining setup tasks until this command produces the expected output.

## Install the SOE

1. **Open a terminal window**. [What's this?](https://learn.microsoft.com/windows/terminal/)
   **Procedure**.
   1. Open the Windows Power User Menu.
      - *Keyboard*. Press **Windows key (⊞)** + **X**.
      - *Mouse*. Right-click on **Start (⊞)** icon.
   1. Select **Terminal** or **PowerShell**, depending on your Windows version.

   **Expected Output**. A User Account Control ([UAC](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/)) prompt asking for permission to allow the terminal to make changes to your device. Click **Yes** to continue.

   **Troubleshooting**. If the UAC prompt does not appear or you are unable to open an admin terminal, ensure that you have administrative privileges on your account and try again.

1. **Prepare for SOE setup.** These commands update the Windows package source, install Git, and download the GC-STEM ATLAS repository containing the SOE setup tools and configuration files.

   Copy and paste the following command block into a terminal and press **Enter**.

```powershell
winget source update --name winget
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
Env: Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
git clone https://github.com/GC-STEM/atlas.git "$HOME/Repos/atlas"
# Cmd to run the SOE setup script
```

```powershell
winget source update --name winget
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id GitHub.cli -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Microsoft.PowerShell -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Python.PythonInstallManager -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Microsoft.VisualStudioCode -e --source winget --accept-source-agreements --accept-package-agreements
Env: Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
pymanager install 3.12 --quiet
git clone https://github.com/GC-STEM/atlas.git "$HOME/Repos/atlas"
(Get-Content "$HOME/Repos/atlas/.vscode/extensions.json" -Raw | ConvertFrom-Json).recommendations | ForEach-Object { code --install-extension $_ }
```

   **Expected output.** You should see messages confirming that the WinGet source was updated, Git was installed or updated (or was already current), and ATLAS was downloaded to `$HOME/Repos/atlas`.

   The final messages should look similar to:

   ```text
   Cloning into 'C:\Users\<your-username>\Repos\atlas'...
   remote: Enumerating objects: ...
   Receiving objects: 100% (...), done.
   Resolving deltas: 100% (...), done.
   ```

   Your output may vary. The key indicator of success is that the ATLAS repository was cloned without errors.

   **Troubleshooting.** If any command reports an error, follow the [CLI troubleshooting procedures](#understand-basic-cli-troubleshooting). Do **NOT** continue to the next setup task until the error is resolved.

1. **Close the terminal window** after the installation completes successfully.

1. **Open a new terminal window**. [What's this?](https://learn.microsoft.com/windows/terminal/)
   **Procedure**.
   1. Open the Windows Power User Menu.
      - *Keyboard*. Press **Windows key (⊞)** + **X**.
      - *Mouse*. Right-click on **Start (⊞)** icon.
   1. Select **Terminal** or **PowerShell**, depending on your Windows version.

   ```powershell
   py install 3.12 --quiet
   ```

1. **Restart the computer**. [How?](https://support.microsoft.com/windows/restart-reboot-your-pc-110262aa-fc79-1c33-7b00-c140ae3a6dac)

## Clone the Atlas repository

1. **Open a terminal window**. [What's this?](https://learn.microsoft.com/windows/terminal/)
   **Procedure**.
   1. Open the Windows Power User Menu.
      - *Keyboard*. Press **Windows key (⊞)** + **X**.
      - *Mouse*. Right-click on **Start (⊞)** icon.
   1. Select **Terminal** or **PowerShell**, depending on your Windows version.


## Configure the SOE

## Verify the SOE

## Help and Support

- [**Support for Students**](https://github.com/GC-STEM/crs000/wiki/Support-for-Students)
- [**Support for Faculty**](https://github.com/GC-STEM/crs000-faculty/wiki/Support-for-Faculty)
