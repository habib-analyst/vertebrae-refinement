# Third-party sources

The baseline is the pretrained vertebrae SwinUNETR checkpoint and inference code from [SuPreM](https://github.com/MrGiovanni/SuPreM), pinned to commit `7583213147e33daf2031cc0a3ad30faa516f4f64`. Credit belongs to its original authors. This project does not claim to have developed or trained that model.

SuPreM's [license](https://github.com/MrGiovanni/SuPreM/blob/7583213147e33daf2031cc0a3ad30faa516f4f64/LICENSE) is CC BY-NC-ND 4.0. The reproduction runner fetches the source and executes it without editing it. Upstream source and checkpoints are not vendored into this repository and are not covered by its MIT license.

The two demo CT cases come from the upstream `AbdomenAtlasDemo` resource. Related dataset documentation is maintained in [AbdomenAtlas](https://github.com/MrGiovanni/AbdomenAtlas). Dataset versions and original CT sources can have different terms; a license for one version is not assumed to cover this specific demo or all derived files.

Only original code and numerical experiment records are published here. CT volumes, checkpoint files, medical-image figures, and NIfTI prediction archives are excluded. Obtain the original resources from their providers and follow their applicable terms before redistributing them.

Python dependencies retain their own licenses.
