# GitHub Copilot instructions for GC-STEM HoAI

## Purpose and audience

This repository supports HoAI '26 (eight sessions over four days) and a planned
AI-assisted coding course for people with no programming experience. Use plain
language, define new terms, and favor small projects with observable results.

## Actual repository structure

- `README.md`: event entry point and the existing schedule numbered 0 through 7.
- `Sessions/1/GitHub-Copilot-Warmup.md`: event wrapper for the Agent warmup.
- `Sessions/5/GitHub-Copilot-Agent.md`: event wrapper for the selected Tempora Agent lesson.
- `Adventures/`: reusable HoAI lessons: `echo-chamber/README.md` and `tempora/README.md`.
- `docs/SETUP.md`: participant setup using Codespaces or local VS Code and Node.js.
- `docs/COURSE-ROADMAP.md`: future course plans and unresolved decisions.
- `.github/ci/`: maintainer validation and link-checking tools.
- `projects/`: ignored participant practice apps; create learner work here.

The repo does not contain Microsoft's full adventure library, shared data,
artwork, or language-specific solution runners. Use existing paths and link to
upstream material when it has not been adapted locally.

## Helping a participant

For the warmup and Tempora, use JavaScript and Node.js without installing
packages. Keep the app small, explain how to run it from the workspace root, and use the
lesson's examples to check the behavior. Ask for clarification when a rule is
ambiguous. Explain edits and proposed tool actions in language a beginner can
understand. Do not claim success until the relevant commands have run and the
results agree with the examples. Account settings control approval prompts;
do not promise that a particular prompt or tool limit always applies.

When a participant asks to build an app, place it under `projects/` and leave
the shared workshop materials and configuration alone unless asked to edit them.

## Maintaining curriculum

Keep session timing separate from reusable lessons. Do not invent event details,
session owners, or account entitlements. Session 5 is The Clockwork Town of
Tempora in Agent Mode. Its first version compares HH:MM readings on one day
using clock minutes minus tower minutes, without wrapping at midnight.
Preserve the existing schedule unless a maintainer asks to change it. Mark
planned content as planned, and update the catalog when a lesson is added.

Each lesson needs a goal, prerequisites, clear rules, starter prompt, run
instructions, known expected results, reflection, optional extensions, and
source attribution. Avoid unexplained frameworks, unnecessary dependencies,
and promises of production-ready output. Follow `CONTRIBUTING.md` and run the
checks documented in `.github/ci/README.md` for repository changes.

Microsoft CopilotAdventures is the main source for adapted activities.
Retain its copyright and MIT notice in `THIRD_PARTY_NOTICES.md` and link to the
specific upstream lesson. Check current product documentation before copying
setup instructions or custom-agent formats.
