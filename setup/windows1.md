# SOE Setup on Windows

---
> [!WARNING]
> This page is under active development. It is not ready for student or faculty use.Please check back later.
---

Welcome to *SOE Setup on Windows*! This document provides instructions for setting up the STEM Standard Operating Environment (SOE) on Windows using [**Windows Terminal**](https://learn.microsoft.com/windows/terminal/) and [**PowerShell**](https://learn.microsoft.com/powershell/scripting/overview), a command-line shell.

## Table of Contents <!-- omit from toc -->

Follow these steps in numeric order to set up the SOE on Windows:

1. [Read me first](#read-me-first)
2. [Prepare your computer](#prepare-your-computer)
3. [Install the SOE](#install-the-soe)
4. [Configure the SOE](#configure-the-soe)
5. [Verify the SOE](#verify-the-soe)
6. [TBD](#tbd)

## Read me first

A **command-line interface (CLI)** lets you control a program by typing commands, which are written instructions. **Output** is the text a program displays in response. You will use commands to install the tools for your STEM coursework.

- Work through the sections in order. Keep your computer connected to the internet.
- Copy only the text inside each command block regardless of whether it's just one line or multiple lines of commands. Paste it into PowerShell with **Ctrl+V**, then press **Enter** to run it. If a block has several commands, run one line at a time.
- Wait for the **prompt**, the text that shows PowerShell is ready for another command, to return before continuing. An installation may take several minutes.
- The WinGet installation commands accept the software and source license agreements through their `--accept-package-agreements` and `--accept-source-agreements` options. If an installer opens, follow its instructions. Windows may ask permission to make changes to your device. [Learn more](https://learn.microsoft.com/windows/package-manager/winget/install).
- Messages and version numbers may differ from the examples. A message saying a tool is already installed and has no available update means you can continue.

**Troubleshooting**. If a command does not produce the expected result, copy the command and all of its output into the AI chat tool recommended by your instructor. Ask it to explain the error and suggest a fix. If you do not have access to that tool, contact your instructor with the same information. Resolve the problem before continuing with the remaining setup tasks.

## Prepare your computer

### Switch Out of S Mode

**Switch out of S mode**, if enabled. [How to check?](https://github.com/GC-STEM/atlas/wiki/Troubleshoot-Win#verification-check-for-s-mode) [How to switch?](https://support.microsoft.com/windows/experience/platform-variants/switching-out-of-s-mode-in-windows)

### Create a Restore Point

**Create a restore point** and label it, `Before SOE install`. [How?](https://support.microsoft.com/windows/experience/backup-recovery/system-protection) This step is optional but recommended in case you need to revert your system to its previous state.

## Install the SOE

### Open a Terminal

**Windows Terminal** is an application that provides a window for command-line tools. **PowerShell** is the shell, or program, that reads and runs the commands you enter. Together, they let you install software and manage files for STEM projects using the command line. [Learn more](https://learn.microsoft.com/windows/terminal/).

**Procedure**.

1. Open the Windows Power User Menu.
   - *Keyboard*. Press **Windows key (⊞)** + **X**.
   - *Mouse*. Right-click on the **Start (⊞)** icon.
2. Select **Terminal** or **PowerShell**, depending on which is available.
3. Check the command prompt (the line where you enter commands).
   - *Starts with `PS`?* You are ready.
   - *Does not start with `PS`?* Type `powershell.exe` and press **Enter**. The prompt should now start with `PS`.

**Expected Output**. You should see a PowerShell prompt similar to `PS C:\Users\YourName>`, with a cursor where you can type commands. Your folder path may differ. You can type commands or paste them from these instructions.

### Check for WinGet

**Windows Package Manager**, also called **WinGet**, downloads and installs applications through the `winget` command. It is included with most modern versions of Windows, but you may need to install it if it is not already available on your system. [Learn more](https://learn.microsoft.com/windows/package-manager/).

**Procedure**. Type the following command exactly as it appears below and press **Enter**.

<!-- ci:command-test id=verify-winget fixture=empty-repos expect=repo -->
```powershell
winget -v
```

**Expected Output**. A version number in the format `vX.Y.Z`, such as `v1.29.380`. Your version number will be different, which is expected and does not indicate an error. The key indicator of success is that WinGet displays a version number. If it does, skip to [**Update Winget Sources**](#update-winget-sources).

If you receive an error indicating that `winget` is not recognized, you need to install it with the Microsoft Store link provided below.

**Procedure**. Copy the following command and paste it into the terminal and press **Enter**.

<!-- ci:command-test id=install-winget fixture=empty-repos expect=repo -->
```powershell
Start-Process "ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1"
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe
}
winget --version

```

If you just installed WinGet, close and reopen the terminal for the changes to take effect. Then verify the installation by running `winget -v` again.

## Configure the SOE

### Configure GitHub CLI

**Procedure**. Copy the command block into the terminal and press **Enter**. Follow the on-screen instructions to complete the authentication process.

<!-- ci:command-test id=gh-auth-login fixture=empty-repos expect=repo -->
```powershell
gh auth login --clipboard --hostname github.com --git-protocol https --web

```

### Configure Git

**Procedure**. Copy the command block into the terminal and press **Enter**.

<!-- ci:command-test id=git-config fixture=empty-repos expect=repo -->
```powershell
$user = gh api user | ConvertFrom-Json
git config --global user.name $(if ($user.name) { $user.name } else { $user.login })
git config --global user.email "$($user.id)+$($user.login)@users.noreply.github.com"
gh auth setup-git
git config --global --get-regexp '^user\.(name|email)$'

```

### Configure VS Code

## Verify the SOE

## TBD

### Advanced setup

The command block contains the same commands as the individual installation steps above, but runs them all at once.

<!-- ci:command-test id=install-soe-all-at-once fixture=empty-repos expect=repo -->
```powershell
winget source update
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id GitHub.cli -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Microsoft.PowerShell -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Python.PythonInstallManager -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Microsoft.VisualStudioCode -e --source winget --accept-source-agreements --accept-package-agreements
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
pymanager install 3.12 --quiet
git clone https://github.com/GC-STEM/atlas.git "$HOME/Repos/atlas"
(Get-Content "$HOME/Repos/atlas/.vscode/extensions.json" -Raw | ConvertFrom-Json).recommendations | ForEach-Object { code --install-extension $_ }
```
