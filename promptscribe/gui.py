# promptscribe/gui.py
import os
import json
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from promptscribe import db


# ---------- Utility ----------
def _load_metadata(include_missing=False):
    sessions = []
    DB = db.SessionLocal()
    try:
        entries = DB.query(db.SessionEntry).order_by(db.SessionEntry.start_ts.desc()).all()
        for e in entries:
            missing = not e.file or not os.path.exists(e.file)
            if missing and not include_missing:
                continue
            desc = ""
            try:
                meta_file = os.path.splitext(e.file or "")[0] + ".meta.json"
                if meta_file and os.path.exists(meta_file):
                    with open(meta_file, "r", encoding="utf-8") as mf:
                        meta = json.load(mf)
                        desc = meta.get("user_description") or meta.get("description") or ""
            except Exception:
                pass
            sessions.append({
                "id": e.id or "",
                "name": e.name or "",
                "description": desc or "",
                "file": e.file or "",
                "timestamp": e.start_ts or 0,
                "missing": missing
            })
    finally:
        DB.close()
    return sessions


def _read_text_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[Error reading file: {e}]"


# ---------- Tooltip ----------
class Tooltip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def show(self, text, x, y):
        self.hide()
        if not text:
            return
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x+20}+{y+20}")
        label = tk.Label(
            tw, text=text, justify="left",
            background="#333", foreground="white",
            relief="solid", borderwidth=1,
            font=("Segoe UI", 9)
        )
        label.pack(ipadx=6, ipady=2)

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


# ---------- Filtering ----------
def _apply_filters(sessions, filters):
    results = []
    for s in sessions:
        if filters["keyword"] and filters["keyword"].lower() not in (s["name"] + s["id"]).lower():
            continue
        if filters["filetype"] and filters["filetype"] != "All":
            ext = os.path.splitext(s["file"])[1].lower()
            if ext != filters["filetype"].lower():
                continue
        if filters["desc_kw"] and filters["desc_kw"].lower() not in s["description"].lower():
            continue
        if filters["missing"] == "Missing" and not s["missing"]:
            continue
        if filters["missing"] == "Available" and s["missing"]:
            continue
        ts = s.get("timestamp", 0)
        if filters["date_from"] and ts < filters["date_from"]:
            continue
        if filters["date_to"] and ts > filters["date_to"]:
            continue
        results.append(s)
    return results


# ---------- Main GUI ----------
def launch_gui():
    root = tk.Tk()
    root.title("PromptScribe GUI")
    root.geometry("1300x720")

    # --- Top Filter Bar ---
    top_frame = ttk.Frame(root, padding=(10, 6))
    top_frame.pack(side=tk.TOP, fill=tk.X)

    ttk.Label(top_frame, text="Keyword:").pack(side=tk.LEFT, padx=4)
    search_var = tk.StringVar()
    ttk.Entry(top_frame, textvariable=search_var, width=20).pack(side=tk.LEFT, padx=4)

    ttk.Label(top_frame, text="File Type:").pack(side=tk.LEFT, padx=4)
    filetype_combo = ttk.Combobox(top_frame, width=10, state="readonly")
    filetype_combo.pack(side=tk.LEFT, padx=4)

    ttk.Label(top_frame, text="Description:").pack(side=tk.LEFT, padx=4)
    desc_entry = ttk.Entry(top_frame, width=15)
    desc_entry.pack(side=tk.LEFT, padx=4)

    ttk.Label(top_frame, text="Status:").pack(side=tk.LEFT, padx=4)
    missing_combo = ttk.Combobox(top_frame, values=["All", "Missing", "Available"], width=10, state="readonly")
    missing_combo.set("All")
    missing_combo.pack(side=tk.LEFT, padx=4)

    ttk.Label(top_frame, text="Date From (YYYY-MM-DD):").pack(side=tk.LEFT, padx=4)
    date_from_entry = ttk.Entry(top_frame, width=12)
    date_from_entry.pack(side=tk.LEFT, padx=4)
    ttk.Label(top_frame, text="To:").pack(side=tk.LEFT, padx=2)
    date_to_entry = ttk.Entry(top_frame, width=12)
    date_to_entry.pack(side=tk.LEFT, padx=4)

    # --- Buttons ---
    btn_frame = ttk.Frame(root, padding=(8, 4))
    btn_frame.pack(side=tk.TOP, fill=tk.X)
    def spacer(): ttk.Label(btn_frame, text="  ").pack(side=tk.LEFT)
    ttk.Button(btn_frame, text="Apply Filters", command=lambda: refresh_sessions()).pack(side=tk.LEFT)
    spacer()
    ttk.Button(btn_frame, text="Open", command=lambda: open_selected()).pack(side=tk.LEFT)
    spacer()
    ttk.Button(btn_frame, text="Export CSV", command=lambda: export_csv()).pack(side=tk.LEFT)
    spacer()
    ttk.Button(btn_frame, text="Exit", command=root.destroy).pack(side=tk.RIGHT)

    # --- Main Split Layout ---
    main_pane = ttk.Panedwindow(root, orient=tk.VERTICAL)
    main_pane.pack(fill=tk.BOTH, expand=True)

    # --- Table View ---
    table_frame = ttk.Frame(main_pane, padding=6)
    columns = ("id", "name", "description", "file")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=25)

    # initial proportional widths (percentages)
    column_ratios = {"id": 0.18, "name": 0.15, "description": 0.25, "file": 0.42}

    for c in columns:
        tree.heading(c, text=c.upper())
        tree.column(c, width=int(root.winfo_width() * column_ratios[c]), anchor="w", stretch=True)
    tree.pack(fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    tooltip = Tooltip(tree)
    def on_motion(event):
        rowid = tree.identify_row(event.y)
        colid = tree.identify_column(event.x)
        if not rowid or not colid:
            tooltip.hide()
            return
        val = tree.set(rowid, colid)
        if val:
            tooltip.show(val, event.x_root, event.y_root)
        else:
            tooltip.hide()
    tree.bind("<Motion>", on_motion)
    tree.bind("<Leave>", lambda e: tooltip.hide())

    # Adjust column widths dynamically
    def resize_columns(event):
        width = event.width
        for c, ratio in column_ratios.items():
            tree.column(c, width=int(width * ratio))
    tree.bind("<Configure>", resize_columns)

    # --- Notebook (Bottom Section) ---
    notebook = ttk.Notebook(main_pane)
    main_pane.add(table_frame, weight=2)
    main_pane.add(notebook, weight=3)

    # --- Filters ---
    filters = {"keyword": "", "filetype": "", "desc_kw": "", "missing": "All", "date_from": None, "date_to": None}

    def parse_date(d):
        try:
            return datetime.strptime(d.strip(), "%Y-%m-%d").timestamp()
        except Exception:
            return None

    def get_filters():
        filters["keyword"] = search_var.get().strip()
        filters["filetype"] = filetype_combo.get().strip()
        filters["desc_kw"] = desc_entry.get().strip()
        filters["missing"] = missing_combo.get()
        filters["date_from"] = parse_date(date_from_entry.get())
        filters["date_to"] = parse_date(date_to_entry.get())
        return filters

    # ---- Actions ----
    def refresh_sessions():
        tree.delete(*tree.get_children())
        sessions = _load_metadata(include_missing=True)
        # populate file type dropdown dynamically
        exts = sorted({os.path.splitext(s["file"])[1].lower() for s in sessions if s["file"]})
        filetype_combo["values"] = ["All"] + exts
        if not filetype_combo.get():
            filetype_combo.set("All")

        active_filters = get_filters()
        sessions = _apply_filters(sessions, active_filters)
        for s in sessions:
            tag = "missing" if s["missing"] else ""
            tree.insert("", "end", values=(s["id"], s["name"], s["description"], s["file"]), tags=(tag,))
        tree.tag_configure("missing", background="#f8d7da", foreground="#721c24")

    def export_csv():
        sessions = _apply_filters(_load_metadata(include_missing=True), get_filters())
        if not sessions:
            messagebox.showinfo("No data", "No sessions found.")
            return
        export_rows = [
            {
                "ID": s["id"],
                "Name": s["name"],
                "Description": s["description"],
                "File": s["file"],
                "Timestamp": s["timestamp"],
                "Missing": "Yes" if s["missing"] else "No",
            } for s in sessions
        ]
        out_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not out_path:
            return
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(export_rows[0].keys()))
            writer.writeheader()
            writer.writerows(export_rows)
        messagebox.showinfo("Exported", f"Saved to {out_path}")

    def open_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a session first.")
            return
        sid, name, desc, path = tree.item(sel[0])["values"]
        if not path or not os.path.exists(path):
            messagebox.showerror("Missing", f"Log file not found: {path}")
            refresh_sessions()
            return
        _open_session_tab(sid, name, desc, path)

    def _open_session_tab(sid, name, desc, file_path):
        for tab_id in notebook.tabs():
            tab_widget = root.nametowidget(tab_id)
            if getattr(tab_widget, "session_id", None) == sid:
                notebook.select(tab_id)
                return
        tab = ttk.Frame(notebook)
        tab.session_id = sid
        header_frame = ttk.Frame(tab)
        header_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(header_frame, text=f"ID: {sid}    Name: {name}", anchor="w").pack(side=tk.LEFT, anchor="w")
        ttk.Button(header_frame, text="×", width=3, command=lambda: notebook.forget(tab)).pack(side=tk.RIGHT)
        ttk.Label(tab, text=f"Description: {desc}", anchor="w").pack(fill=tk.X, padx=6)

        viewer_frame = ttk.Frame(tab)
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        x_scroll = ttk.Scrollbar(viewer_frame, orient="horizontal")
        y_scroll = ttk.Scrollbar(viewer_frame, orient="vertical")
        text_area = tk.Text(
            viewer_frame,
            wrap="none",
            bg="#1e1e1e",
            fg="#cccccc",
            insertbackground="white",
            xscrollcommand=x_scroll.set,
            yscrollcommand=y_scroll.set
        )
        x_scroll.config(command=text_area.xview)
        y_scroll.config(command=text_area.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        text_area.tag_configure("cmd", foreground="#00ff66", font=("Consolas", 10, "bold"))
        text_area.tag_configure("out", foreground="#aaaaaa", font=("Consolas", 10))
        content = _read_text_file(file_path)
        for line in content.splitlines():
            tag = "cmd" if line.startswith("$") else "out"
            text_area.insert("end", line + "\n", tag)
        text_area.config(state="disabled")

        notebook.add(tab, text=(name or sid[:8]))
        notebook.select(tab)

    tree.bind("<Double-1>", lambda e: open_selected())
    root.bind("<Control-w>", lambda e: notebook.forget(notebook.select()))

    refresh_sessions()
    root.mainloop()
