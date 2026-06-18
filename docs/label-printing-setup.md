# Automatic label printing (no print dialog)

The check-in scan page (`validate/templates/validate/scan.html`) prints a 70×40mm
name badge for each scanned attendee. By default a browser shows the print dialog
every time. This guide sets up a station so labels print **silently** to the label
printer with no dialog.

## How it works

`printLabel()` writes the label HTML (from `buildLabelHtml`) into a hidden iframe.
That iframe's `onload` calls `window.print()`. Normally that opens the print
dialog; when the browser is launched in **kiosk printing** mode, the same call
prints immediately to the default printer with no dialog. No code change is
needed — this is purely a per-station browser setting.

## One-time station setup (Windows)

### 1. Make the label printer the default
- Settings → Bluetooth & devices → Printers & scanners.
- Turn **off** "Let Windows manage my default printer".
- Select the AIMO label printer → **Set as default**.

> Under kiosk printing, every `window.print()` goes straight to the default
> printer. If the default is not the label printer, labels will silently print to
> the wrong device.

### 2. Set the media size to 70×40mm
- Open the label printer's **Printing preferences**.
- Set the paper / media / label size to **70mm × 40mm** so it matches the label's
  `@page { size: 70mm 40mm; margin: 2mm; }`.
- If the size is wrong, the label will be cropped or scaled.

### 3. Launch the browser with the kiosk-printing flag
Point the browser at the scan page and add `--kiosk-printing`:

**Chrome**
```
chrome.exe --kiosk-printing --app=https://pikomgolf.talxone.com/<scan-page-url>
```

**Edge**
```
msedge.exe --kiosk-printing --app=https://pikomgolf.talxone.com/<scan-page-url>
```

Easiest: create a desktop shortcut whose **Target** is the full line above, and
always open the station from that shortcut.

- `--kiosk-printing` enables silent printing.
- `--app=<url>` opens the page in a clean app window (no tabs/address bar). It is
  optional — you can also just open the URL normally — but it makes for a tidier
  kiosk.

## Operating notes

- The on-page **"print label"** toggle still controls whether a label prints per
  scan. Leave it on for printing stations.
- The **"Test print"** button prints a sample badge — use it to confirm the size
  and that no dialog appears.
- A normal browser window (launched without the flag) will still show the print
  dialog. Only the flagged launch prints silently, so make sure stations use the
  shortcut.
- macOS/Linux: the same `--kiosk-printing` flag works
  (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --kiosk-printing --app=...`),
  with the OS default printer + media size configured the same way.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Dialog still appears | Browser wasn't launched with `--kiosk-printing`; use the shortcut. |
| Prints to the wrong printer | Set the label printer as the Windows default (step 1). |
| Label cropped / scaled | Set printer media size to 70×40mm (step 2). |
| Nothing prints | Check the on-page "print label" toggle is on; confirm the printer is online. |
