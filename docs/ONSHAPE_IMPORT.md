# SI Console 3D import guide

Rev R3. Date 2026-11-23. Status: DRAFT REFERENCE, NOT FOR SUBMISSION.
This guide covers the shared 3D workspace only. The docs will live in the private GitHub repo si-console once Jayden creates it, not in Onshape. The repo does not exist yet.
Model files: ~/workspace/si-console-research-2/blueprints-R3/cad/.

## 1. Onshape, step by step

Onshape is the first choice for the shared 3D workspace. The free plan works for this project.

### Make a free account

1. Go to onshape.com.
2. Click Sign Up.
3. Pick the free plan. It is called Onshape Free.
4. Enter your name, email, and a password. Confirm your email.
5. Sign in. You now have a free account.

### Make a document

1. Click Create in the top left.
2. Pick Document.
3. Name it "SI Console".
4. Click Create. The document opens with one empty Part Studio tab.

### Import the STEP files

Import the full assembly first, then the parts.

1. Click the plus sign next to the tabs at the bottom. Pick Import.
2. Upload si_console_assembly.step. This is the full model, all parts in place, 61 solids.
3. Wait for the import to finish. Open the Assembly tab that Onshape makes from it.
4. Import the part STEP files one at a time, or in one batch. Use the same Import button each time.
5. Import these parts: pi5, case_front_panel, case_back_panel, case_top_panel, case_bottom, case_side_left, case_side_right, mini_screen, btn_green, btn_red, kill_switch, btn_ptt, toggle_lang, led_coord, led_agent1, led_agent2, led_guard, uln2003, perfboard, case_fan, soundbar, monitor.
6. Also import mini_screen_wedge.step. It is the printed support block under the mini screen.
7. All files are exported in case coordinates. X is 0 left to 360 right. Y is 0 front to 240 back. Z is 0 desk to 140 top. The parts land in place when imported together. Do not move them by hand.
8. If a part lands in the wrong place, check that the import used millimetres. Onshape imports STEP in millimetres by default. If the units are wrong, re-import and set the units to mm.

### Rebuild the assembly

1. The assembly STEP already has every part in place. Use it as the reference.
2. To make an assembly you can edit, make a new Assembly tab.
3. Insert each imported part into the assembly. Start with the case panels, then the Pi 5, then the mini screen, then the buttons, kill switch, LEDs, ULN2003, perfboard, case fan, and soundbar. Add the monitor last, behind the case.
4. Fix each part in place. The parts are already in case coordinates, so use the Fix mate, not a move.
5. Name the mates after the parts they hold. Example: "front panel fixed", "pi5 fixed".
6. Check the front view. Green button left, red button middle, kill switch right, PTT and toggle far right, LEDs top row left to right. If the view is mirrored, check the import orientation.

### Share with edit access

1. Click Share in the top right of the document.
2. Type the teammate email address.
3. Set the permission to "Can edit".
4. Click Share. Repeat for each teammate.
5. Do not set the document to public. Do not use the public link. Only named teammates get access.
6. Teammates open the shared link, sign in with their own free Onshape account, and edit the same document.
7. Hasan owns the real CAD in Fusion 360. Onshape is the shared view and the backup. Changes in Onshape must be copied back to Fusion 360 by Hasan. Do not treat Onshape as the source of truth.

## 2. Fusion 360, step by step

Hasan uses Fusion 360. The same STEP files work there.

### Import the STEP files

1. Open Fusion 360. Sign in with an Autodesk account. A free personal licence works for this project.
2. Make a new design. Save it as "SI Console" in your project folder.
3. Click File, then Open, then pick si_console_assembly.step. This opens the full model with all parts in place.
4. To get the parts as separate files, click File, then Open, then pick each part STEP file. Import these parts: pi5, case_front_panel, case_back_panel, case_top_panel, case_bottom, case_side_left, case_side_right, mini_screen, mini_screen_wedge, btn_green, btn_red, kill_switch, btn_ptt, toggle_lang, led_coord, led_agent1, led_agent2, led_guard, uln2003, perfboard, case_fan, soundbar, monitor.
5. All files use millimetres and case coordinates. The parts land in place. Do not move them by hand.

### Rebuild the assembly

1. The assembly STEP already has every part in place. Use it as the reference.
2. To make an assembly you can edit, make a new design and insert each part as a component. Start with the case panels, then the Pi 5, then the mini screen, then the buttons, kill switch, LEDs, ULN2003, perfboard, case fan, and soundbar. Add the monitor last, behind the case.
3. Ground each component. The parts are already in case coordinates, so grounding keeps them in place.
4. Check the front view. Green button left, red button middle, kill switch right, PTT and toggle far right, LEDs top row left to right.

### Share with edit access

1. Save the design to your Autodesk project folder.
2. In the Data Panel, right click the project folder. Pick Share.
3. Add each teammate by email. Set the permission to edit.
4. Or share the single design: right click the design file, pick Share, add teammates by email with edit access.
5. Do not make the project public. Only named teammates get access.
6. Teammates open the shared link with their own Autodesk account and edit the same design.
7. Fusion 360 is the source of truth for the real CAD. Hasan owns it. The Onshape document is the shared view and the backup.

## 3. What is ASSUMED, and what Hasan must check in CAD

This model is reference only. It is not Fallen submission material. Check every ASSUMED number against the real part before cutting or printing.

- Back panel cable cutouts moved in R3. R2 put them at Y 20 from the top of the panel, Z about 112 to 117. That is wrong for a bottom-mounted Pi. The Pi ports sit at Z about 12 to 16. R3 moves the cutouts to port height, Z centred 14. One shared slot for both micro-HDMI ports, X 61 to 90, because the two ports are only 13 mm apart at the centres and two separate 15 mm slots would overlap. USB-C slot X 46 to 56. The 2D R3 drawings match this. Confirm the exact X in CAD from the Pi mount position.
- Kill switch body is 78.3 mm deep. That is 3.3 mm more than the 75 mm clear zone behind the front panel in R2. Nothing sits in that 3.3 mm in this model. Check the layout in CAD before cutting the case.
- Mini screen wedge is a flat support block, 121 x 89.48 x 8 mm, ASSUMED. The BOM says 15 degrees. A 15 degree tilt does not fit the R2 flush cutout. Confirm the tilt in CAD. The wedge shape must change if the tilt stays.
- Finger joints are not modelled. The panels are plain rectangles. See the 2D R3 drawings for the joint layout. Draw the joints in Fusion 360.
- Case outer size 360 x 240 x 140 mm is ASSUMED, from R2. It is not a CAD result. Confirm before cutting.
- Front panel hole centres are ASSUMED. Measure the real buttons with calipers and test in cardboard first.
- LED colour map is ASSUMED: green COORD, red AGENT 1, blue AGENT 2, yellow GUARD. Confirm the colours with the team before wiring.
- Soundbar size is ASSUMED, 100 x 45 x 45 mm. No datasheet was found. The soundbar is a proposed budget cut. The monitor speakers over HDMI audio replace it. See the Overview doc for the totals with and without the cut.
- Monitor tilt is 10 degrees, ASSUMED. Kickstand shape is ASSUMED.
- Case fan position on the rear wall, centre X 320 Z 115, is ASSUMED.
- Perfboard size and position, 80 x 60 mm, centre of the case, is ASSUMED.
- Cooler footprint 47 x 44 mm is ASSUMED. GPIO header position is ASSUMED. Standoff heights are ASSUMED.

## 4. Where the docs live

This workspace is for the 3D design only. The docs do not live in Onshape.

- SI_Console_Overview.md and SI_Console_Detailed.md will live in the private GitHub repo si-console once Jayden creates it.
- The 2D drawings live in blueprints/ in the repo, and in blueprints-R3/ in the local workspace.
- The 3D files live in cad/ in the repo, and in blueprints-R3/cad/ in the local workspace.
- Edit the docs in the GitHub repo. Edit the 3D model in Onshape or Fusion 360. Do not paste the docs into Onshape.
