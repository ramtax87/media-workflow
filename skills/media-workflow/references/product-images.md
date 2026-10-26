# Official product references and realistic catalogue images

For an item list or specific real products, use this mode alongside
[workflow.md](workflow.md) and the record format in [records.md](records.md).

Keep the distinction between an official source photograph and an AI-edited
derivative visible in their records and delivery notes.

## Start with an item list

A spreadsheet, CSV, catalogue export or plain list is sufficient. Preserve item
IDs and supplied brand, name, SKU/GTIN, pack size, variant and market. Record unknowns.

This fictional example illustrates the input, not real searchable products:

```csv
id,brand,sku,gtin,name,pack_size,variant,market,output
oil-750,Example Pantry,EP-O750,,Olive oil,750 ml,Glass bottle,DE,WebP 1200x1200
oats-500,Example Pantry,EP-OT500,,Oat flakes,500 g,Fine cut,DE,WebP 1200x1200
soap-1l,Example Home,EH-S1000,,Hand soap,1 L,Unscented refill,DE,WebP 1200x1200
```

## Find and match the source

Search the manufacturer or brand website first, including official media libraries,
product pages and authorized supplier assets. Search-result thumbnails help discovery;
open the source page and original image before accepting the match. Prefer an
adequate-resolution source over an enlarged thumbnail. A retailer image is not an
official manufacturer source merely because it appears first in search.

Compare SKU/GTIN where available, then brand, product name, quantity, variant,
packaging and market. Reconcile labels against the source page and item list.
Packaging revisions can differ; record which revision was found. Preserve the
source page URL, image URL, retrieval time and observed matching evidence.

| Example finding | Decision |
| --- | --- |
| `oil-750`: official page confirms the SKU and a 750 ml bottle | Accept the identity match; prepare the requested format. |
| `oats-500`: only a 1 kg pack is found | Mark ambiguous/missing; seek the exact pack or ask for a reference. Do not relabel the 1 kg pack. |
| `soap-1l`: the available photo shows a scented pump bottle | Reject the match; it is a different variant and container. |

Download only the intended image through a supported browser/download tool, retaining
untouched source bytes in the private archive. Do not bypass access controls or
execute downloaded content. Record the image's rights status as user-provided
permission, documented licence, applicable supplier agreement, or unknown, with
evidence where available. Public accessibility and AI regeneration do not grant
reuse rights. Keep unknown status explicit for the owner before public use.

## Choose the smallest transformation that meets the request

**Format-only:** Use this when “compatible” means file type, dimensions, compression
or transparency already present in the source. Preserve the product's appearance;
fit it within the target canvas without distortion or clipped labels. Conversion
does not require a generative model. Inspect the resulting file.

**Licensed source:** Use an authorized source asset with its required attribution
or other recorded conditions. Do not call a retailer or stock image manufacturer
official without evidence. Any conversion still keeps the source relationship.

**Reference-guided edit:** Use this when the request needs a changed background,
consistent studio composition or another substantive visual change. Inspect the
source and supply it as the image tool's reference. Record the exact edit prompt,
reference hash and returned original. Preserve brand, logos, spelling, quantities,
package geometry, variant colours and visible claims. Ask the model to change only
the requested presentation, then verify that it did so.

**Generated illustration:** Use this for generic items or when the owner accepts
an illustrative replacement. Record it as generated. A convincing image of an
invented package cannot be described as an official photograph of the listed SKU.
If exact branded fidelity is required and no suitable reference exists, leave the
item blocked instead of silently substituting a plausible image.

## Review for product fidelity

Compare the source and result individually. Read the visible brand, product name,
quantity and label text; inspect the container, closure, colour and variant.
Reject invented certifications, altered claims, wrong ingredients or changed pack
sizes. Do not repair uncertain text by guessing. If a generative edit repeatedly
changes packaging, use the faithful source with simpler presentation changes or
report the limitation.

Inspect the final encoded version at the intended display size. Small writing
must not become a different readable claim after sharpening or regeneration.
Check all requested aspect ratios and thumbnails; the correct large image does
not prove that the product remains identifiable in a small crop.

Retain source and generation provenance separately: official source URL and hash,
reference relationship, tool/model when known, actual edit prompt, rejected attempts,
selected result, review evidence and final-file hashes. Preserve C2PA or other
provenance metadata where supported. If an export cannot retain it, keep the original
and sidecar record; never remove provenance to disguise an AI edit as an untouched
official photograph.

## Hand off the catalogue

Deliver the item-ID-to-file mapping and label each result as sourced, converted,
reference-edited or generated. Include unresolved source matches and rights status
in the handoff. Keep missing items visible so the website can use an agreed fallback
without confusing it with the exact product. Follow the main workflow's private Git,
original-backup and publication boundaries.
