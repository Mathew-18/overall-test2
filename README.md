# DH Construction — original website restored

Open the site at index.html through a local web server. All 11 generated pages are in the ZIP with their original filenames and directory paths. Its foundation is the original website source at bdef77be974cf9cdbef7ecade8ef5187aeef3979 and the earlier shared navigation work. The individual page bodies retain the long original layouts, copy, projects, customer quotations, image slots, counters, canvas art and animations.

## Preview on Windows

1. Extract the entire ZIP to a folder.
2. Open PowerShell in the folder containing index.html.
3. Run `py -m http.server 8000 --bind 127.0.0.1`.
4. Open `http://127.0.0.1:8000/` in Chrome. Press Ctrl+C in PowerShell to stop.

The CSS, JavaScript, logo, Bootstrap, icons, AOS and fonts ship locally. As in the original website, the content photographs use external image URLs and the Contact map uses an external Google Maps embed. Open the preview with internet access to these hosts to review the images and map. The bundled screenshots were captured with external requests blocked.

## Review on your separate GitHub Pages test repository

1. From an extracted **test copy**, remove the root CNAME before uploading. Remove it from the test repository too if it already exists there. The original CNAME is intentionally in this ZIP.
2. Upload the contents, including index.html and its sibling folders, to the root of main in the separate test repository. Retain exact filename capitalization. The review and tests folders can be kept locally.
3. Select **Settings → Pages → Deploy from a branch → main → / (root)**. Leave the test repository’s custom domain empty.
4. Open the address GitHub supplies when the deployment finishes. The default canonical and sitemap root is configured for Mathew-18/DH_Construction_Phase1_Test. Preview pages request no indexing.

## Updating the source

Each page is ordinary editable HTML. Page-specific CSS and original animation code stay with their page. Edit templates/header.html, templates/footer.html, templates/assistant.html and data/site.json for shared content. The generator updates only marked regions and the discovery files.

    python tools/render_shared.py
    python tools/render_shared.py --check

For a different test host use `--base-url https://example.github.io/TEST-REPO/` when generating and checking. For a separately approved production build use `--production` with the confirmed production base URL. Python is a development tool. Site visitors do not need it.

## Enquiries

All eight original page forms use their original labels, fields, choices and placement. Submitting with consent opens a WhatsApp draft. The guided assistant accepts suggested choices or free text, includes an optional budget, and lets the visitor correct individual answers. The final **Submit via WhatsApp** action goes straight to a draft. The visitor reviews it and presses Send in WhatsApp. A link to the same draft is available if the browser blocks the popup. The site does not report delivery or store enquiries on a server.

The destination is +91 90423 56696 from the original project. Automatic delivery would require a separately approved backend using the official WhatsApp Business Cloud API, approved sender configuration, valid credentials held on that backend, and a suitable consent and delivery-status flow. This package requires no API token or subscription.

See review/REPORT.md for the comparison, testing evidence, external dependencies and owner checks. review/SHA256SUMS.txt records the SHA-256 digest of each other file in the archive.

## Optional offline copy of the original photographs

If the original image hosts are accessible from your computer and you want a portable copy, run `py tools/cache_original_images.py --download` **inside a separate extracted folder**. It downloads only the original image URLs, saves recognized image files under assets/original-media, and adds a relative srcset to the matching image tags. The original src, caption and placement stay in the HTML. It lists any unavailable URLs and keeps their existing references. Run without --download to see the count without changing files. The supplied ZIP retains the hosted references from the source.
