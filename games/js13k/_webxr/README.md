# Shared 3D libraries for the js13k WebXR games

js13k's WebXR category lets games load one of these libraries from the contest's server
(`/<year>/webxr/aframe.js`, `/<year>/webxr/three.js`). GN 2.0 hosts copies here instead, and
those games point to `../_webxr/<year>/...`.

| Year | A-Frame | three.js |
|---|---|---|
| 2017 | 0.6.1 | |
| 2018 | 0.8.2 | |
| 2019 | 1.0.4 | r107 |
| 2020 | 1.0.4 | r120 |
| 2021 | | r131 |
| 2022 | 1.3.0 | r143 |
| 2023 | | r155 |
| 2024 | 1.6.0 | r167 |
| 2025 | 1.7.1 | r179 |
| 2026 | | r180 |

For 2019, A-Frame 1.0.4 is used instead of the contest's 0.9.2: 0.9.2 crashes in current browsers, and the 2019 games run fine on 1.0.4.

Both are MIT licensed (see LICENSE-aframe.txt and LICENSE-three.js.txt).
