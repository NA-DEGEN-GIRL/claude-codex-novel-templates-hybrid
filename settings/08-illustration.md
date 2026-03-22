# Cover Image & Episode Illustrations

> Cover images apply to all novels. Episode illustrations apply only when `illustration: true`.

---

## 1. Cover Image

Save `cover.png` (or `.jpg`) in the novel root.

**Auto-generation**: Generate via NovelAI MCP server's `generate_image` tool.
- Auto-generate if `cover.png` doesn't exist at first episode writing
- If it already exists, do not touch (regenerate only on explicit user request)

**Prompt composition elements:**
- Protagonist appearance (from `settings/03-characters.md`)
- Novel genre and atmosphere (modern → urban/neon, SF → futuristic, 무협 → Eastern martial arts)
- Key symbolic objects (sword, magic, tech devices, etc.)
- Tone & mood (dark → dim lighting, bright → vivid colors)
- Cover-appropriate composition: upper body or full body, impactful pose
- Recommended resolution: 832x1216 (portrait)

After generation:
1. **Save the prompt used to `cover-prompt.txt`** (reference point for regeneration/modification).

**`cover-prompt.txt` format:**

```
[Prompt]
masterpiece, best quality, amazing quality,
1boy, solo, upper body, ...tags...

[Negative Prompt]
lowres, bad anatomy, ...

[Settings]
resolution: 832x1216
tool: generate_cover / generate_image
date: YYYY-MM-DD
```

- When regenerating a cover, modify based on the prompt in this file.
- If a cover exists without a prompt file, reverse-engineer the prompt and write `cover-prompt.txt`.

### character-prompts.md

Create `character-prompts.md` in the novel root to manage per-character image generation prompts.
The NovelAI MCP server (`novelai-image`) parses this file to auto-generate images.

> Even when `illustration: false`, `character-prompts.md` is maintained for cover generation (`generate_cover`).

**Immutable Traits**: Each character prompt block MUST include an `## Immutable Traits` section (keep the section header in Korean as `## 불변의 특징` for parser compatibility). These traits are **never omitted** from prompts during illustration/portrait generation.

```markdown
## 불변의 특징
- {{trait_1}} (e.g., "왼쪽 눈 아래 점", "오른손 검지 흉터", "은색 귀걸이")
- {{trait_2}}
```

> These traits persist across variants and are auto-added to `extra_tags` when calling `generate_illustration`/`generate_character`. They are core data for character visual consistency in future webtoon pipelines.

**Character portraits** (when `illustration: true`): Images generated via `generate_character` tool are saved to `assets/characters/`. Used as reference for the character's baseline appearance.

**Portrait management rules** (when `illustration: true`):
- Generate a base portrait via `generate_character` before the character's first appearance
- If appearance changes significantly (transformation, time skip, disguise, etc.), generate a variant portrait
- Variant filename: `{character_name}-{variant_name}.png` (e.g., `사쿠라-방송_모드.png`)

---

## 2. Episode Illustrations

> **This section applies only when `illustration: true`.** When `illustration: false` (default), skip episode illustration generation. If the user explicitly requests illustrations, follow these rules.

### Insertion Criteria

Insert illustrations only in the following situations, NOT every episode:

- Character first appearance or appearance change (disguise, injury, new outfit, etc.)
- Emotionally striking scene (post-duel, confession, farewell, etc.)
- New location/worldbuilding element appearing for the first time
- When you want to visually emphasize the overall tone of an episode

> Do not insert every episode. Illustrations are only effective when reserved for truly visually powerful scenes. Use your judgment on frequency, but do not overuse.

### Illustration Generation Method

**Always use the `generate_illustration` tool** (auto-ensures character consistency):

```
generate_illustration(
  novel_id="{{NOVEL_ID}}",
  scene_prompt="scene/background/atmosphere tags (do NOT include character appearance tags)",
  characters=[
    {"name": "CharacterA"},
    {"name": "CharacterB", "variant": "variant_name", "extra_tags": "scene-specific extra tags"}
  ],
  output_filename="chXXX-scene-name.png"
)
```

**How it works:**
1. Auto-loads character tags from `character-prompts.md` and passes them as V4 char_captions
2. Per-character coordinate assignment for accurate placement in multi-character compositions
3. Scene/background tags and character appearance tags are separated to prevent attribute confusion

> **Do NOT use `generate_image` for episode illustrations.**
> `generate_image` does not auto-load character tags, resulting in inconsistent character appearances.

### Illustration Format (Required — only this format is allowed)

Insert at the end of the episode body (before EPISODE_META) using **this blockquote format**:

```markdown
---

> **삽화**: {{character_name}} — {{scene description}}
> ![삽화]({{image_path}})
```

> **Required**: Must include `>` blockquote + `**삽화**:` description line.
> The reader parses this format to display illustration captions.
> Using `![description](path)` alone is **forbidden** — the caption will not display.

- Image path is under `{{NOVEL_ID}}/assets/illustrations/`.
- If no prompt exists for the character in `character-prompts.md`, add one first.
- Episodes containing illustrations are tracked in `summaries/illustration-log.md`.

### Illustration Tracking (Required)

Record in `summaries/illustration-log.md` every time an illustration is generated:
- Episode number, filename, characters present, scene_prompt, generation date
- Without this record, consistency during regeneration/audit is impossible

### Illustration Management

Manage illustrations systematically:
- **Single verification**: Immediately after insertion — check image-text match, tag consistency, format
- **Batch audit**: At arc completion — full review (appearance change reflection, orphan images, broken references)
- **Regeneration**: When issues found, modify and regenerate based on existing prompt records in `summaries/illustration-log.md`

---
