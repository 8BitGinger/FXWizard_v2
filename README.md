# FX Wizard: Live Graphics for OBS

![Logo](./assets/FxNoBack.png)

**FX Wizard** puts animated lower thirds and fullscreen overlays on an OBS stream, run from a simple control panel in a web browser. The panel is built for touch screens, so a producer can take and clear graphics live with a tap.

---

## ✨ Features

### Animated lower thirds
- **10 animated backgrounds:** Blue, Green, Black, Red, Space, Clouds, Tech, Finance, Sports, Politics, plus **Custom** (the first image in the `custom` folder)
- **6 font styles:** Default, Script, Fun, Modern, Classic, Accent
- **12 font colors:** White (default), Black, Silver, Gold, Yellow, Orange, Red, Pink, Purple, Blue, Sky, Green
- **9 screen positions:** any corner, any edge, or the center
- **9 animations:** Slide Up, Slide Down, Slide Left, Slide Right, Fade In, Spin, **Glitch** (flickers in as torn, color-shifted slices, and glitches out the same way), **Bounce** (drops onto its spot and bounces), and **Slam** (comes down hard from big and blurry, with a flash and a shake). All of them except Glitch fade out
- **Set duration:** how many seconds it stays on screen

### Fullscreen overlays
Each overlay has its own built-in animation, so there's nothing extra to pick.

| Overlay | What it does | In | Out |
|---|---|---|---|
| **Fullscreen L3s** | | | |
| **L3 PNG** | Full-width name bar (`assets/l3Large.png`) with an optional title | Slides in from the left | Slides back out to the left |
| **L3 Info** | One paragraph of information on `assets/l3LargeAlt.png` in the bottom-left corner. The text is centered in the image's box and wraps onto about 5 lines (up to 400 characters). Line breaks you type are kept | Slides in from the left | Slides back out to the left |
| **L3 Gif** | Name and title on a bar showing `assets/largeGif.gif`, centered across the screen | Rises up from the bottom | Drops back down |
| **Custom** | Like L3 Gif, with the first PNG, JPG or GIF in the `custom` folder. Square corners, no side borders, and the image fades out at both sides | Rises up from the bottom | Drops back down |
| **Overlays** | | | |
| **Color Wave** | Soft, color-changing glow around the edges; the center stays clear | Fades in | Fades out |
| **Confetti** | Bursts from both bottom corners, then light confetti rain | Slides up | Fades out |
| **Fall** | Red, orange, gold and brown leaves sway, spin and flip as they float down | Fades in | Fades out |
| **Snow** | Soft white snowflakes drift down; nearer flakes are bigger and faster | Fades in | Fades out |
| **Fire** | Flames burn along the bottom of the screen while glowing embers float up | Fades in | Fades out |
| **Underwater** | Blue-green water with swaying light rays, rising bubbles, and small schools of fish swimming by every few seconds | Fades in | Fades out |
| **Like, Follow & Subscribe** | **Like**, **Follow** and **Subscribe** buttons pop up along the bottom, a cursor clicks each one (they change to **Liked**, **Following** and **Subscribed**) and the bell rings, all in about 3 seconds. Any socials you add (YouTube, Facebook, Twitter, Instagram, LinkedIn, Web) show above the buttons, each with its icon | Pops up | Fades out |
| **Breaking News** | **LIVE** in the top-right corner and a red **BREAKING NEWS** bar along the bottom, with your ticker text scrolling across | Bar slides up | Fades out |
| **Stingers** | | | |
| **Stinger - Standard** | A wide band of red, white and blue stripes (some with stars) sweeps from top-left to bottom-right, covering the whole screen at the halfway point; the stripes drift slightly (about 2 seconds) | Sweeps in | Sweeps off |
| **Storm** | Storm clouds roll down with rain and lightning, cover the screen, then clear (about 2.8 seconds) | Rolls in | Clears |
| **Ghost** | A big glowing ghost rises from the bottom and floats off the top (about 2.4 seconds) | Rises in | Floats off |
| **Bars** | TV color bars: each piece slides in from its own direction, they hold, then fade (about 2.6 seconds) | Slides in | Fades out |
| **Static** | An old TV screen full of static with a rolling band (about 1.8 seconds) | Fades in | Fades out |
| **X-mas** | A candy-cane band with a string of lights sweeps from left to right (about 1.8 seconds) | Sweeps in | Sweeps off |
| **Sports** | Pick a sport (about 2.6 seconds): **Football** (one giant football jets across the screen), **Basketball** (basketballs rain down and pile up until they cover the screen), **Baseball** (home plate spins in on a patch of dirt, with a puff of dust), or **Soccer** (a ball flies straight at the camera, thumps the lens, and bounces away) | Flies, rains or spins in | Leaves the same way |
| **Spring** | Flowers pop in a few at a time until they cover the screen, butterflies flutter past, then a breeze blows the flowers away (about 3 seconds) | Pops in | Blows away |

L3 PNG, L3 Info, L3 Gif and Custom text is always shown in capitals. If text is longer than normal, it shrinks to fit instead of getting cut off.

🟩 **Greenscreen depth:** with Greenscreen on, Color Wave, Confetti, Fall, Snow, Fire and Underwater show partly *behind* you and partly *in front of* you. See [Greenscreen Depth](#-greenscreen-depth).

### Import L3s
Turn plain `.txt` files into a list of L3 graphics, ready to take. The Import button shows when **L3 PNG** or **L3 Info** is selected, and the L3s are imported as that type.
- One name per line, or `Name | Title` to add a title. For **L3 Info**, each line is one paragraph.
- Pick several files at once; they're added in file-name order.
- Each button shows the file it came from (for example **L3 1A**), which makes it easy to match a rundown.
- Imported L3s stay up for **5 minutes**, or until the producer clears them.
- Names already saved (same name and title) are skipped.

### Control panel
- **Three tabs:** Animated L3's, Fullscreen Overlays, and Podcast Rundown. Animated L3's and Fullscreen Overlays each have their own saved list.
- **Sections that open and close:** the lower third options (Background, Font Style, Font Color, Location, Animation) and the overlay groups (Fullscreen L3s, Overlays, Stingers) are big bars you tap to open or close. Each bar shows what's picked inside, and the panel remembers which ones you left open. Lower thirds start on Blue, Default, White, Bottom Left and Slide Left.
- **Saved graphics:** large, touch-friendly cards, two per row. Tap to take, ✕ to delete, ＋ to add it to the Podcast Rundown. A colored edge shows the background or overlay type. The 🗑️ next to the heading deletes everything saved on that tab (it asks first).
- **Podcast Rundown:** the graphics you added with ＋, grouped into **blocks** (A to E to start; tap **+** next to the letters to add F, G and so on). Tap a letter under **Add to** to choose which block ＋ adds to.
  - **Labels:** each card is labeled on the left with its block, number and type: **A1-L3**, **A2-L3**... for lower thirds (animated or fullscreen) and **A1-OV**, **A2-OV**... for overlays and stingers. Lower thirds and overlays are numbered separately in each block, so a graphic in block B is **B1-L3**, **B1-OV** and so on.
  - Each card shows how long it stays on screen (for example **5s** or **5:00**) so you can double-check the rundown.
  - While **Set Order** is off: drag ⠿ to reorder or to move a card to another block, ✎ to edit the text, duration or block (and Greenscreen depth, for effects that support it) for this rundown only, and ✕ to remove. ✕ next to the last block removes it when it's empty. Cards can't be taken yet.
  - Turn on **Set Order** when the show is ready, then tap a card to take it. While it's on, **Add to** becomes **ALL**: tap **ALL** to see the whole rundown, or a letter to see just that block. Empty blocks are greyed out.
  - While a card is on screen it's outlined in green, with a floating red **⏹ OFF** button that counts down the time left; tap it to take the graphic down early. A ★ marks the one played last.
  - The 🗑️ empties the rundown (saved graphics aren't affected, and the blocks stay). **CLEAR ALL** is right at the top.
  - **💾 Save Rundown / 📂 Import Rundown** (shown while Set Order is off): save the whole rundown, its blocks and a full copy of every graphic, as a file in the `rundowns` folder, and bring it back later, like a template. It still works after those graphics are deleted from Saved, and the files can be copied to another computer. See [Saving rundowns](#saving-rundowns).
- **TOGGLE ON / TOGGLE OFF:** puts the graphic up with no time limit. The button turns yellow and pulses and reads **TOGGLE OFF** until you press it again, press Clear All, or take something else on the same tab. Stingers play once, so it's greyed out for them.
- **Message box:** floats at the bottom of the panel on every tab and shows what you just took and how long it will stay up, for example **Taken: Ryan Fann** *for 5:00*. It lights up for each new message, dims after 3 seconds, and goes back to **Ready** after 15 seconds with nothing new.
- **Clear All:** takes everything off screen right away, with its normal out animation.
- **Toggle bar** (under the connection status):
  - **Greenscreen** on the left: turns on [Greenscreen Depth](#-greenscreen-depth). It's always off when the panel opens. On the Podcast Rundown tab, it pulses amber if the rundown is running (**Set Order** on) and has effects set for Greenscreen while it's off.
  - **Light mode** on the right: shows 🌙 in dark mode and ☀️ in light mode. Dark is the default, and the browser remembers your choice.
- **🔧 Connection help:** the wrench in the top bar opens a window with the live connection status and a list of things to check when it isn't **OPEN**.

---

## 🔌 How It Works

```
Control panel  ──►  Server (port 8080)  ──►  Display page in OBS
(your browser)      (relays messages)       (shows the graphics)
```

- **Control panel:** `websocket_demo.html`, opened in any browser.
- **Display:** the same file with `#display` on the end, added to OBS as a Browser Source.
- **Underlay** (optional, for Greenscreen): the same file with `#underlay` on the end, added to OBS *below* your keyed camera.
- **Server:** passes each message from the control panel to the display. It can run inside OBS (Python) or on its own (Node.js).

---

## 🛠️ Setup Option A: Server Inside OBS (Recommended)

_The server starts and stops with OBS automatically._

### 1. What you need
- **OBS Studio** with Python scripting
- **Python 3.11 (64-bit)**
- The `websockets` Python library

### 2. Install
1. **Install the library.** Open a terminal and run:
   ```bash
   python -m pip install websockets
   ```
2. **DLL fix.** In your Python install folder, copy `python311.dll` and rename the copy to `python3.dll`. This lets OBS load Python.
3. **Load the script.**
   - In OBS, go to **Tools > Scripts**.
   - On the **Python Settings** tab, set the path to your Python folder (for example `C:\Program Files\Python311`).
   - On the **Scripts** tab, click **+** and add `server.py`.
4. **Check it.** Open the control panel. The bar at the top should say **Connection Status: OPEN**.

---

## 🛠️ Setup Option B: Standalone Node.js Server

_Runs in its own window, separate from OBS._

### 1. What you need
- **Node.js**

### 2. Install
1. In a terminal in the project folder, run:
   ```bash
   npm install
   ```
2. Start the server:
   ```bash
   node server.js
   ```
   You can also double-click `launch_server.bat`. Open it in a text editor first and change the folder path to where FX Wizard is on your computer.

---

## 📺 Add the Display to OBS

1. Add a **Browser Source**.
2. Check **Local file** and choose `websocket_demo.html`.
3. Add `#display` to the end of the file path.
4. Set the size to your canvas, for example **1920 x 1080**. Fullscreen overlays are designed for 1920 x 1080.

---

## 🟩 Greenscreen Depth

If you key yourself out of a greenscreen in OBS, FX Wizard can put some of an overlay **behind** you and some **in front of** you, for a deeper, 3D look. Snow falls behind you *and* past the camera; fish swim behind your head and across your face.

### Set it up in OBS
1. Add another **Browser Source** with `websocket_demo.html#underlay` (same size as your canvas).
2. Order your sources (top of the list = front):
   ```
   websocket_demo.html#display    ← in front of you
   Your camera (with Chroma Key)
   websocket_demo.html#underlay   ← behind you
   Your background
   ```
3. In the control panel, turn on **Greenscreen** in the toggle bar.

### What goes where
| Overlay | Behind you (`#underlay`) | In front of you (`#display`) |
|---|---|---|
| **Snow** | Small, far-away flakes | Bigger, closer flakes, plus a few big soft ones drifting right past the camera |
| **Fall** | Small, far-away leaves | Bigger leaves, plus a few big blurry ones close to the camera |
| **Confetti** | Smaller, slower confetti rain | The corner bursts and full-size confetti |
| **Fire** | The flames and their glow | Big embers drifting up, and a faint warm glow lighting you from below |
| **Underwater** | Deep water, light rays, ripples, far fish and small bubbles | A light blue tint (so you look underwater too), big bubbles, and close fish swimming past |
| **Color Wave** | The whole colored glow, like a backlight | Nothing |

Everything else (lower thirds, the Fullscreen L3s, Breaking News, and all the stingers) stays on `#display` in front, as usual. With Greenscreen off, the underlay stays empty, so you can leave it in your scene.

### Effects saved for Greenscreen
Greenscreen is **off** every time the control panel opens. If you **save** one of the effects above while Greenscreen is on, it remembers that it's meant for Greenscreen and shows a small green mark on its card. You can also tick **Greenscreen depth** with ✎ on a Podcast Rundown card.

When a running Podcast Rundown (**Set Order** on) has any of these but Greenscreen is off, FX Wizard warns you:
- an offer to turn it on when you turn on **Set Order**
- a yellow banner at the top of the Podcast Rundown, with a **Turn on** button
- on the Podcast Rundown tab, the **Greenscreen** switch pulses amber, and you're asked before you turn Greenscreen off
- a warning in the message box if you take one of those rundown cards while it's off

Without a running rundown (or on the other tabs), Greenscreen turns off without asking.

What gets sent always follows the switch: with Greenscreen off, those effects play normally on `#display`.

---

## 💻 Using the Control Panel

Open `websocket_demo.html` in a browser (without `#display`). Check that the top bar says **OPEN**.

### Animated L3's tab
1. Type a **Name** and an optional **Title**.
2. Set the **Duration** in seconds.
3. Tap a section to open it and pick a **Background**, **Font Style**, **Font Color**, **Location**, or **Animation**.
   - **Custom background:** put an image (PNG, JPG or GIF) in the `custom` folder next to `assets`, then tap **Custom…**. It uses the first image in the folder by file name, and checks the folder again each time you tap it or the panel connects. (If the server is older and can't read the folder, a file picker opens instead.)
4. Press **⚡ TAKE** to put it on screen now, **TOGGLE ON** to keep it up until you turn it off, or **💾 SAVE** to add it to Saved Animated Lower Thirds.

### Fullscreen Overlays tab
1. Open **Fullscreen L3s**, **Overlays** or **Stingers** and pick one.
2. For L3 PNG, L3 Gif and Custom, type a **Name** and an optional **Title**. For L3 Info, type the paragraph in **Text**.
   - **Custom:** same as the Custom background: tap **Custom…** to use the first PNG, JPG or GIF in the `custom` folder.
   - **Like, Follow & Subscribe:** under **Socials**, tap an icon (YouTube, Facebook, Twitter, Instagram, LinkedIn, Web) to open a box for that account and type it in. Tap the icon again to leave it out. All of them are optional, and the panel remembers what you typed. Give it at least 4 seconds so the clicks finish.
   - **Breaking News:** type the scrolling text in **Ticker text**. **TOGGLE ON** keeps it up until you turn it off.
   - **Sports** (a stinger): pick **Football**, **Basketball**, **Baseball** or **Soccer** under **Sport**.
3. Set the **Duration**. The stingers have a fixed length, so this field is hidden for them.
4. Press **⚡ TAKE**, **TOGGLE ON**, or **💾 SAVE**.

### Importing L3s
1. Make a `.txt` file with one name per line:
   ```
   Jane Smith
   Marcus Lee
   Dr. Alicia Gomez | Keynote Speaker
   ```
2. On the Fullscreen Overlays tab, pick **L3 PNG** or **L3 Info**, then press **📄 IMPORT L3s (.txt)** and choose one or more files.
3. The names appear under **Saved Overlays**, each labeled with its file name.

### Running a show
1. Open **Podcast Rundown** and tap the block you're filling under **Add to** (A to start).
2. On the Animated L3's and Fullscreen Overlays tabs, tap **＋** on each saved graphic for that block, in show order. Then pick the next block and repeat. Need more than A to E? Tap **+** next to the letters.
3. Back on **Podcast Rundown**, drag ⠿ to fix the order (or move a card to another block), ✎ to tweak anything for this rundown, and check each card's label and time.
4. Turn on **Set Order**. Cards can only be taken once it's on. Tap **ALL** or a block letter to choose what's shown.
5. During the show, tap each card to take it. It's outlined in green while it's on screen, with a **⏹ OFF** button to take it down early, and ★ marks the one played last.

### Saving rundowns
1. Build the rundown, then press **💾 Save Rundown** (Set Order must be off) and give it a name.
2. It's saved as `rundowns/<name>.json` next to `websocket_demo.html`. Saving with a name that's already there asks before replacing it.
3. To use it again, press **📂 Import Rundown** and tap it in the list (newest first), or **Choose a file…** to open a rundown file from anywhere. Importing replaces the current rundown (it asks first) and turns Set Order off so you can check it.

The file holds everything needed, so it works even if those graphics were deleted from Saved. The server does the saving, so it needs the current `server.py` or `server.js` (after updating, reload the script in OBS under **Tools > Scripts**, or restart `node server.js`). With an older server, **Save Rundown** downloads the file instead: move it into the `rundowns` folder.

### During the show
- **Tap a saved card** (or a Podcast Rundown card, once Set Order is on) to take it. **⏹ OFF** on a live rundown card takes it down early.
- **✖ CLEAR ALL** removes everything from the screen, including anything toggled on.
- **TOGGLE OFF** takes down the graphic you toggled on.
- If the top bar says **CLOSED**, press the **🔧** for things to check.
- Using a greenscreen? Turn on **Greenscreen** before you take Snow, Fall, Confetti, Fire, Underwater or Color Wave. It starts off each time the panel opens.
- **✕** on a card deletes it (you'll be asked to confirm).

---

## 🎨 Customizing

| To change... | Look in | What to edit |
|---|---|---|
| Lower third text size | `css/styles.css`, section 4 | `font-size` in `#action-name` and `#action-title` |
| Add a lower third background | `css/styles.css`, section 5 | Add a class with your GIF from `assets/`, add a button in the **Backgrounds** part of `websocket_demo.html`, and add the name to `BG_CLASSES` in the script |
| L3 PNG image | `assets/l3Large.png` | Replace the image (1920 x 1080) |
| L3 PNG font or size | `css/styles.css`, section 7 | `#overlay-box.l3Large #overlay-text` and `#overlay-name` |
| L3 Info image | `assets/l3LargeAlt.png` | Replace the image (1920 x 500). If the box inside moves, adjust `#overlay-box.l3LargeAlt #overlay-text` |
| L3 Info size or position | `css/styles.css`, section 7 | `--alt-width`, `--alt-left` and `--alt-bottom` in `#overlay-box.l3LargeAlt`. The text follows |
| L3 Gif GIF | `assets/largeGif.gif` | Replace the GIF |
| L3 Gif bar size or position | `css/styles.css`, section 7 | `#overlay-gif` |
| Stinger - Standard speed, colors, or drift | `css/styles.css`, section 7 | The `--stinger-...` settings at the top of `#stinger`. Stripe thicknesses are the `--h` values in `websocket_demo.html` |
| Like, Follow & Subscribe look or timing | `css/styles.css`, section 7 | `.sc-btn` (colors are `--bg0`/`--bg1`, click times are `--t`), the `scCursor` keyframes, and `.sc-pill` for the socials. Social icon colors are the `.sc-youtube`, `.sc-facebook`... rules |
| Breaking News look | `css/styles.css`, section 7 | `.bn-live`, `.bn-bar`, `.bn-label` and `#breaking-text`. Scroll speed is `TICKER_SPEED` in the script |
| Ghost stinger speed or colors | `css/styles.css`, section 7 | The `--ghost-...` settings at the top of `#ghost` |
| X-mas stinger speed or colors | `css/styles.css`, section 7 | The `--xmas-...` settings at the top of `#xmas` |
| Storm, Static, Sports or Spring stinger length | `websocket_demo.html`, script section 2 | `length` on `storm`, `tvstatic`, `sportsfx` or `spring` in `OVERLAYS` (in seconds) |
| Greenscreen split (how much goes behind or in front) | `websocket_demo.html`, script section 6 | `DEPTH` near the top of the canvas effects |
| Bars stinger length or colors | `css/styles.css` (`--bars-time`, `--bar-slide`) and `websocket_demo.html` (each bar's color, direction and delay) | |
| Glitch, Bounce or Slam animation | `css/styles.css`, section 8 | The `glitchIn`, `glitchOut`, `bounceIn` and `slamIn` keyframes |
| Podcast Rundown blocks to start with | `websocket_demo.html`, script section 15 | `DEFAULT_BLOCKS` |
| Imported L3 duration | `websocket_demo.html`, script section 1 | `IMPORT_DURATION` (in seconds) |
| Server address | `websocket_demo.html`, script section 1 | `SOCKET_URL` |

Both `styles.css` and the script in `websocket_demo.html` start with a numbered list of their sections.

---

## 📝 Good to Know

- **Saved graphics and the Podcast Rundown live in the browser.** They're stored on the computer and browser where you saved them. Clearing that browser's data deletes them, and a different computer or browser starts with an empty list. Use **💾 Save Rundown** to keep a rundown as a file.
- **Large GIFs load the first time.** Some backgrounds are 20–50 MB, so a background can take a moment to appear the first time it's used.
- **Older saves still work.** Graphics saved with earlier versions still open correctly.
- **Sharing the project:** `custom/` and `rundowns/` keep your own files out of Git (see `.gitignore`); only their `README.txt` is shared. Python's `__pycache__` is ignored too.

---

## 📁 Project Files

| File | What it is |
|---|---|
| `websocket_demo.html` | The control panel, the display (`#display`) and the greenscreen underlay (`#underlay`), all in one page |
| `css/styles.css` | All the styles and animations |
| `assets/` | Background GIFs, the L3 images, and logos |
| `custom/` | Your own image for the **Custom…** background and the **Custom** Fullscreen L3 (the first PNG, JPG or GIF by name is used). Not shared in Git |
| `rundowns/` | Saved Podcast Rundowns, one `.json` file each. Not shared in Git |
| `server.py` | Server that runs inside OBS (also lists `custom/`, and saves and opens rundowns in `rundowns/`) |
| `server.js` | Standalone Node.js server (same as `server.py`, outside OBS) |
| `launch_server.bat` | Double-click launcher for the Node.js server |

---

## 📜 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 📧 Contact

For support, contact the author at **ryan.fann@gmail.com** or visit the GitHub repository: **FXWizard**

## 🌟 Acknowledgements

This project benefited from the assistance of Gemini, a large language model, in the following areas:

- **Architectural Design**: Transitioning to an internal Python WebSocket server for OBS.
- **UI Refinement**: Implementation of Tailwind CSS and studio-grade color palettes.
- **Debugging**: Resolving CSS animation conflicts and Python async loop errors.
- **Branding**: Generation of the FX Wizard Logo.
- **Gifs**: Used [EzGif](https://ezgif.com/video-to-gif) to transfer content from [Storyblocks](https://www.storyblocks.com/)
- **Fonts**: [Google Fonts](https://fonts.google.com/)
