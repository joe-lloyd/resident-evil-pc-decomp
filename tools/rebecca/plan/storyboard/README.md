# Build the storyboard

From the repository root, restore the asset cache and generate the page:

```sh
node tools/rebecca/assets.ts pull
node tools/rebecca/plan/storyboard.ts /tmp/rebecca-storyboard
```

Use Node 24 or later. Image conversion uses macOS `sips` or ImageMagick `magick` on Linux. The output contains `index.html` and camera JPEGs at 640 pixels wide. The generator embeds the CSS and browser script in the page.

Run the source checks:

```sh
node --test tools/rebecca/plan/storyboard.test.ts
```

Serve the output over HTTP to test browser storage and clipboard access. Use HTTPS for clipboard access outside localhost. The page includes the research navigation script at `/research/rebecca-day/nav.js`. That script needs the research index on the same host.

# Publish the page

Copy the generated output through the existing research route:

```sh
rsync -az --rsync-path='sudo -n rsync' /tmp/rebecca-storyboard/ pi-server:/opt/homelab/cert-setup/dashboard/research/rebecca-storyboard/
```

The hand-written research index links the storyboard in its Start here section. The navigation script reads that card from the index.

# Read the counts

Room scripts and camera renders determine current build status. The page also keeps the older label from `day.ts`. The original mansion save room counts as built through its existing room script. Its review image can still be missing.

Item rows join the source tables to `item_aot_set` records in room scripts. The table includes the starting kit from `GameStart.cpp`, hand-written cabin pickups and the original save room's Sword Key. Repeated pickup records with the same item flag count once. Loaded weapons contribute their rounds. Missing placements do not contribute to balance totals.

The entry audit follows `scripts.ts`. A room's message zero counts when its script shows it and no entry cutscene replaces it. Files retain their full text and the labels from calendar, map and roster pages. The page also shows raw room messages for source edits.

The missing list combines repository evidence with unfinished rows from `todo.ts`. An under-way tracker row needs review, even when a door tour has passed. Chris's entrance is part of `cut-sleep`, so it does not count as an unwritten scene.

Balance findings are prompts for a route test. Enemy HP is absent from `foes.ts`. The page does not simulate damage, inventory spending or route choices. The linked playthrough uses an older room layout, so the storyboard does not assign room timestamps from it.

# Review edits

Goal edits, dialogue notes and item notes save automatically to this browser's localStorage. Copy my edits exports markdown grouped by room, including the field, old source value and new text or note. Clear edits asks before removing saved changes. If the source changes after an edit, the page flags the saved edit and includes both source versions in the export. No edits are sent to a server.
