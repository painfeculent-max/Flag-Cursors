"""Flag Cursors – curseurs de souris aux couleurs de plus de 100 pays, ou 100 % perso."""
import sys
from tkinter import colorchooser

import customtkinter as ctk

import engine
from flags import FLAGS, REGIONS, render_flag

# ------------------------------------------------------------- palette
BG = "#0b0d14"
PANEL = "#12151f"
CARD = "#1a1e2b"
CARD_HOVER = "#262c42"
ACCENT = "#7c5cff"
ACCENT_HOVER = "#947aff"
TEXT = "#eef0f8"
MUTED = "#8b91a8"
GOOD = "#4ade80"
BAD = "#f87171"

COLS = 5
ALL = "Tous"
SKIN_FLAG, SKIN_CUSTOM = "Drapeau", "Personnalisé"


def to_ctk(pil_img, size):
    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)


def seg(parent, values, command):
    return ctk.CTkSegmentedButton(
        parent, values=values, command=command, fg_color=BG, selected_color=ACCENT,
        selected_hover_color=ACCENT_HOVER, unselected_color=BG,
        unselected_hover_color=CARD_HOVER, text_color=TEXT)


def menu(parent, values, command):
    return ctk.CTkOptionMenu(
        parent, values=values, command=command, fg_color=CARD, button_color=ACCENT,
        button_hover_color=ACCENT_HOVER, dropdown_fg_color=CARD,
        dropdown_hover_color=CARD_HOVER, text_color=TEXT, dropdown_text_color=TEXT)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("Flag Cursors")
        self.geometry("1260x780")
        self.minsize(1120, 680)
        self.configure(fg_color=BG)

        self.st = engine.load_state()
        self.var_hand = ctk.BooleanVar(value=self.st["hand"])
        self.var_startup = ctk.BooleanVar(value=self.st["startup"])
        self.region = ALL
        self.cards = {}
        self.color_btns = {}
        self._preview_job = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_left()
        self._build_right()
        self._build_cards()
        self._refresh_grid()
        self._set_skin_type(self.st["skin"]["type"])

    # ------------------------------------------------------------ gauche
    def _build_left(self):
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(24, 12), pady=24)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(3, weight=1)

        head = ctk.CTkFrame(left, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(head, text="Flag Cursors", text_color=TEXT,
                     font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(head, text=f"{len(FLAGS)} drapeaux · ou crée ton propre curseur dans l'onglet « Personnalisé »",
                     text_color=MUTED, font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(2, 14))

        self.search = ctk.CTkEntry(left, placeholder_text="🔍  Rechercher un pays…", height=42,
                                   corner_radius=21, fg_color=PANEL, border_color=CARD_HOVER,
                                   text_color=TEXT, font=ctk.CTkFont(size=14))
        self.search.grid(row=1, column=0, sticky="ew")
        self.search.bind("<KeyRelease>", lambda e: self._refresh_grid())

        self.seg_region = ctk.CTkSegmentedButton(
            left, values=[ALL] + REGIONS, command=self._on_region, height=34,
            fg_color=PANEL, selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
            unselected_color=PANEL, unselected_hover_color=CARD_HOVER, text_color=TEXT)
        self.seg_region.set(ALL)
        self.seg_region.grid(row=2, column=0, sticky="ew", pady=(12, 12))

        self.scroll = ctk.CTkScrollableFrame(left, fg_color=PANEL, corner_radius=18,
                                             scrollbar_button_color=CARD_HOVER,
                                             scrollbar_button_hover_color=ACCENT)
        self.scroll.grid(row=3, column=0, sticky="nsew")
        for c in range(COLS):
            self.scroll.grid_columnconfigure(c, weight=1, uniform="c")

    def _build_cards(self):
        for region, name, ops in FLAGS:
            img = to_ctk(render_flag(ops, 176, 118), (88, 59))
            btn = ctk.CTkButton(
                self.scroll, text=name, image=img, compound="top", width=120, height=104,
                corner_radius=14, fg_color=CARD, hover_color=CARD_HOVER, text_color=TEXT,
                border_width=2, border_color=CARD, font=ctk.CTkFont(size=12),
                command=lambda n=name: self._pick_flag(n))
            self.cards[name] = (region, btn)

    def _refresh_grid(self):
        q = self.search.get().strip().lower()
        for _, btn in self.cards.values():
            btn.grid_forget()
        i = 0
        for _, name, _ in FLAGS:
            region, btn = self.cards[name]
            if self.region != ALL and region != self.region:
                continue
            if q and q not in name.lower():
                continue
            btn.grid(row=i // COLS, column=i % COLS, padx=6, pady=6, sticky="ew")
            i += 1

    def _on_region(self, value):
        self.region = value
        self._refresh_grid()

    # ------------------------------------------------------------- droite
    def _build_right(self):
        right = ctk.CTkScrollableFrame(self, fg_color=PANEL, corner_radius=24, width=392,
                                       scrollbar_button_color=CARD_HOVER,
                                       scrollbar_button_hover_color=ACCENT)
        right.grid(row=0, column=1, sticky="ns", padx=(12, 24), pady=24)
        self.right = right

        ctk.CTkLabel(right, text="APERÇU", text_color=MUTED,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 8))
        stage = ctk.CTkFrame(right, fg_color=CARD, corner_radius=18)
        stage.pack(fill="x", padx=14)
        for col, (title, attr) in enumerate((("Normal", "prev_n"), ("Lien", "prev_l"))):
            stage.grid_columnconfigure(col, weight=1)
            lbl = ctk.CTkLabel(stage, text="")
            lbl.grid(row=0, column=col, pady=(16, 4))
            setattr(self, attr, lbl)
            ctk.CTkLabel(stage, text=title, text_color=MUTED,
                         font=ctk.CTkFont(size=12)).grid(row=1, column=col, pady=(0, 12))

        self.lbl_name = ctk.CTkLabel(right, text="", text_color=TEXT,
                                     font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_name.pack(pady=(12, 0))
        self.lbl_region = ctk.CTkLabel(right, text="", text_color=MUTED, font=ctk.CTkFont(size=13))
        self.lbl_region.pack(pady=(0, 6))

        self._section("Couleurs")
        self.seg_skin = seg(right, [SKIN_FLAG, SKIN_CUSTOM], self._set_skin_type)
        self.seg_skin.pack(fill="x", padx=14)
        self._build_custom_editor()

        self._section("Forme du curseur normal")
        self.menu_n = menu(right, engine.SHAPES, lambda v: self._on_shape("shape_normal", v))
        self.menu_n.set(self.st["shape_normal"])
        self.menu_n.pack(fill="x", padx=14)

        self._section("Forme du curseur lien")
        self.menu_l = menu(right, engine.SHAPES, lambda v: self._on_shape("shape_link", v))
        self.menu_l.set(self.st["shape_link"])
        self.menu_l.pack(fill="x", padx=14)

        self._section("Taille (px)")
        self.seg_size = seg(right, [str(x) for x in engine.SIZES], self._on_size)
        self.seg_size.set(str(self.st["size"] if self.st["size"] in engine.SIZES else 48))
        self.seg_size.pack(fill="x", padx=14)

        sw = dict(progress_color=ACCENT, button_color=TEXT, text_color=TEXT,
                  font=ctk.CTkFont(size=13))
        ctk.CTkSwitch(right, text="Changer aussi le curseur « lien »",
                      variable=self.var_hand, **sw).pack(anchor="w", padx=16, pady=(16, 6))
        ctk.CTkSwitch(right, text="Garder au démarrage de Windows",
                      variable=self.var_startup, **sw).pack(anchor="w", padx=16, pady=6)

        ctk.CTkButton(right, text="Appliquer mes curseurs", height=48, corner_radius=24,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white",
                      font=ctk.CTkFont(size=16, weight="bold"),
                      command=self._apply).pack(fill="x", padx=14, pady=(18, 8))
        ctk.CTkButton(right, text="Restaurer les curseurs Windows", height=40, corner_radius=20,
                      fg_color="transparent", border_width=2, border_color=CARD_HOVER,
                      hover_color=CARD_HOVER, text_color=TEXT,
                      command=self._restore).pack(fill="x", padx=14)

        self.status = ctk.CTkLabel(right, text="", text_color=MUTED, wraplength=320,
                                   font=ctk.CTkFont(size=13))
        self.status.pack(pady=14, padx=14)

    def _section(self, text):
        ctk.CTkLabel(self.right, text=text.upper(), text_color=MUTED,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(14, 4))

    def _build_custom_editor(self):
        c = self.st["skin"]["custom"]
        f = ctk.CTkFrame(self.right, fg_color=CARD, corner_radius=14)
        self.custom_frame = f
        f.grid_columnconfigure(1, weight=1)

        def label(row, text):
            ctk.CTkLabel(f, text=text, text_color=TEXT, font=ctk.CTkFont(size=13),
                         anchor="w").grid(row=row, column=0, sticky="w", padx=(14, 8), pady=7)

        label(0, "Remplissage")
        self.menu_mode = menu(f, engine.FILL_MODES, lambda v: self._set_custom("mode", v))
        self.menu_mode.set(c["mode"])
        self.menu_mode.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=7)

        for row, (key, text) in enumerate((("c1", "Couleur 1"), ("c2", "Couleur 2"),
                                           ("outline", "Contour"), ("ring", "Liseré")), start=1):
            label(row, text)
            b = ctk.CTkButton(f, text="", width=52, height=28, corner_radius=8,
                              fg_color=c[key], hover_color=c[key], border_width=2,
                              border_color=CARD_HOVER, command=lambda k=key: self._pick_color(k))
            b.grid(row=row, column=2, padx=(0, 14), pady=7)
            self.color_btns[key] = b

        label(5, "Épaisseur contour")
        self.sl_thick = ctk.CTkSlider(f, from_=0, to=6, number_of_steps=6, progress_color=ACCENT,
                                      button_color=TEXT, command=lambda v: self._set_custom("thick", int(v)))
        self.sl_thick.set(c["thick"])
        self.sl_thick.grid(row=5, column=1, columnspan=2, sticky="ew", padx=(0, 14))
        label(6, "Épaisseur liseré")
        self.sl_ring = ctk.CTkSlider(f, from_=0, to=4, number_of_steps=4, progress_color=ACCENT,
                                     button_color=TEXT, command=lambda v: self._set_custom("ringw", int(v)))
        self.sl_ring.set(c["ringw"])
        self.sl_ring.grid(row=6, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=(0, 6))

    # ----------------------------------------------------------- logique
    def _set_skin_type(self, value):
        self.st["skin"]["type"] = "flag" if value in ("flag", SKIN_FLAG) else "custom"
        is_flag = self.st["skin"]["type"] == "flag"
        self.seg_skin.set(SKIN_FLAG if is_flag else SKIN_CUSTOM)
        if is_flag:
            self.custom_frame.pack_forget()
        else:
            self.custom_frame.pack(fill="x", padx=14, pady=(10, 0), after=self.seg_skin)
        for name, (_, btn) in self.cards.items():
            sel = is_flag and name == self.st["skin"]["flag"]
            btn.configure(border_color=ACCENT if sel else CARD)
        self._update_preview()

    def _pick_flag(self, name):
        self.st["skin"]["flag"] = name
        self._set_skin_type("flag")

    def _pick_color(self, key):
        cur = self.st["skin"]["custom"][key]
        res = colorchooser.askcolor(color=cur, parent=self, title="Choisir une couleur")
        if res and res[1]:
            self._set_custom(key, res[1])
            self.color_btns[key].configure(fg_color=res[1], hover_color=res[1])

    def _set_custom(self, key, value):
        self.st["skin"]["custom"][key] = value
        self._schedule_preview()

    def _on_shape(self, key, value):
        self.st[key] = value
        self._update_preview()

    def _on_size(self, v):
        self.st["size"] = int(v)

    def _schedule_preview(self):
        if self._preview_job:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(60, self._update_preview)

    def _update_preview(self):
        self._preview_job = None
        sk = self.st["skin"]
        for lbl, shape in ((self.prev_n, self.st["shape_normal"]), (self.prev_l, self.st["shape_link"])):
            img, _ = engine.make_cursor_image(sk, shape, 96)
            lbl.configure(image=to_ctk(img, (96, 96)))
        if sk["type"] == "flag":
            self.lbl_name.configure(text=sk["flag"])
            self.lbl_region.configure(text=engine.FLAG_BY_NAME[sk["flag"]][0])
        else:
            self.lbl_name.configure(text="Mon curseur")
            self.lbl_region.configure(text="Personnalisé")

    def _say(self, msg, ok=True):
        self.status.configure(text=msg, text_color=GOOD if ok else BAD)

    def _apply(self):
        try:
            self.st["hand"] = self.var_hand.get()
            self.st["startup"] = self.var_startup.get()
            engine.apply_state(self.st)
            engine.set_startup(self.st["startup"])
            engine.save_state(self.st)
            self._say("✓ Curseurs appliqués !")
        except Exception as e:  # noqa: BLE001
            self._say(f"Erreur : {e}", ok=False)

    def _restore(self):
        try:
            engine.restore_default()
            engine.set_startup(False)
            self.var_startup.set(False)
            self.st["startup"] = False
            engine.save_state(self.st)
            self._say("Curseurs Windows d'origine restaurés.")
        except Exception as e:  # noqa: BLE001
            self._say(f"Erreur : {e}", ok=False)


def main():
    args = sys.argv[1:]
    if "--restore" in args or "--unregister-startup" in args:
        if "--restore" in args:
            try:
                engine.restore_default()
            except Exception:  # noqa: BLE001
                pass
        try:
            engine.set_startup(False)
        except Exception:  # noqa: BLE001
            pass
        return
    if "--apply-last" in args:
        try:
            engine.apply_saved()
        except Exception:  # noqa: BLE001
            pass
        return
    App().mainloop()


if __name__ == "__main__":
    main()
