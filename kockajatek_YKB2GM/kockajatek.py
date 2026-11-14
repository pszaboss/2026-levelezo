import csv
import json
import random
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class KockaJatek:
    def __init__(self, ablak):
        self.ablak = ablak
        self.ablak.title("Dobókocka játék")
        self.ablak.geometry("920x670")
        self.ablak.minsize(790, 590)
        self.dobasok = []
        self.adatbazis = sqlite3.connect(Path(__file__).with_name("dobasok.db"))
        self.adatbazis.execute(
            "CREATE TABLE IF NOT EXISTS jatekok ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "idopont TEXT NOT NULL, "
            "eredmenyek TEXT NOT NULL)"
        )
        self.adatbazis.commit()

        stilus = ttk.Style()
        if "clam" in stilus.theme_names():
            stilus.theme_use("clam")
        stilus.configure("Cim.TLabel", font=("Segoe UI", 19, "bold"))
        stilus.configure("Ertek.TLabel", font=("Segoe UI", 15, "bold"))
        stilus.configure("Szoveg.TLabel", font=("Segoe UI", 10))
        stilus.configure("Focim.TButton", font=("Segoe UI", 11, "bold"), padding=9)
        stilus.configure("Gomb.TButton", padding=7)
        stilus.configure("TNotebook.Tab", padding=(14, 8))

        keret = ttk.Frame(ablak, padding=16)
        keret.pack(fill="both", expand=True)
        ttk.Label(keret, text="Dobókocka játék", style="Cim.TLabel").pack(anchor="w")
        ttk.Label(
            keret,
            text="Dobj egyet, vagy nézd meg, mi történik sok dobás után!",
            style="Szoveg.TLabel"
        ).pack(anchor="w", pady=(2, 12))

        self.fulek = ttk.Notebook(keret)
        self.fulek.pack(fill="both", expand=True)
        self.jatek_lap = ttk.Frame(self.fulek, padding=12)
        self.elozmeny_lap = ttk.Frame(self.fulek, padding=12)
        self.fulek.add(self.jatek_lap, text="Dobások")
        self.fulek.add(self.elozmeny_lap, text="Előzmények")

        vezerlo = ttk.Frame(self.jatek_lap)
        vezerlo.pack(fill="x", pady=(0, 12))
        ttk.Label(vezerlo, text="Dobások száma:").pack(side="left", padx=(0, 8))
        self.darabszam = tk.StringVar(value="10")
        ttk.Entry(vezerlo, textvariable=self.darabszam, width=9).pack(side="left", padx=(0, 12))
        ttk.Button(vezerlo, text="Dobjunk!", style="Focim.TButton", command=self.dobas).pack(side="left")
        ttk.Button(vezerlo, text="Új játék", style="Gomb.TButton", command=self.uj_jatek).pack(side="left", padx=9)

        osszegzes = ttk.LabelFrame(self.jatek_lap, text="Eredmény", padding=12)
        osszegzes.pack(fill="x", pady=(0, 12))
        osszegzes.columnconfigure(0, weight=1)
        osszegzes.columnconfigure(1, weight=1)
        osszegzes.columnconfigure(2, weight=1)
        osszegzes.columnconfigure(3, weight=1)

        self.kocka = ttk.Label(osszegzes, text="⚄", font=("Segoe UI Symbol", 44))
        self.kocka.grid(row=0, column=0, rowspan=2, sticky="w", padx=(10, 15))
        self.adatok = []
        for oszlop, (cim, kezdo) in enumerate([
            ("Dobások", "0"), ("Összesen", "0"), ("Átlag", "–")
        ], start=1):
            ttk.Label(osszegzes, text=cim).grid(row=0, column=oszlop, pady=(5, 2))
            szoveg = ttk.Label(osszegzes, text=kezdo, style="Ertek.TLabel")
            szoveg.grid(row=1, column=oszlop, pady=(0, 8))
            self.adatok.append(szoveg)

        reszletek = ttk.Frame(self.jatek_lap)
        reszletek.pack(fill="both", expand=True)
        reszletek.columnconfigure(0, weight=3)
        reszletek.columnconfigure(1, weight=2)
        reszletek.rowconfigure(0, weight=1)

        stat = ttk.LabelFrame(reszletek, text="Melyik szám hányszor jött ki?", padding=12)
        stat.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        stat.columnconfigure(1, weight=1)
        self.sorok = []
        for ertek in range(1, 7):
            ttk.Label(stat, text=str(ertek) + "  ", font=("Segoe UI", 11)).grid(
                row=ertek - 1, column=0, sticky="w", pady=7
            )
            csik = ttk.Progressbar(stat, maximum=100)
            csik.grid(row=ertek - 1, column=1, sticky="ew", padx=8, pady=7)
            gyakorisag = ttk.Label(stat, text="0 (0%)", width=11)
            gyakorisag.grid(row=ertek - 1, column=2, sticky="e", pady=7)
            self.sorok.append((csik, gyakorisag))

        lista_keret = ttk.LabelFrame(reszletek, text="Dobások listája", padding=8)
        lista_keret.grid(row=0, column=1, sticky="nsew")
        lista_keret.columnconfigure(0, weight=1)
        lista_keret.rowconfigure(0, weight=1)
        self.lista = tk.Listbox(lista_keret, font=("Consolas", 10), activestyle="none")
        self.lista.grid(row=0, column=0, sticky="nsew")
        gorgeto = ttk.Scrollbar(lista_keret, orient="vertical", command=self.lista.yview)
        gorgeto.grid(row=0, column=1, sticky="ns")
        self.lista.configure(yscrollcommand=gorgeto.set)

        mentesek = ttk.Frame(self.jatek_lap)
        mentesek.pack(side="bottom", fill="x", pady=(10, 0), before=reszletek)
        ttk.Button(mentesek, text="Mentés TXT", command=lambda: self.fajlba_mentes("txt")).pack(side="left", padx=(0, 7))
        ttk.Button(mentesek, text="Mentés CSV", command=lambda: self.fajlba_mentes("csv")).pack(side="left", padx=(0, 7))
        ttk.Button(mentesek, text="Mentés JSON", command=lambda: self.fajlba_mentes("json")).pack(side="left", padx=(0, 7))
        ttk.Button(mentesek, text="Mentés az előzményekbe", command=self.adatbazisba_mentes).pack(side="right")

        ttk.Label(
            self.elozmeny_lap,
            text="Itt találod a korábban elmentett dobásokat."
        ).pack(anchor="w", pady=(0, 10))
        tabla_keret = ttk.Frame(self.elozmeny_lap)
        tabla_keret.pack(fill="both", expand=True)
        oszlopok = ("id", "idopont", "darab", "osszeg", "atlag")
        self.tabla = ttk.Treeview(tabla_keret, columns=oszlopok, show="headings", selectmode="browse")
        for nev, felirat, szelesseg in [
            ("id", "Azonosító", 85), ("idopont", "Mentés ideje", 170),
            ("darab", "Dobások", 100), ("osszeg", "Összeg", 100),
            ("atlag", "Átlag", 100)
        ]:
            self.tabla.heading(nev, text=felirat)
            self.tabla.column(nev, width=szelesseg, anchor="center")
        self.tabla.pack(side="left", fill="both", expand=True)
        tabla_gorgeto = ttk.Scrollbar(tabla_keret, command=self.tabla.yview)
        tabla_gorgeto.pack(side="right", fill="y")
        self.tabla.configure(yscrollcommand=tabla_gorgeto.set)
        elozmeny_gombok = ttk.Frame(self.elozmeny_lap)
        elozmeny_gombok.pack(fill="x", pady=(12, 0))
        ttk.Button(elozmeny_gombok, text="Lista frissítése", command=self.elozmenyek_frissitese).pack(side="left", padx=(0, 8))
        ttk.Button(elozmeny_gombok, text="Kijelölt megnyitása", command=self.megnyitas).pack(side="left", padx=(0, 8))
        ttk.Button(elozmeny_gombok, text="Kijelölt törlése", command=self.torles).pack(side="left")

        self.allapot = tk.StringVar(value="Adj meg egy számot, és kezdődhet a dobás!")
        ttk.Label(keret, textvariable=self.allapot).pack(anchor="w", pady=(9, 0))
        self.elozmenyek_frissitese()
        self.ablak.protocol("WM_DELETE_WINDOW", self.bezaras)

    def dobas(self):
        try:
            darab = int(self.darabszam.get())
            if not 1 <= darab <= 10000:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Hibás adat", "1 és 10 000 közötti egész számot adj meg!")
            return
        self.dobasok = [random.randint(1, 6) for _ in range(darab)]
        self.frissites()
        self.allapot.set(f"Kész! {darab} dobás eredményét látod.")

    def frissites(self):
        db = len(self.dobasok)
        osszeg = sum(self.dobasok)
        self.adatok[0].configure(text=str(db))
        self.adatok[1].configure(text=str(osszeg))
        self.adatok[2].configure(text=f"{osszeg / db:.2f}" if db else "–")
        jelek = "⚀⚁⚂⚃⚄⚅"
        self.kocka.configure(text=jelek[self.dobasok[-1] - 1] if db else "⚄")
        for ertek, (csik, felirat) in enumerate(self.sorok, start=1):
            db_ertek = self.dobasok.count(ertek)
            szazalek = 100 * db_ertek / db if db else 0
            csik.configure(value=szazalek)
            felirat.configure(text=f"{db_ertek} ({szazalek:.0f}%)")
        self.lista.delete(0, tk.END)
        for sorszam, dobas in enumerate(self.dobasok, start=1):
            self.lista.insert(tk.END, f"{sorszam:>4}. dobás: {dobas}")

    def uj_jatek(self):
        self.dobasok = []
        self.frissites()
        self.allapot.set("Új játék indulhat!")
        self.fulek.select(self.jatek_lap)

    def van_eredmeny(self):
        if self.dobasok:
            return True
        messagebox.showinfo("Nincs eredmény", "Előbb dobj a kockával!")
        return False

    def fajlba_mentes(self, formatum):
        if not self.van_eredmeny():
            return
        utvonal = filedialog.asksaveasfilename(
            title="Dobások mentése",
            defaultextension="." + formatum,
            initialfile="dobasok." + formatum,
            filetypes=[(formatum.upper() + " fájl", "*." + formatum)]
        )
        if not utvonal:
            return
        try:
            if formatum == "txt":
                with open(utvonal, "w", encoding="utf-8") as fajl:
                    fajl.write("Dobások: " + str(len(self.dobasok)) + "\n")
                    fajl.write("Eredmények: " + ", ".join(map(str, self.dobasok)) + "\n")
                    for ertek in range(1, 7):
                        fajl.write(f"{ertek}: {self.dobasok.count(ertek)} alkalom\n")
            elif formatum == "csv":
                with open(utvonal, "w", encoding="utf-8-sig", newline="") as fajl:
                    iro = csv.writer(fajl, delimiter=";")
                    iro.writerow(["Sorszám", "Dobás"])
                    iro.writerows(enumerate(self.dobasok, start=1))
            else:
                with open(utvonal, "w", encoding="utf-8") as fajl:
                    json.dump({
                        "dobasok_szama": len(self.dobasok),
                        "eredmenyek": self.dobasok,
                        "gyakorisag": {str(i): self.dobasok.count(i) for i in range(1, 7)}
                    }, fajl, ensure_ascii=False, indent=2)
        except OSError as hiba:
            messagebox.showerror("Mentési hiba", str(hiba))
            return
        self.allapot.set("A fájl mentése sikerült.")
        messagebox.showinfo("Sikeres mentés", "A dobások mentése sikerült!")

    def adatbazisba_mentes(self):
        if not self.van_eredmeny():
            return
        self.adatbazis.execute(
            "INSERT INTO jatekok (idopont, eredmenyek) VALUES (?, ?)",
            (datetime.now().strftime("%Y.%m.%d. %H:%M"), json.dumps(self.dobasok))
        )
        self.adatbazis.commit()
        self.elozmenyek_frissitese()
        self.allapot.set("Az eredmény bekerült az előzményekbe.")
        messagebox.showinfo("Sikeres mentés", "A játékot elmentettem az előzmények közé.")

    def elozmenyek_frissitese(self):
        for elem in self.tabla.get_children():
            self.tabla.delete(elem)
        rekordok = self.adatbazis.execute(
            "SELECT id, idopont, eredmenyek FROM jatekok ORDER BY id DESC"
        ).fetchall()
        for azonosito, idopont, eredmenyek in rekordok:
            dobasok = json.loads(eredmenyek)
            darab = len(dobasok)
            atlag = f"{sum(dobasok) / darab:.2f}" if darab else "–"
            self.tabla.insert("", "end", values=(azonosito, idopont, darab, sum(dobasok), atlag))

    def kijelolt_azonosito(self):
        kijelolt = self.tabla.selection()
        if not kijelolt:
            messagebox.showinfo("Nincs kijelölés", "Válassz egy sort a listából!")
            return None
        return int(self.tabla.item(kijelolt[0], "values")[0])

    def megnyitas(self):
        azonosito = self.kijelolt_azonosito()
        if azonosito is None:
            return
        sor = self.adatbazis.execute(
            "SELECT eredmenyek FROM jatekok WHERE id = ?", (azonosito,)
        ).fetchone()
        if sor is None:
            self.elozmenyek_frissitese()
            return
        self.dobasok = json.loads(sor[0])
        self.frissites()
        self.fulek.select(self.jatek_lap)
        self.allapot.set("A korábbi eredményt megnyitottam.")

    def torles(self):
        azonosito = self.kijelolt_azonosito()
        if azonosito is None:
            return
        if not messagebox.askyesno("Törlés", "Biztosan törlöd a kijelölt eredményt?"):
            return
        self.adatbazis.execute("DELETE FROM jatekok WHERE id = ?", (azonosito,))
        self.adatbazis.commit()
        self.elozmenyek_frissitese()
        self.allapot.set("A kijelölt eredményt töröltem.")

    def bezaras(self):
        self.adatbazis.close()
        self.ablak.destroy()


if __name__ == "__main__":
    foablak = tk.Tk()
    KockaJatek(foablak)
    foablak.mainloop()
