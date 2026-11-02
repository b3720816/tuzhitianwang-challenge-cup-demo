# Third-party dependencies

Application dependency declarations and lockfiles retain their package identities. Application licensing does not replace dependency licenses.

| Package | License |
|---|---|
| Vue, Vite, @vitejs/plugin-vue | MIT |
| ECharts, zrender | Apache-2.0 |
| FastAPI, Pydantic, Uvicorn | MIT / BSD-3-Clause (Uvicorn) |
| pytest, httpx | MIT / BSD-3-Clause (httpx) |

Runtime dependencies are installed from their respective distributions; their notices and licenses remain applicable. The checked-in ECharts build notice is preserved in the frontend output. No training framework, research model, third-party dataset, or cloud credential is distributed here.

Bundled frontend runtime license metadata: vue (MIT), echarts (Apache-2.0), zrender (BSD-3-Clause), tslib (0BSD). License texts available in `licenses/`.
