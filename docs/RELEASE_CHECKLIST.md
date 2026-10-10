# Release checklist

## Completed locally

- [x] Source, dependency, build, and privacy audit
- [x] Unsupported direct-ASD prototype removed from production source
- [x] Windows API handle cleanup and 64-bit function signatures
- [x] Background first scan and guarded writes
- [x] Unit tests and source compilation
- [x] Standalone Windows x64 build
- [x] Responsive packaged-window launch check
- [x] SHA-256 checksum generation
- [x] README, contributing guide, changelog, security policy, and GitHub templates
- [x] Privacy scan of source and release executable

## Requires owner approval or external validation

- [x] Select and add the MIT License
- [x] Choose commit author name and GitHub noreply email
- [ ] Initialize Git and create the first commit
- [ ] Create the public `evenicle-2-save-editor` GitHub repository
- [ ] Push source and configure repository description/topics
- [ ] Test an actual scan/write/save cycle against supported game releases
- [ ] Publish the `v0.1.0` prerelease and attach the Windows build/checksum
- [ ] Confirm public repository and download accessibility

The project should remain a prerelease until an end-to-end test confirms a value can be scanned,
changed, saved in-game, and observed again after restarting the game.
