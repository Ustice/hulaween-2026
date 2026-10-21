# Hulaween 2026 Field Guide

Independent fan guide combining 90 official slots and 39 published campground entries as of the first edition. Sources accompany individual entries. Missing and conflicting times remain TBA. 

`python3 build.py` creates portable HTML and a browser offline cache worker. `create_pdf.py` uses ReportLab to create dist/guide.pdf with day bookmarks and Spotify deep links. Rebuild both after data changes. See UPDATE_GUIDE.md for the bounded festival monitoring procedure.

On iPhone, open the deployed page in Safari, tap Download PDF, then Share > Save to Files > On My iPhone. On Android, save the PDF in Downloads. Reopen the local PDF in airplane mode to verify availability. HTML download is a full self-contained snapshot; phone file viewers may limit interactive JavaScript. Cached live pages and downloaded files need a connected refresh/redownload for new editions. Download the music separately inside Spotify; app deep links may still need connectivity to resolve.

The current edition uses expanded official-style day grids with campground lanes and a separate nonmusic.html activities page. Each has an offline HTML and poster PDF. Full artist descriptions and Spotify deep links open from schedule blocks. Timed activities without end times are start markers, not invented duration blocks. The official Spirit Lake release is included, covering House of the Lost, Incendia, Oasis and the lake show; keep monitoring subsequent organizer announcements.

## Hosting and privacy

GitHub Pages serves `dist/` over HTTPS. Favorites stay in browser local storage; they are not uploaded or synchronized between devices. Sensor identification is not implemented. No location or microphone data is collected by this guide.

Build HTML with `python3 build.py`. Rebuild PDFs on macOS using Python with ReportLab and fontTools; the PDF builder currently uses system Arial fonts. Commit the generated `dist/` files. Pushes to `main` deploy them with GitHub Actions.

Festival artwork and fonts remain the property of their respective owners; this repository does not grant redistribution rights to those assets.
