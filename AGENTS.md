# Repository instructions for AI contributors

## Version isolation

- Never begin a new creative direction directly on `main`.
- Start from the version requested by the user and create `variant/<short-name>`.
- Keep alternative lore, UI, and Blender pipelines in separate branches unless the user explicitly asks for an integration.
- Do not resolve a conflict by concatenating both sides or by committing `<<<<<<<`, `=======`, or `>>>>>>>` markers.
- Preserve existing assets that belong to other version branches.

## Required checks before committing

```bash
rg -n '^(<<<<<<<|=======|>>>>>>>)' --hidden -g '!vendor/**' .
node --check js/app.js
node --check js/data.js
node --check js/world.js
```

Also verify that every local `src`, `href`, model, and image path used by the edited page exists in the same branch.

## Documentation

- Update `README.md` when the default entry point changes.
- Update `VERSIONING.md` when a new long-lived version branch is created.
