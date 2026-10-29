# API image publishing

`Dockerfile.public` and its Dockerfile-specific ignore file restrict the build context and image to the API application and Python requirements. The `data/` snapshot, ingestion scripts, notebook, environment files and repository metadata are excluded. This image does not seed a graph; the full local Compose workflow still uses `Dockerfile` and the separately obtained snapshot.

The GitHub Actions `Publish API image` workflow publishes `ghcr.io/lszefner/traice-api` with `latest` and commit-SHA tags when its input files change on `main`, or when started manually. It uses the repository workflow's `GITHUB_TOKEN` with `packages: write`; no personal access token is needed. The workflow must actually succeed before this image exists. Review the built image and package settings before wider distribution.

New packages are initially private. An account with package administrator access can separately change its visibility in the package's GitHub settings; GitHub states that making a package public cannot be reversed. Verify an anonymous pull after changing visibility. Do not treat the image as public until both the setting and anonymous pull have been verified. The repository can remain private.
