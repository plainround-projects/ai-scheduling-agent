# Prompt changelog

Each prompt lives in `prompts/<name>/<version>.md` with a `version:` line in its front matter. A prompt is never edited after it has been used for a recorded run; a change is a new version and a line here.

## agent

- **v1** (2026-10-27): first version. Reads before it writes, treats every write as a proposal a person approves, uses the earliest fitting slot, obeys remembered preferences, and says so when nothing can be done.
