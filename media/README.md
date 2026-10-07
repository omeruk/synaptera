# media/

Previews and stills for the README gallery. All files are cut from the existing videos or converted from them; nothing was simulated or re-rendered for them (`scripts/make_media.py`; the cut times are computed from the HDF5 run records, not guessed). The source videos are not part of the public copy (no video file is).

Source videos (1920×1080, 30 fps, playback ×0.25, 6 s title card at the start):

| label | file | run |
|---|---|---|
| n1 video | `flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_en_vis.mp4` | n1, seed 3: hand-made route + brain feeding decision |
| n2 video | `flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_en_vis.mp4` | n2, seed 3: brain only, hand-made flight programme |
| compare video | `flight_n1_vs_n2_v2_compare_en_vis.mp4` | n1 and n2 side by side |

In the n1 and compare videos the playback is ×0.25 until 1 s after the feeding decision starts (run time 4.025 s) and ×1 afterwards; the n2 video is ×0.25 throughout. Run time = time of the closed-loop simulation; video time = position in the mp4.

## GIF previews (900 px wide, 256-colour palette from `palettegen`/`paletteuse`, a caption bar below the picture states the playback speed)

Layout of `preview_n1.gif` and `preview_n2.gif` (900 × 434 px): two regions of the 1920 × 1080 video frame, stacked. Top: the brain panels (frontal and dorsal, with their header and class legend; x 0–1370, y 0–380 of the frame), scaled to 900 px wide. Bottom: the follow camera and the arena view (full width, y 600–930 of the frame), scaled to 900 px wide. Left out: the neuropil bars, the circuit boxes and the graph strip. The video's own "playback ×0.25" label (inside the camera region) is removed with `delogo`; the first letters of a neuropil label that reach into the brain crop are painted black. `preview_compare.gif` (900 × 536 px) keeps the whole frame of the comparison video, because that video has its own layout (the brain only as a thumbnail); its on-screen "×0.25" is correct for the GIF.

| file | source | run time | video time | playback speed | frame rate | length | size |
|---|---|---|---|---|---|---|---|
| `preview_n1.gif` | n1 video | 0.000–4.025 s (take-off, cruise past the towers, approach, descent, touchdown, start of feeding) | 6.0–22.1 s | ×0.375 real time (video ×0.25, shown 1.5× faster) | 12 fps | 10.8 s | 8.2 MB |
| `preview_n2.gif` | n2 video | 0.35–2.15 s (cruise, first tower contact at 0.925 s) | 7.4–14.6 s | ×0.25 | 15 fps | 7.3 s | 5.3 MB |
| `preview_compare.gif` | compare video | 0.35–2.55 s (n1 passes the towers, n2 is at the first tower) | 7.4–16.2 s | ×0.25 | 12 fps | 8.8 s | 6.9 MB |

Size limits: 9.5 MB (n1), 6 MB (n2), 8 MB (compare). At 900 px and 15 fps the n1 GIF was 9.9 MB and the compare GIF 8.5 MB, so both were rendered at 12 fps (8.2 and 6.9 MB); the width stayed 900 px. The caption bar of each GIF gives its playback speed.

## Stills (`stills/*.png`, 1280 px wide; `stills/stills.csv` lists video, frame and times)

| file | video | run time (s) | moment |
|---|---|---|---|
| `takeoff.png` | n1 | 0.167 | take-off (phase `takeoff`, step 6) |
| `cruise_between_towers.png` | n1 | 1.192 | first cruise step with x ≥ 240 mm (towers at x 160–200 and 280–320 mm) |
| `approach.png` | n1 | 1.692 | approach (6 steps after the phase starts) |
| `touchdown.png` | n1 | 3.017 | touchdown step (first feeding step; first platform contact one step earlier) |
| `feeding_mn9_circuit.png` | n1 | 3.142 | feeding, first step with MN9 > 50 Hz; sugar GRN → SEZ → MN9 strip visible |
| `brain_panel_feeding.png` | n1 | 3.142 | crop of the frontal and dorsal brain panels of the same frame |
| `n2_first_tower_contact.png` | n2 | 0.917 | first step with tower contact (step 36) |
| `compare_view.png` | compare | 3.217 | 8 steps after the n1 touchdown; n2 is still at the tower |

## What the pictures show

- Brain panels: every dot is a neuron placed at the centroid of its arbor; colour classes, dot size, glow and the dim background cloud are display settings, not measurements. Which neurons glow comes from the simulated spikes.
- The route, altitude, approach, landing, head reflex and postures are hand-made; the visual input is the FlyVis network; the only behaviour decided by the brain model is feeding (MN9 > 10 Hz). The orange proboscis marker is a visual marker (the body model has no proboscis joint).

## Licence and attribution

CC BY-NC 4.0. The pictures contain results derived from the FlyWire v783 connectome (Dorkenwald et al. 2024; Schlegel et al. 2024; CC BY-NC 4.0) and renderings of the NeuroMechFly / FlyGym body model (Apache-2.0; Wang-Chen et al. 2024) with FlyVis (Lappalainen et al. 2024) as the source of the visual input. Details: [NOTICE.md](../NOTICE.md), [THIRD_PARTY.md](../THIRD_PARTY.md). Author: omeruk.
