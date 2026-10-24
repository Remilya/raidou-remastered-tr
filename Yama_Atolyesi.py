#!/usr/bin/env python3
"""RAIDOU Remastered Türkçe Çeviri & Yama Üretim Atölyesi (GUI)."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR / "raidou-remastered-ptbr"
SCRIPTS_DIR = REPO_DIR / "Scripts"
SPREADSHEETS_DIR = REPO_DIR / "Spreadsheets"
TEXTURES_DIR = REPO_DIR / "Content" / "Texturas"
RELEASE_DIR = BASE_DIR / "Raidou_PC_Release"
INSTALLER_EXE = RELEASE_DIR / "Raidou_TR_Kurulum.exe"


class TranslationStudioApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("RAIDOU Remastered — Türkçe Çeviri & Yama Atölyesi")
        self.geometry("760x580")
        self.minsize(760, 580)
        self.configure(bg="#14141a")
        self._build_ui()
        self.refresh_stats()

    def _build_ui(self) -> None:
        # Header
        header = tk.Frame(self, bg="#26141e", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="RAIDOU REMASTERED — ÇEVİRİ ATÖLYESİ",
            font=("Segoe UI", 16, "bold"),
            fg="#e6be5f",
            bg="#26141e",
        ).pack(anchor="w", padx=22, pady=(14, 2))

        tk.Label(
            header,
            text="CSV Metin Düzenleme • Unity AssetBundle Derleme • Hızlı Kurulum Paketi Üretimi",
            font=("Segoe UI", 9),
            fg="#c8c8d4",
            bg="#26141e",
        ).pack(anchor="w", padx=22)

        tk.Frame(self, bg="#b48c41", height=2).pack(fill=tk.X)

        # Stats Frame
        stats_frame = tk.Frame(self, bg="#1e1e28", bd=1, relief=tk.SOLID)
        stats_frame.pack(fill=tk.X, padx=22, pady=16)

        self.lbl_stats = tk.Label(
            stats_frame,
            text="İstatistikler yükleniyor...",
            font=("Segoe UI", 10, "bold"),
            fg="#f0f0f5",
            bg="#1e1e28",
            justify=tk.LEFT,
            padx=14,
            pady=12,
        )
        self.lbl_stats.pack(side=tk.LEFT)

        tk.Button(
            stats_frame,
            text="↻ Yenile",
            font=("Segoe UI", 9, "bold"),
            bg="#323242",
            fg="white",
            activebackground="#45455a",
            activeforeground="white",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.refresh_stats,
        ).pack(side=tk.RIGHT, padx=14)

        # Quick Open Section
        open_frame = tk.LabelFrame(
            self,
            text=" 1. Çeviri Dosyalarını Aç ",
            font=("Segoe UI", 10, "bold"),
            fg="#e6be5f",
            bg="#14141a",
             padx=14,
            pady=10,
        )
        open_frame.pack(fill=tk.X, padx=22, pady=(0, 12))

        btn_cfg = {
            "font": ("Segoe UI", 9, "bold"),
            "bg": "#2b2b38",
            "fg": "white",
            "activebackground": "#3d3d50",
            "activeforeground": "white",
            "relief": tk.FLAT,
            "padx": 12,
            "pady": 7,
            "cursor": "hand2",
        }

        tk.Button(
            open_frame,
            text="📄 Dialogue.csv Aç (Diyaloglar)",
            command=lambda: self._open_path(SPREADSHEETS_DIR / "Dialogue.csv"),
            **btn_cfg,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            open_frame,
            text="📄 Text.csv Aç (Arayüz / Eşya / Genel)",
            command=lambda: self._open_path(SPREADSHEETS_DIR / "Text.csv"),
            **btn_cfg,
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            open_frame,
            text="🖼️ Dokular (Texturas) Klasörünü Aç",
            command=lambda: self._open_path(TEXTURES_DIR),
            **btn_cfg,
        ).pack(side=tk.LEFT, padx=8)

        # Build & Package Section
        build_frame = tk.LabelFrame(
            self,
            text=" 2. Yamayı Derle ve Paketle ",
            font=("Segoe UI", 10, "bold"),
            fg="#e6be5f",
            bg="#14141a",
            padx=14,
            pady=12,
        )
        build_frame.pack(fill=tk.X, padx=22, pady=(0, 12))

        self.btn_import_csv = tk.Button(
            build_frame,
            text="1) Sadece CSV -> JSON Aktar",
            font=("Segoe UI", 9, "bold"),
            bg="#323244",
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=9,
            cursor="hand2",
            command=lambda: self._run_script([str(SCRIPTS_DIR / "csv_texts.py"), "import"]),
        )
        self.btn_import_csv.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_build_fast = tk.Button(
            build_frame,
            text="2) Hızlı Derle (CSV -> Bundle)",
            font=("Segoe UI", 10, "bold"),
            bg="#a52630",
            fg="white",
            relief=tk.FLAT,
            padx=14,
            pady=9,
            cursor="hand2",
            command=lambda: self._run_script([str(SCRIPTS_DIR / "build_release.py")]),
        )
        self.btn_build_fast.pack(side=tk.LEFT, padx=8)

        self.btn_build_full = tk.Button(
            build_frame,
            text="3) Tam Derle + ZIP Paketle (Metin + Doku)",
            font=("Segoe UI", 9, "bold"),
            bg="#2b5b3c",
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=9,
            cursor="hand2",
            command=lambda: self._run_script(
                [str(SCRIPTS_DIR / "build_release.py"), "--with-textures", "--zip"]
            ),
        )
        self.btn_build_full.pack(side=tk.LEFT, padx=8)

        tk.Button(
            build_frame,
            text="🚀 Kurulum Aracını Test Et",
            font=("Segoe UI", 9, "bold"),
            bg="#443850",
            fg="#ffd97d",
            relief=tk.FLAT,
            padx=12,
            pady=9,
            cursor="hand2",
            command=self._launch_installer,
        ).pack(side=tk.RIGHT)

        # Log Console
        tk.Label(
            self,
            text="İşlem Günlüğü:",
            font=("Segoe UI", 9, "bold"),
            fg="#b8b8c8",
            bg="#14141a",
        ).pack(anchor="w", padx=22)

        self.txt_log = tk.Text(
            self,
            bg="#0d0d12",
            fg="#d8e2ec",
            font=("Consolas", 9),
            relief=tk.FLAT,
            height=13,
            padx=10,
            pady=8,
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=22, pady=(4, 16))
        self.log("Yama Atölyesi hazır. CSV dosyalarında Translation sütununu doldurup 'Hızlı Derle' butonuna basabilirsiniz.")

    def log(self, text: str) -> None:
        self.txt_log.insert(tk.END, text + "\n")
        self.txt_log.see(tk.END)

    def refresh_stats(self) -> None:
        dlg_total, dlg_tr = self._count_csv(SPREADSHEETS_DIR / "Dialogue.csv")
        txt_total, txt_tr = self._count_csv(SPREADSHEETS_DIR / "Text.csv")
        tex_count = len(list(TEXTURES_DIR.glob("*.png"))) if TEXTURES_DIR.is_dir() else 0

        self.lbl_stats.config(
            text=(
                f"📊 Dialogue.csv: {dlg_total:,} satır ({dlg_tr:,} yeni çeviri girildi)   |   "
                f"Text.csv: {txt_total:,} satır ({txt_tr:,} yeni çeviri girildi)   |   "
                f"Dokular: {tex_count} PNG"
            )
        )

    @staticmethod
    def _count_csv(path: Path) -> tuple[int, int]:
        if not path.is_file():
            return 0, 0
        total = 0
        translated = 0
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                if row.get("Translation", "").strip():
                    translated += 1
        return total, translated

    def _open_path(self, path: Path) -> None:
        if not path.exists():
            messagebox.showwarning("Bulunamadı", f"Dosya veya klasör bulunamadı:\n{path}")
            return
        os.startfile(str(path))

    def _launch_installer(self) -> None:
        if not INSTALLER_EXE.is_file():
            messagebox.showwarning("Bulunamadı", f"Kurulum aracı bulunamadı:\n{INSTALLER_EXE}")
            return
        subprocess.Popen([str(INSTALLER_EXE)], cwd=str(RELEASE_DIR))

    def _run_script(self, script_args: list[str]) -> None:
        cmd = [sys.executable, *script_args]
        self.log(f"\n>>> Çalıştırılıyor: {' '.join(Path(a).name if i < 2 else a for i, a in enumerate(cmd))}")

        def worker() -> None:
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(REPO_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    self.after(0, self.log, line.rstrip())
                proc.wait()
                if proc.returncode == 0:
                    self.after(0, self.log, "✓ İşlem başarıyla tamamlandı.")
                else:
                    self.after(0, self.log, f"✗ İşlem hata kodu ile bitti: {proc.returncode}")
                self.after(0, self.refresh_stats)
            except Exception as exc:
                self.after(0, self.log, f"HATA: {exc}")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = TranslationStudioApp()
    app.mainloop()
