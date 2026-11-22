# Original website restoration and review

## Foundation and comparison

The production-source commit used for comparison was bdef77be974cf9cdbef7ecade8ef5187aeef3979. The independent Phase 1.1 copy retains the same section text as that commit and supplies the corrected shared header and footer. This review package uses those pages as its foundation. The shorter final redesign supplied reusable enquiry handling, navigation behaviour, SEO generation and validation code. All work was performed in DH-Construction-Preserved.

The table counts page content sections; the floating assistant and shared shell are excluded. Heights are the full document in CSS pixels from the local Chromium run with external requests blocked. Responsive wrapping and external content can affect the final height on a visitor’s device.

| Original page path | Previous redesign sections | Original sections restored | Original section images | Height at 390 px | Height at 1440 px |
| --- | ---: | ---: | ---: | ---: | ---: |
| index.html | 7 | 13 | 24 | 18,168 | 10,578 |
| about/about.html | 4 | 9 | 1 | 13,572 | 7,421 |
| services/All_services.html | 5 | 6 | 1 | 12,194 | 6,592 |
| Projects/projects.html | 3 | 8 | 1 | 13,936 | 6,951 |
| Contact/contact.html | 4 | 3 | 0 | 6,188 | 3,443 |
| services/Buliding_Construction.html | 6 | 11 | 29 | 18,539 | 10,612 |
| services/Building_rennovation.html | 6 | 12 | 6 | 18,756 | 10,899 |
| services/interior_designs.html | 6 | 9 | 18 | 12,427 | 7,843 |
| services/Infrastructure.html | 6 | 11 | 7 | 18,397 | 10,459 |
| services/Glass.html | 7 | 11 | 7 | 17,634 | 10,836 |
| services/falseceling.html | 7 | 13 | 7 | 20,945 | 12,088 |

All 106 content sections were compared in source order. Automated checks matched 2,246 original text fragments, section classes and identifiers, headings, all 101 original image placements, parent classes and alt attributes, AOS effects, canvas identifiers and counter targets. Original keyframe names remain present. The About page includes the hero, story, mission and vision, values, journey, statistics, reasons to choose the company, team and closing call to action.

## Changes to the original experience

- Preserved the original inline page layouts and animations, typography, hero treatments, card grids, portfolio descriptions, timeline, statistics, testimonials, images and CTAs. Shared navigation and footer correct cross-page links and branding. The footer includes original page-specific descriptions, contact details, service topics and copyright text.
- Local copies of Bootstrap 5.3.2, Bootstrap Icons 1.11.3, AOS 2.3.4, Poppins and Playfair Display replace requests to those CDNs. Their licenses are included. Lower-page images use lazy loading. The navigation retains the source logo and offers an optimized copy of the same mark.
- Kept all eight forms in their original layout with their original labels, fields, service options and submit buttons. Connected their labels and controls, added consent and native validation, and replaced simulated success/reset timers with real prefilled WhatsApp handoffs. Submission is independent of AOS.
- Added a compact conversational assistant beside the original contact controls. Suggested replies advance immediately. Visitors can also type a custom service, property or start time. They can supply or skip a budget, minimize and return, edit individual answers, and submit directly from the consented review.
- Added keyboard controls for the FAQ, galleries, project cards and estimate options, proper focus return from dialogs, navigable headings and landmarks, visible focus and stronger text contrast. Restored counters run during scrolling and use their final value under reduced motion. The calculator retains original prices and handles fractional areas and invalid or negative inputs.
- Retained the case-sensitive URLs, shared template generator, per-page titles and descriptions, social metadata, preview canonicals and sitemap. The test build requests no indexing.

## Checks executed

| Check | Result |
| --- | --- |
| Static source and navigation | Six automated tests passed, including parity, all local HTML links and fragments, required local assets, landmarks, correct current menu item on every page, all six services and footer destinations. |
| Responsive browser run | 121 passes covering all 11 pages at widths 320, 360, 390, 430, 768, 992, 1024, 1280, 1440 and 1920, plus 844 × 390 landscape. No measured horizontal page overflow, initial heading overlap, local HTTP resource error or uncaught page script error. All routes ran under a project subdirectory. |
| Navigation | All 66 page/width navigation cases passed, including touch emulation, Enter, Arrow Down, Tab, Escape, focus restoration, desktop/mobile breakpoint changes, current service selection and native no-JavaScript disclosure. |
| Original interactive content | 41 FAQ questions toggled by keyboard, 16 filter selections, 60 image or project-detail dialogs opened and dismissed with focus restored, and all ten calculator option buttons exercised. Confirmed fractional, empty and negative area behaviour. Verified 28 original counter targets and 32 motion-enabled counter checks including the About page statistics. |
| Forms and assistant | Eight forms and 54 fields exercised. Tested missing information and consent, malformed phone/email, double submits, popup fallback, encoded Unicode and punctuation, and recipient 919042356696. Validated optional budget entry and skipping, suggested and typed answers, Back, Edit, minimize/resume, close/reset, consent after editing and one final WhatsApp handoff. |
| Accessibility | Axe-core 4.10.3 returned zero rule violations in 22 scans, covering all eleven initial pages at 375 and 1440 px. This automated result is limited to the tested states. |
| Screenshots | Screenshots of all 11 pages at 390 and 1440 px, plus the open assistant on mobile, are in review/screenshots. The restricted test browser did not load external photo or map tiles. |

## External dependencies and owner checks

1. **Original photographs.** The source has five committed raster files, all preserved byte-for-byte. Its 101 section image placements reference 60 distinct URLs across Unsplash and Picsum. Requests to those hosts returned HTTP 403 from this environment. The package preserves their original addresses and positions. The visual review could not establish that each remote file will load or that any image depicts a company project. The source includes no locally stored copy of those remote files. The README explains optional caching from a computer that can reach both hosts.
2. **WhatsApp.** The source uses +91 90423 56696. The tests intercepted the outgoing WhatsApp draft and inspected the full encoded content. The business owner should confirm ownership and receipt with a consented test on an actual device. Clicking Submit opens WhatsApp directly. The visitor must press Send there. No messages were sent during QA.
3. **Business content.** The original testimonials, project/client names, awards or claims, figures, pricing and warranties are reproduced as requested. Their authenticity and publication permissions require owner review. The original pages also differ on opening hours, Sunday availability and the detailed address. Confirm them and the exact map pin before production.
4. **Browser and hosting scope.** Tested Chromium with desktop and touch-device emulation. Physical devices, other browser engines, live Google Maps, live message delivery and an actual GitHub Pages deployment were outside this run. Local serving exercised a repository subpath. The original production CNAME is in the ZIP and should be removed only from the separate test copy before publishing.

## Repeat the checks

Use Python 3 for the generator. Unit parity tests additionally use lxml. Browser checks use Python Playwright and Chromium. The optional accessibility scan accepts a local axe-core bundle.

    python tools/render_shared.py --check
    python -m unittest discover -s tests -v
    python tests/browser_navigation.py
    python tests/enquiries_browser.py
    python tests/browser_restoration.py --artifacts /path/to/review/screenshots
    python tests/audit_accessibility.py --axe /path/to/axe.min.js

The release includes per-file checksums in review/SHA256SUMS.txt. The ZIP was re-opened, CRC-tested and compared to its source, then extracted into a fresh directory for generator, unit and local hosting checks.
