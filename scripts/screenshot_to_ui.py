"""
Screenshot → Android UI Spec — turns a UI screenshot/mockup into an
implementation-ready Markdown spec that @ui-builder / @coder convert into
XML layouts + ViewBinding.

This does NOT write Kotlin/XML itself. It extracts a precise, structured
description of the screen (component tree, IDs, colors, text, spacing) so the
coder agent can generate native Android UI that conforms to AGENTS.md
(Material 3, XML + ViewBinding, no Jetpack Compose).

Usage:
    python scripts/screenshot_to_ui.py --file docs/input/login.png
    python scripts/screenshot_to_ui.py --file login.png --screen login
    python scripts/screenshot_to_ui.py            # process every image in docs/input/

Output:
    docs/parsed/<name>.ui.md   (the structured UI spec)

Requirements (shared with doc_watcher):
    pip install requests Pillow
The LiteLLM proxy must be running (docker compose up -d) because extraction
uses the vision model.
"""

from __future__ import annotations

import sys
import time
import argparse
from pathlib import Path

# Reuse the hardened vision plumbing from doc_watcher (same scripts/ dir):
# retries, timeout, max_tokens, and auto-continuation on truncation.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_watcher import (  # noqa: E402
    encode_image,
    call_vision_model,
    VisionError,
    IMAGE_EXTENSIONS,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "docs" / "input"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "parsed"


# The prompt is engineered to produce a spec the coder can implement directly,
# under the project's hard constraints (Material 3, ConstraintLayout, ViewBinding,
# resource naming <type>_<screen>_<element>, no Compose).
UI_EXTRACTION_PROMPT = """You are a senior Android UI engineer. You are given a screenshot of a mobile app screen.
Produce a precise, implementation-ready UI SPEC in Markdown that another engineer will turn
into a NATIVE Android XML layout using Material 3 components and ViewBinding (NEVER Jetpack Compose).

Be exhaustive and concrete. Do not invent content that is not visible. If something is ambiguous,
state your best estimate and mark it "(approx)".

Output EXACTLY these sections in this order:

## Screen Summary
- One or two sentences: what this screen is and its primary purpose.
- Suggested screen name in snake_case (used for the layout file name and resource IDs).

## Root Layout
- Recommended root container (prefer `androidx.constraintlayout.widget.ConstraintLayout`;
  use `CoordinatorLayout` if there is an app bar/FAB/collapsing behavior; note `ScrollView`/
  `NestedScrollView` if content scrolls).
- Background color (hex) and overall padding (dp).
- Whether a Material `Toolbar`/`MaterialToolbar`, `BottomNavigationView`, `TabLayout`, or
  `FloatingActionButton` is present.

## Component Tree (top to bottom, left to right)
For EVERY visible element output a numbered row with:
- **Type** — the concrete Android/Material 3 widget class
  (e.g. `MaterialTextView`, `TextInputLayout` + `TextInputEditText`, `MaterialButton`,
  `ShapeableImageView`, `RecyclerView`, `MaterialCardView`, `Chip`, `SwitchMaterial`,
  `BottomNavigationView`, `FloatingActionButton`).
- **id** — resource id following `<type>_<screen>_<element>` (e.g. `tv_login_title`,
  `et_login_email`, `btn_login_submit`). Use the screen name from Screen Summary.
- **Text / content** — exact visible text, hint text, or icon description.
- **Style** — text size (sp, approx), weight, text color (hex), background/tint (hex),
  corner radius (dp) if rounded.
- **Size & position** — width/height behavior (match_parent/wrap_content/fixed dp),
  and placement relative to siblings/parent (approx).
- **Spacing** — margins/padding in dp (approx).
- **Accessibility** — for images/icons: a `contentDescription` naming the purpose
  (or mark decorative). Flag any touch target that looks smaller than 48dp.

## Lists / Repeated Content
- If a `RecyclerView` is present, describe the row item layout as its own mini component
  tree, suggest the item layout file name, the LayoutManager, and any dividers.

## Color Palette
- Table of the distinct colors used with hex values and a suggested `colors.xml` name
  (e.g. `color_login_primary`).

## Strings
- Table of every user-visible string with a suggested `strings.xml` key
  (e.g. `login_title`, `login_email_hint`).

## Implementation Notes
- Any state/interaction implied (buttons, inputs, toggles, navigation).
- Dimensions worth extracting into `dimens.xml`.
- Anything uncertain the engineer should confirm.

Rules:
- Map everything to Material 3 (`com.google.android.material`) widgets.
- Never suggest Jetpack Compose, `findViewById`, or deprecated APIs.
- Keep ids lowercase snake_case with the `<type>_<screen>_<element>` convention.
- Be complete — do not stop early; this spec is the single source of truth for the build.
"""


def slugify(name: str) -> str:
    """snake_case a screen name for file names / ids."""
    out = []
    for ch in name.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "."):
            out.append("_")
    slug = "".join(out).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "screen"


def extract_ui_spec(image_path: Path, screen_name: str | None = None) -> str:
    """Run the vision model and return a full Markdown UI spec (raises VisionError on failure)."""
    image_data, mime_type, width, height = encode_image(image_path)

    prompt = UI_EXTRACTION_PROMPT
    if screen_name:
        prompt += f'\n\nUse "{slugify(screen_name)}" as the screen name for the layout file and all resource ids.'

    content = call_vision_model(prompt, image_data, mime_type)

    header = (
        f"<!--\n"
        f"  Android UI Spec generated from screenshot\n"
        f"  Source: {image_path.name} ({width}x{height}px)\n"
        f"  Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"  Consumed by: @ui-builder / @coder to generate XML + ViewBinding\n"
        f"-->\n\n"
        f"# UI Spec: {image_path.name}\n\n"
        f"> Source screenshot: `{image_path.name}` ({width}x{height}px)\n"
        f"> Target: Native Android — Material 3 + XML + ViewBinding (NO Compose)\n\n---\n\n"
    )
    return header + content


def process_one(image_path: Path, screen_name: str | None = None) -> bool:
    if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
        print(f"  ⏭️  Skipped (not an image): {image_path.name}")
        return False

    stem = slugify(screen_name) if screen_name else image_path.stem
    output_path = OUTPUT_DIR / f"{stem}.ui.md"
    print(f"  🖼️  Analyzing: {image_path.name} → {output_path.name}")

    try:
        spec = extract_ui_spec(image_path, screen_name)
    except VisionError as e:
        print(f"  ❌ Vision extraction failed: {e}")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"  ❌ Error analyzing {image_path.name}: {e}")
        return False

    output_path.write_text(spec, encoding="utf-8")
    print(f"  ✅ Saved UI spec: {output_path.name} ({output_path.stat().st_size / 1024:.1f} KB)")
    return True


def process_all_inputs() -> None:
    images = [
        f for f in INPUT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ] if INPUT_DIR.exists() else []

    if not images:
        print(f"📂 No image files found in {INPUT_DIR}")
        print(f"   Drop a screenshot (PNG/JPG/WEBP) there, or pass --file <path>.")
        return

    print(f"📂 Found {len(images)} screenshot(s):\n")
    ok = sum(1 for img in sorted(images) if process_one(img))
    print(f"\n✅ Done: {ok}/{len(images)} UI specs generated")
    print(f"📁 Output: {OUTPUT_DIR}")
    print('   Next: "@ui-builder build the screen from docs/parsed/<name>.ui.md"')


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a UI screenshot into an Android UI spec")
    parser.add_argument("--file", type=str, help="Path to a single screenshot image")
    parser.add_argument("--screen", type=str, help="Screen name (snake_case) for file/ids, e.g. 'login'")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.file:
        image_path = Path(args.file)
        if not image_path.is_absolute():
            # Allow paths relative to project root or cwd.
            candidate = PROJECT_ROOT / args.file
            image_path = candidate if candidate.exists() else image_path
        if not image_path.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        success = process_one(image_path, args.screen)
        sys.exit(0 if success else 1)
    else:
        process_all_inputs()


if __name__ == "__main__":
    main()
