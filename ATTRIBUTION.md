# Attribution and licensing policy

This independent project gratefully builds on Adafruit's published hardware,
learning guides, and CircuitPython ecosystem. Attribution does not imply
Adafruit's endorsement, manufacture, or qualification of our derivative.

**Current inventory:** original project documentation plus the
[Adafruit 5768 reference package](hardware/reference/adafruit-5768/README.md).
That package contains pinned upstream EAGLE sources, their original README and
license, a KiCad conversion with imported symbols/footprints, and derived review
exports. The entire hardware reference package is covered by its
[CC BY-SA 3.0 license](hardware/reference/adafruit-5768/LICENSE.txt), not the root
MIT license. Upstream markings embedded in the reference are retained as source
provenance, not as branding for a new handbell product.

No third-party firmware or sound recordings are vendored. The original project
[MIT license](LICENSE) is unchanged.

## License boundaries

| Material | Policy |
|---|---|
| Original project software and documentation | Existing MIT license, except explicitly marked material |
| Imported/adapted hardware | Preserve applicable upstream notices and license; plan to retain CC BY-SA 3.0 for adaptations of the verified 3.0 sources |
| Third-party software and libraries | Retain actual per-file/dependency licenses and copyright notices; do not infer them from hardware licensing |
| Bell recordings, images, models, and guide text | Establish rights separately; link rather than copy until verified |
| Original future mechanical designs | Record an explicit license before release; do not assume an electronics license covers every CAD asset |
| Names and logos | No implication of endorsement; no automatic trademark rights from an open hardware license |

The root MIT license does not override ShareAlike obligations. Put the complete
applicable license text and required notices alongside imported/adapted
hardware when it is first added. Do not label the whole repository "MIT" in a
way that hides those exceptions. This policy is project provenance practice,
not legal advice.

## Hardware license evidence

Each row refers to the exact source commit in the
[reference catalog](docs/reference-designs.md). For the verified sources,
the conclusion comes from README attribution language **and the actual
`license.txt`**, not a GitHub license badge.

| Adafruit product/source | Evidence at inspected revision |
|---|---|
| 5768 Prop-Maker Feather | [README](https://github.com/adafruit/Adafruit-RP2040-Prop-Maker-Feather-PCB/blob/408fa9a40c0a01a3a65497ef42a29e0b08fe711e/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-RP2040-Prop-Maker-Feather-PCB/blob/408fa9a40c0a01a3a65497ef42a29e0b08fe711e/license.txt) |
| 3988 Prop-Maker FeatherWing | [README](https://github.com/adafruit/Adafruit-Prop-Maker-FeatherWing-PCB/blob/f0e322ee15e06fe7810d9ec08f992a1b2fbe9bc2/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-Prop-Maker-FeatherWing-PCB/blob/f0e322ee15e06fe7810d9ec08f992a1b2fbe9bc2/license.txt) |
| 3006 MAX98357 breakout | [README](https://github.com/adafruit/Adafruit-MAX98357-I2S-Amp-Breakout/blob/c7cf21b4a83affb8bd0ee4fb8251d5b266d964ff/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-MAX98357-I2S-Amp-Breakout/blob/c7cf21b4a83affb8bd0ee4fb8251d5b266d964ff/license.txt) |
| 5770 I2S BFF | [README](https://github.com/adafruit/Adafruit-I2S-Amplifier-BFF-PCB/blob/fe191f0585be438605feca267afa38fe587e57f4/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-I2S-Amplifier-BFF-PCB/blob/fe191f0585be438605feca267afa38fe587e57f4/license.txt) |
| 5302 KB2040 | [README](https://github.com/adafruit/Adafruit-KB2040-PCB/blob/b4160dcf4385ef2cc30e9652489328321720ee4b/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-KB2040-PCB/blob/b4160dcf4385ef2cc30e9652489328321720ee4b/license.txt) |
| 4900 QT Py RP2040 | [README](https://github.com/adafruit/Adafruit-QT-Py-RP2040-PCB/blob/5b6ebd1661fd5250b4f60bdba14d5c475259b7f4/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-QT-Py-RP2040-PCB/blob/5b6ebd1661fd5250b4f60bdba14d5c475259b7f4/license.txt) |
| 5397 Charger BFF | [README](https://github.com/adafruit/Adafruit-Charger-BFF-PCB/blob/2acd339ac57539b236e1b072488f581ea56e3a4c/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-Charger-BFF-PCB/blob/2acd339ac57539b236e1b072488f581ea56e3a4c/license.txt) |
| 5426 QT Py ESP32-S3 | [README](https://github.com/adafruit/Adafruit-QT-Py-ESP32-S3-PCB/blob/333b35f9c77338d69816e542e7c6aa4db271d432/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-QT-Py-ESP32-S3-PCB/blob/333b35f9c77338d69816e542e7c6aa4db271d432/license.txt) |
| 5405 QT Py ESP32-C3 | [README](https://github.com/adafruit/Adafruit-QT-Py-ESP32-C3-PCB/blob/8618fb52d806fb184ec5807490db0a9b084ffa9c/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-QT-Py-ESP32-C3-PCB/blob/8618fb52d806fb184ec5807490db0a9b084ffa9c/license.txt) |
| 4410 Micro-Lipo | [README](https://github.com/adafruit/Adafruit-MicroLipo-PCB/blob/d8ab4b0f00c69a9f337a8d697bd15e0b9bae2e25/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-MicroLipo-PCB/blob/d8ab4b0f00c69a9f337a8d697bd15e0b9bae2e25/license.txt) |
| 2809 LIS3DH | [README](https://github.com/adafruit/Adafruit-LIS3DH-Breakout-PCB/blob/f5f3e1b33fec19a56b2c14c69bb1b97c1c4f2861/README.md), [CC BY-SA 3.0](https://github.com/adafruit/Adafruit-LIS3DH-Breakout-PCB/blob/f5f3e1b33fec19a56b2c14c69bb1b97c1c4f2861/license.txt) |
| 4884 Feather RP2040 | [README](https://github.com/adafruit/Adafruit-Feather-RP2040-PCB/blob/ea88166891ee0a1697a3899a5d55ab3722a2f125/README.md) says Creative Commons Attribution/Share-Alike but omits a version and references an absent `license.txt`. **Version unresolved: do not silently assign 3.0 or import until resolved.** |

Preserve the upstream attribution to Limor Fried/Ladyada and Adafruit Industries
and any additional named contributors as actually stated in the source.
The relevant READMEs request that their attribution text accompany
redistribution; retain it verbatim in notices at import time.

## Software evidence

- [CircuitPython LICENSE](https://github.com/adafruit/circuitpython/blob/d897c15f24b2a6de6529f138aed4705327020dab/LICENSE):
  MIT default with per-file/license exceptions. Audit included dependencies.
- [Adafruit CircuitPython LIS3DH LICENSE](https://github.com/adafruit/Adafruit_CircuitPython_LIS3DH/blob/cd40b482a098a62ecce1b4c62a1f1930be984e16/LICENSE):
  MIT; retain source headers and notices if incorporated.
- [Learning System Guides LICENSE](https://github.com/adafruit/Adafruit_Learning_System_Guides/blob/e45576f18a6d6fc345c89be725dbb22bf6d647ea/LICENSE):
  MIT for covered code; inspect individual files. This is not a blanket finding
  about WAV files, guide prose, photos, or every dependency.
- [TinyUF2 LICENSE](https://github.com/adafruit/tinyuf2/blob/6ca7559832df25513351f8fa2f43a8605c723dd5/LICENSE):
  MIT for covered code; relevant to a future S3 provisioning path, not required
  to replace RP2040's ROM bootloader.

## Required provenance record for each imported or adapted item

Record the source URL, project/product ID, upstream author/copyright statement,
commit/release, source filenames and hashes, applicable license and full notice
location, our destination files, exact reuse type, modifications, and reviewer.
Distinguish **reference only**, **unmodified copy**, **adaptation**, and
**independent implementation informed by documentation**.

For schematic/PCB derivatives, place readable attribution in schematic title
blocks and release documentation; preserve upstream silkscreen attribution
where required and practical without misleadingly branding a new board as an
Adafruit product. Conversion to KiCad does not remove license obligations.

For recordings, also record performer/source rights, sample processing, loop
edits, normalization, and distribution permission. For models/libraries, audit
the library/model license separately from the board circuit.
