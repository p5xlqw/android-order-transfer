from __future__ import annotations

import json
import logging
import queue
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import tempfile
import time
import uuid
import zipfile
import ctypes
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from pathlib import PurePosixPath
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
BRIDGE = APP_DIR / "mtp_bridge.ps1"
DEBUG_LOG = Path(tempfile.gettempdir()) / "order-transfer-debug.log"
APP_ICON_PNG_BASE64 = "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"
logging.basicConfig(
    filename=str(DEBUG_LOG), level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8",
)
logger = logging.getLogger("order_transfer")
BASE_SORT_OPTIONS = ("名前", "拡張子", "ファイルサイズ", "更新日時", "作成日時", "アクセス日時")
METADATA_SORT_TYPES = {
    "トラック番号": "number", "ディスク番号": "number", "タイトル": "text",
    "アルバム": "text", "アーティスト": "text", "ジャンル": "text",
    "作曲者": "text", "年": "number", "再生時間": "number",
    "ビットレート": "number", "総ビットレート": "number", "サンプルレート": "number",
    "音声チャンネル数": "number", "音声形式": "text", "可変ビットレート": "text",
    "音声ビット深度": "number",
    "撮影日時": "date", "カメラ": "text", "カメラメーカー": "text",
    "レンズ": "text", "ISO感度": "number", "F値": "number",
    "露出時間": "number", "焦点距離": "number", "フラッシュ": "text",
    "測光モード": "text", "向き": "text", "画像サイズ": "text",
    "画像の幅": "number", "画像の高さ": "number", "ページ数": "number",
    "動画の幅": "number", "動画の高さ": "number", "フレームレート": "number",
    "動画形式": "text", "FourCC": "text", "映像ビットレート": "number",
    "動画の横比": "number", "動画の縦比": "number",
    "画像のビット深度": "number", "画像の横解像度": "number", "画像の縦解像度": "number",
    "画像形式": "text",
    "立体視": "text",
    "監督": "text", "作成者": "text", "件名": "text", "タグ": "text",
    "コメント": "text", "単語数": "number", "文字数": "number",
    "段落数": "number", "行数": "number", "スライド数": "number",
    "改訂番号": "number", "プレゼンテーション形式": "text",
}


def _count_present_wpd_interfaces() -> int | None:
    """Count connected Windows Portable Device (including MTP) interfaces."""
    if sys.platform != "win32":
        return None

    class GUID(ctypes.Structure):
        _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                    ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]

    class DeviceInterfaceData(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("InterfaceClassGuid", GUID),
                    ("Flags", wintypes.DWORD), ("Reserved", ctypes.c_size_t)]

    wpd_guid = GUID(0x6AC27878, 0xA6FA, 0x4155,
                    (ctypes.c_ubyte * 8)(0xBA, 0x85, 0xF9, 0x8F, 0x49, 0x1D, 0x4F, 0x33))
    setupapi = ctypes.WinDLL("setupapi", use_last_error=True)
    get_class_devs = setupapi.SetupDiGetClassDevsW
    get_class_devs.argtypes = [ctypes.POINTER(GUID), wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD]
    get_class_devs.restype = ctypes.c_void_p
    enum_interfaces = setupapi.SetupDiEnumDeviceInterfaces
    enum_interfaces.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(GUID),
                                wintypes.DWORD, ctypes.POINTER(DeviceInterfaceData)]
    enum_interfaces.restype = wintypes.BOOL
    destroy_list = setupapi.SetupDiDestroyDeviceInfoList
    destroy_list.argtypes = [ctypes.c_void_p]
    destroy_list.restype = wintypes.BOOL

    info_set = get_class_devs(ctypes.byref(wpd_guid), None, None, 0x2 | 0x10)  # PRESENT | DEVICEINTERFACE
    if info_set == ctypes.c_void_p(-1).value:
        return None
    try:
        count = 0
        index = 0
        while True:
            data = DeviceInterfaceData()
            data.cbSize = ctypes.sizeof(DeviceInterfaceData)
            if enum_interfaces(info_set, None, ctypes.byref(wpd_guid), index, ctypes.byref(data)):
                count += 1
                index += 1
                continue
            if ctypes.get_last_error() == 259:  # ERROR_NO_MORE_ITEMS
                return count
            return None
    finally:
        destroy_list(info_set)


class MtpOrderTransfer:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("順番転送ツール")
        try:
            self.app_icon_image = tk.PhotoImage(data=APP_ICON_PNG_BASE64)
            self.root.iconphoto(True, self.app_icon_image)
        except tk.TclError:
            self.app_icon_image = None
        self.root.geometry("900x830")
        self.root.minsize(900, 830)
        self.root.maxsize(900, 830)
        self.events: queue.Queue[dict] = queue.Queue()
        self.bridge_errors: list[str] = []
        self.process: subprocess.Popen[str] | None = None
        self.bridge_available = False
        self.bridge_requests: list[tuple[tuple[str, str], float, float | None]] = []
        self.source_files: list[Path] = []
        self.all_source_files: list[Path] = []
        self.relative_paths: dict[str, str] = {}
        self.archive_temp: Path | None = None
        self.zip_loading = False
        self.zip_request_id = 0
        self.zip_cancel_event: threading.Event | None = None
        self.lifecycle_lock = threading.Lock()
        self.closing = False
        self.close_after_cancel = False
        self.folders: list[dict] = []
        self.loaded_folder_ids: set[int] = set()
        self.requested_folder_ids: set[int] = set()
        self.busy = False
        self.cancel_file: Path | None = None
        self.transfer_total = 0
        self.transfer_processed = 0
        self.transfer_bytes_total = 0
        self.transfer_bytes_done = 0
        self.transfer_started_at: float | None = None
        self.transfer_last_event_at: float | None = None
        # Heartbeats arrive every 5 seconds; this is only the fallback if
        # Windows does not deliver a WPD removal notification.
        self.transfer_stall_timeout = 12.0
        self.transfer_active_index = 0
        self.bridge_unresponsive_handled = False
        self.device_disconnect_handled = False
        self.device_monitor_stop = threading.Event()
        self.device_removed_event = threading.Event()
        self.device_monitor_thread: threading.Thread | None = None
        self.device_monitor_baseline: int | None = None
        self.pending_transfer: dict | None = None
        self.transfer_results: list[dict[str, str]] = []
        self.metadata_by_path: dict[str, dict[str, str]] = {}
        self.metadata_request_id = 0
        self.metadata_loading = False
        self.dragged_preview_row: str | None = None
        self.dragged_preview_path: Path | None = None
        self.drop_insert_index: int | None = None
        self.drag_overlay: tk.Toplevel | None = None
        self.drop_marker: tk.Toplevel | None = None
        self.last_moved_path: Path | None = None
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(150, self._poll_events)
        self.root.after(1000, self._tick_metrics)
        self._start_bridge()

    def _start_device_disconnect_monitor(self) -> None:
        """Poll present WPD interfaces so unplug detection never hooks Tk's WndProc."""
        if sys.platform != "win32":
            return
        baseline = _count_present_wpd_interfaces()
        if baseline is None or baseline == 0:
            logger.warning("mtp_presence_monitor_unavailable baseline=%s", baseline)
            return
        self.device_monitor_baseline = baseline
        self.device_removed_event.clear()
        self.device_monitor_stop.clear()
        self.device_monitor_thread = threading.Thread(
            target=self._watch_device_presence, args=(baseline,), daemon=True,
            name="mtp-device-presence",
        )
        self.device_monitor_thread.start()
        logger.info("mtp_presence_monitor_started interfaces=%s", baseline)

    def _watch_device_presence(self, baseline: int) -> None:
        while not self.device_monitor_stop.wait(0.3):
            present = _count_present_wpd_interfaces()
            if present is not None and present < baseline:
                logger.error("mtp_presence_lost before=%s after=%s", baseline, present)
                self.device_removed_event.set()
                return

    def _handle_device_removed(self) -> None:
        """Abort the ordered batch as soon as Windows reports MTP removal."""
        if (not self.busy or self.transfer_started_at is None
                or self.device_disconnect_handled or self.closing):
            return
        self.device_disconnect_handled = True
        logger.error("mtp_device_removed_during_transfer index=%s processed=%s total=%s",
                     self.transfer_active_index, self.transfer_processed, self.transfer_total)
        self._stop_transfer_after_disconnect("USB接続が切断されたため、転送全体を中止しました。")

    def _stop_transfer_after_disconnect(self, message: str) -> None:
        self.device_monitor_stop.set()
        self.bridge_unresponsive_handled = True
        self.bridge_available = False
        self.bridge_requests.clear()
        if self.cancel_file:
            try:
                self.cancel_file.write_text("disconnect", encoding="ascii")
            except OSError:
                pass
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
            except OSError:
                pass
        self.pending_transfer = None
        self._set_busy(False)
        self._remove_cancel_file()
        self.folders = []
        self.loaded_folder_ids.clear()
        self.requested_folder_ids.clear()
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
        self.selected_destination.set("未選択（転送機能の再起動が必要）")
        self.transfer_button.config(state="disabled")
        self.refresh_button.config(state="disabled")
        self.source_button.config(state="disabled")
        self.zip_button.config(state="disabled")
        self.transfer_last_event_at = None
        for index, result in enumerate(self.transfer_results, start=1):
            if index == self.transfer_active_index:
                result["status"] = "失敗（完了未確認）"
            elif result.get("status") in {"完了", "スキップ"}:
                result["status"] = "やり直し"
            elif result.get("status") in {"待機", "転送中"}:
                result["status"] = "未実行"
        self.connection_label.config(text="端末の切断を検知しました。アプリを再起動してください。")
        self.status.config(text=f"{message} アプリを終了します。")
        self.progress_text.config(text=f"転送中断・要やり直し {self.transfer_processed}/{self.transfer_total}件")
        # The MTP session cannot be reused after unplug. Briefly show the
        # stopped state, then close the unusable window without another prompt.
        self.root.after(1800, self._finish_close)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        source_box = ttk.LabelFrame(outer, text="1. 送信元（PCフォルダ／ZIP）", padding=10)
        source_box.pack(fill="x")
        self.source_label = ttk.Label(source_box, text="送信元が選択されていません", anchor="w")
        self.source_label.pack(side="left", fill="x", expand=True)
        self.source_button = ttk.Button(source_box, text="フォルダを選択…", command=self._choose_source_folder)
        self.zip_button = ttk.Button(source_box, text="ZIP／CBZを選択…", command=self._choose_source_zip)
        self.zip_button.pack(side="right", padx=(0, 6))
        self.source_button.pack(side="right")

        sort_row = ttk.Frame(outer, padding=(0, 8, 0, 8))
        sort_row.pack(fill="x")
        ttk.Label(sort_row, text="並び順:").pack(side="left")
        self.sort_by = tk.StringVar(value="名前")
        self.sort_combo = ttk.Combobox(sort_row, textvariable=self.sort_by, values=BASE_SORT_OPTIONS,
                                       state="readonly", width=12)
        self.sort_combo.pack(side="left", padx=(6, 12))
        self.sort_combo.bind("<<ComboboxSelected>>", self._on_sort_selected)
        self.direction = tk.StringVar(value="昇順")
        self.direction_combo = ttk.Combobox(sort_row, textvariable=self.direction, values=("昇順", "降順"),
                                            state="readonly", width=8)
        self.direction_combo.pack(side="left")
        self.direction_combo.bind("<<ComboboxSelected>>", lambda _event: self._update_preview())
        ttk.Label(sort_row, text="  ※転送前に一覧で順番を確認できます").pack(side="left")
        self.skip_existing = tk.BooleanVar(value=False)
        self.skip_box = ttk.Checkbutton(sort_row, text="同名ファイルをスキップ", variable=self.skip_existing)
        self.skip_box.pack(side="right")
        filter_row = ttk.Frame(outer)
        filter_row.pack(fill="x", pady=(0, 6))
        ttk.Label(filter_row, text="拡張子:").pack(side="left")
        self.extension_filter = tk.StringVar(value="すべて")
        self.extension_combo = ttk.Combobox(filter_row, textvariable=self.extension_filter,
                                            values=("すべて",), state="readonly", width=14)
        self.extension_combo.pack(side="left", padx=(6, 8))
        self.extension_combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_extension_filter())
        ttk.Label(filter_row, text="プレビューの行をドラッグすると順番を変更できます").pack(side="left")

        dest_box = ttk.LabelFrame(outer, text="2. USB接続したAndroidの転送先フォルダ", padding=10)
        dest_box.pack(fill="both", expand=True)
        device_bar = ttk.Frame(dest_box)
        device_bar.pack(fill="x", pady=(0, 8))
        self.connection_label = ttk.Label(device_bar, text="端末を検索しています…")
        self.connection_label.pack(side="left", fill="x", expand=True)
        self.refresh_button = ttk.Button(device_bar, text="再検索", command=self._refresh)
        self.refresh_button.pack(side="right")
        tree_frame = ttk.Frame(dest_box)
        tree_frame.pack(fill="both", expand=True)
        self.folder_tree = ttk.Treeview(tree_frame, columns=("id",), displaycolumns=(), show="tree", height=9)
        self.folder_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.folder_tree.yview)
        scroll.pack(side="right", fill="y")
        self.folder_tree.configure(yscrollcommand=scroll.set)
        self.folder_tree.bind("<<TreeviewSelect>>", self._on_folder_select)
        self.folder_tree.bind("<<TreeviewOpen>>", self._on_folder_open)
        self.selected_destination = tk.StringVar(value="未選択（フォルダを1回クリック）")
        ttk.Label(dest_box, textvariable=self.selected_destination, anchor="w", foreground="#1f4e79").pack(fill="x", pady=(8, 0))
        destination_mode = ttk.Frame(dest_box)
        destination_mode.pack(fill="x", pady=(6, 0))
        self.destination_mode = tk.StringVar(value="existing")
        self.existing_mode_radio = ttk.Radiobutton(destination_mode, text="選択したフォルダへ転送",
                                                   variable=self.destination_mode, value="existing",
                                                   command=self._on_destination_mode)
        self.existing_mode_radio.pack(side="left")
        self.new_mode_radio = ttk.Radiobutton(destination_mode, text="新しいフォルダを作成して転送",
                                              variable=self.destination_mode, value="new",
                                              command=self._on_destination_mode)
        self.new_mode_radio.pack(side="left", padx=(12, 6))
        self.new_folder_name = tk.StringVar()
        self.new_folder_name.trace_add("write", lambda *_args: self._refresh_transfer_button())
        self.new_folder_entry = ttk.Entry(destination_mode, textvariable=self.new_folder_name, width=28, state="disabled")
        self.new_folder_entry.pack(side="left", fill="x", expand=True)

        preview_box = ttk.LabelFrame(outer, text="3. 転送順プレビュー", padding=8)
        preview_box.pack(fill="both", expand=True, pady=(10, 0))
        preview_frame = ttk.Frame(preview_box)
        preview_frame.pack(fill="both", expand=True)
        self.preview = ttk.Treeview(preview_frame, columns=("order", "name", "size"), show="headings", height=10)
        self.preview.heading("order", text="順番")
        self.preview.heading("name", text="ファイル名")
        self.preview.heading("size", text="サイズ")
        self.preview.column("order", width=58, anchor="center", stretch=False)
        self.preview.column("name", width=540, anchor="w")
        self.preview.column("size", width=100, anchor="e", stretch=False)
        self.preview.pack(side="left", fill="both", expand=True)
        pscroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview.yview)
        pscroll.pack(side="right", fill="y")
        self.preview.configure(yscrollcommand=pscroll.set)
        self.preview.bind("<ButtonPress-1>", self._preview_drag_start, add="+")
        self.preview.bind("<B1-Motion>", self._preview_drag_motion, add="+")
        self.preview.bind("<ButtonRelease-1>", self._preview_drag_end, add="+")

        self.reverse_transfer = tk.BooleanVar(value=False)
        self.reverse_transfer_box = ttk.Checkbutton(outer, text="下から転送", variable=self.reverse_transfer)
        self.reverse_transfer_box.pack(anchor="w", pady=(5, 0))

        bottom = ttk.Frame(outer, padding=(0, 10, 0, 0))
        bottom.pack(fill="x")
        self.status = ttk.Label(bottom, text="USB接続後、端末側でファイル転送を許可してください。")
        self.status.pack(fill="x")
        progress_row = ttk.Frame(bottom)
        progress_row.pack(fill="x", pady=(5, 0))
        self.metrics_text = ttk.Label(progress_row, text="経過 --:-- | 平均速度 -- | 残り目安 --", width=46, anchor="w")
        self.metrics_text.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.transfer_button = ttk.Button(progress_row, text="順番に転送", command=self._transfer, state="disabled", width=12)
        self.transfer_button.grid(row=0, column=1, sticky="ew")
        self.cancel_button = ttk.Button(progress_row, text="中止", command=self._cancel_transfer, state="disabled", width=9)
        self.cancel_button.grid(row=0, column=2, sticky="ew", padx=(8, 8))
        self.progress_bar = ttk.Progressbar(progress_row, mode="determinate", maximum=100, length=150)
        self.progress_bar.grid(row=0, column=3, sticky="ew")
        self.progress_text = ttk.Label(progress_row, text="0%", width=34, anchor="e")
        self.progress_text.grid(row=0, column=4, sticky="e", padx=(8, 0))
        progress_row.columnconfigure(0, weight=1)
        progress_row.columnconfigure(1, minsize=104)
        progress_row.columnconfigure(2, minsize=88)
        progress_row.columnconfigure(3, minsize=150, weight=0)
        progress_row.columnconfigure(4, minsize=220)

    def _start_bridge(self) -> None:
        logger.info("app_start app_dir=%s", APP_DIR)
        if not BRIDGE.exists():
            self.connection_label.config(text="転送機能の構成ファイルが見つかりません")
            self.refresh_button.config(state="disabled")
            self.source_button.config(state="disabled")
            self.zip_button.config(state="disabled")
            return
        try:
            self.process = subprocess.Popen(
                ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(BRIDGE)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", bufsize=1, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.bridge_available = True
            logger.info("bridge_started pid=%s bridge=%s", self.process.pid, BRIDGE)
        except OSError as exc:
            logger.exception("bridge_start_failed")
            self.connection_label.config(text=f"転送機能を起動できません: {exc}")
            self.refresh_button.config(state="disabled")
            self.source_button.config(state="disabled")
            self.zip_button.config(state="disabled")
            return
        self.refresh_button.config(state="disabled")
        self.bridge_requests.append((("scan", ""), 90.0, time.monotonic()))
        threading.Thread(target=self._read_bridge, daemon=True).start()
        threading.Thread(target=self._read_bridge_errors, daemon=True).start()

    def _read_bridge(self) -> None:
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            try:
                event = json.loads(line)
                if event.get("type") in {"progress", "phase", "file_done", "skipped", "cancel_wait", "transfer_done", "error"}:
                    logger.info("bridge_event %s", event)
                self.events.put(event)
            except json.JSONDecodeError:
                logger.warning("bridge_invalid_json %r", line[:1000])
                continue
        return_code = self.process.wait()
        logger.warning("bridge_ended return_code=%s stderr=%s", return_code, self.bridge_errors[-10:])
        self.events.put({"type": "ended", "returnCode": return_code})

    def _read_bridge_errors(self) -> None:
        assert self.process and self.process.stderr
        for line in self.process.stderr:
            self.bridge_errors.append(line.rstrip())
            logger.error("bridge_stderr %s", line.rstrip())

    def _send(self, data: dict) -> bool:
        if not self.process or not self.process.stdin or self.process.poll() is not None:
            messagebox.showerror("転送機能", "転送機能との接続が切れました。アプリを再起動してください。")
            return False
        try:
            self.process.stdin.write(json.dumps(data, ensure_ascii=False) + "\n")
            self.process.stdin.flush()
            action = data.get("action")
            request_key: tuple[str, str] | None = None
            timeout = 0.0
            if action == "scan":
                request_key, timeout = ("scan", ""), 90.0
            elif action == "children":
                request_key, timeout = ("children", str(data.get("id", ""))), 90.0
            elif action == "source_metadata":
                request_key, timeout = ("source_metadata", str(data.get("requestId", ""))), 180.0
            elif action == "preflight":
                request_key, timeout = ("preflight", ""), 120.0
            if request_key:
                started = time.monotonic() if not self.bridge_requests else None
                self.bridge_requests.append((request_key, timeout, started))
            return True
        except (OSError, BrokenPipeError, ValueError) as exc:
            self.status.config(text=f"転送機能への要求に失敗しました: {exc}")
            return False

    def _poll_events(self) -> None:
        if self.device_removed_event.is_set():
            self.device_removed_event.clear()
            self._handle_device_removed()
        while not self.closing:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            kind = event.get("type")
            if self.device_disconnect_handled and kind in {
                "progress", "phase", "file_progress", "file_done", "skipped",
                "cancel_wait", "heartbeat", "transfer_done",
            }:
                continue
            response_key = {
                "tree": ("scan", ""), "scan_error": ("scan", ""),
                "children": ("children", str(event.get("parentId", ""))),
                "children_error": ("children", str(event.get("parentId", ""))),
                "source_metadata": ("source_metadata", str(event.get("requestId", ""))),
                "preflight_done": ("preflight", ""),
            }.get(kind)
            if response_key:
                for request_index, (queued_key, _timeout, _started) in enumerate(self.bridge_requests):
                    if queued_key == response_key:
                        was_first = request_index == 0
                        del self.bridge_requests[request_index]
                        if was_first and self.bridge_requests:
                            next_key, next_timeout, _ = self.bridge_requests[0]
                            self.bridge_requests[0] = (next_key, next_timeout, time.monotonic())
                        break
            if self.busy and kind in {"progress", "phase", "file_progress", "file_done", "skipped", "cancel_wait", "heartbeat"}:
                self.transfer_last_event_at = time.monotonic()
            if kind == "tree":
                self.refresh_button.config(state="normal")
                self._show_folders(event.get("folders", []))
            elif kind == "children":
                self._show_children(int(event["parentId"]), event.get("folders", []))
            elif kind == "children_error":
                parent_id = int(event["parentId"])
                self.requested_folder_ids.discard(parent_id)
                placeholder = f"loading_{parent_id}"
                if self.folder_tree.exists(placeholder):
                    self.folder_tree.item(placeholder, text="読み込み失敗（再検索してください）")
                self.status.config(text=f"フォルダを読み込めませんでした: {event.get('message', '')}")
            elif kind == "scan_error":
                self.refresh_button.config(state="normal")
                self._show_folders([])
                self.connection_label.config(text="端末を確認できません。USB接続とファイル転送モードを確認してください。")
                self.status.config(text=event.get("message", "端末を検索できませんでした。"))
            elif kind == "preflight_done":
                if self.close_after_cancel:
                    self.pending_transfer = None
                    self._finish_close()
                else:
                    self._finish_preflight(event)
            elif kind == "source_metadata":
                self._finish_source_metadata(event)
            elif kind == "zip_ready":
                self._finish_zip_load(event)
            elif kind == "zip_progress":
                self.status.config(text=f"ZIPを展開中 {event['index']}/{event['total']}: {event['name']}")
            elif kind == "progress":
                self.transfer_total = int(event.get("total", 0))
                self.transfer_active_index = int(event.get("index", 0))
                self._set_transfer_result(event.get("index"), "転送中")
                self.status.config(text=f"転送中 {event['index']}/{event['total']}: {event['name']}（端末側で完了確認中）")
                self._update_progress()
            elif kind == "phase":
                phase_message = event.get("message", "転送中…")
                if str(phase_message).startswith("端末へ転送を依頼中:"):
                    # CopyHere should return promptly. If it blocks on a missing
                    # device, don't leave cancel/close waiting for a file-sized timeout.
                    self.transfer_stall_timeout = 12.0
                else:
                    self.transfer_stall_timeout = 12.0
                self.status.config(text=phase_message)
            elif kind == "file_done":
                self.transfer_processed += 1
                self._set_transfer_result(event.get("index"), "完了")
                self.status.config(text=f"転送完了 {self.transfer_processed}/{self.transfer_total}: {event.get('name', '')}")
                self._update_progress(event.get("bytesDone"), event.get("bytesTotal"))
            elif kind == "file_progress":
                self.transfer_active_index = int(event.get("index", self.transfer_active_index))
                current = int(event.get("currentBytes", 0))
                total = int(event.get("currentTotal", 0))
                amount = f" ({self._format_size(current)} / {self._format_size(total)})" if total > 0 else ""
                self.status.config(text=f"転送中 {event.get('index', 0)}/{event.get('total', 0)}: {event.get('name', '')}（完了確認済み {self.transfer_processed} 件{amount}）")
                self._update_progress(event.get("bytesDone"), event.get("bytesTotal"))
            elif kind == "skipped":
                self.transfer_processed += 1
                self._set_transfer_result(event.get("index"), "スキップ")
                self.status.config(text=f"既存ファイルをスキップ {self.transfer_processed}/{self.transfer_total}: {event.get('name', '')}")
                self._update_progress(event.get("bytesDone"), event.get("bytesTotal"))
            elif kind == "cancel_wait":
                self.status.config(text=f"中止要求を受け付けました。現在のファイルを確認中: {event.get('name', '')}")
            elif kind == "heartbeat":
                pass
            elif kind == "transfer_done":
                self._set_busy(False)
                self._remove_cancel_file()
                if event.get("ok"):
                    sent = event.get("completed", event["total"])
                    skipped = event.get("skipped", 0)
                    self.status.config(text=f"転送完了: {sent} 個送信、{skipped} 個スキップ")
                    self.progress_bar.configure(value=100)
                    self._update_progress(self.transfer_bytes_total, self.transfer_bytes_total)
                    self._refresh_metrics()
                    self._show_transfer_results(f"転送完了: {sent} 個送信、{skipped} 個スキップ")
                elif event.get("cancelled"):
                    self.status.config(text=f"中止しました ({event.get('completed', 0)} 個完了)")
                    self._show_transfer_results("転送を中止しました", event.get("message", "次のファイルは転送していません。"))
                else:
                    self.status.config(text=f"転送を停止しました ({event.get('completed', 0)} 個完了)")
                    self._mark_batch_for_rerun(event.get("failedIndex"))
                    # MTP COM folder handles can be stale after a failed copy,
                    # particularly when USB is removed. Retire this bridge so
                    # later actions cannot continue against that session.
                    self.bridge_unresponsive_handled = True
                    self.bridge_available = False
                    self.bridge_requests.clear()
                    if self.process and self.process.poll() is None:
                        try:
                            self.process.kill()
                        except OSError:
                            pass
                    self.folders = []
                    self.loaded_folder_ids.clear()
                    self.requested_folder_ids.clear()
                    for item in self.folder_tree.get_children():
                        self.folder_tree.delete(item)
                    self.selected_destination.set("未選択（転送機能の再起動が必要）")
                    self.refresh_button.config(state="disabled")
                    self.transfer_button.config(state="disabled")
                    self.source_button.config(state="disabled")
                    self.zip_button.config(state="disabled")
                    self.connection_label.config(text="転送エラーにより接続を停止しました。アプリを再起動してください。")
                    detail = event.get("message", "転送中にエラーが発生しました。")
                    detail += "\n順番を保つため途中からは再開しません。端末を確認し、空の新しいフォルダへ最初から転送してください。"
                    self._show_transfer_results("転送全体を停止しました", detail)
                if self.close_after_cancel:
                    self._finish_close()
            elif kind == "ended":
                if self.bridge_unresponsive_handled:
                    self.bridge_unresponsive_handled = False
                    continue
                self.bridge_available = False
                self.bridge_requests.clear()
                detail = " ".join(self.bridge_errors[-3:])
                self.connection_label.config(text="転送機能が終了しました。再起動してください。")
                self.folders = []
                self.loaded_folder_ids.clear()
                self.requested_folder_ids.clear()
                for item in self.folder_tree.get_children():
                    self.folder_tree.delete(item)
                self.selected_destination.set("未選択（転送機能の再起動が必要）")
                self.refresh_button.config(state="disabled")
                self.transfer_button.config(state="disabled")
                self.source_button.config(state="disabled")
                self.zip_button.config(state="disabled")
                if self.busy:
                    was_transferring = self.transfer_started_at is not None
                    self.pending_transfer = None
                    self._set_busy(False)
                    self._remove_cancel_file()
                    if was_transferring:
                        for index, result in enumerate(self.transfer_results, start=1):
                            if index == self.transfer_active_index:
                                result["status"] = "失敗（完了未確認）"
                            elif result.get("status") in {"待機", "転送中"}:
                                result["status"] = "未実行"
                        self.status.config(text="転送機能が途中で終了しました。端末側の状態を確認してください。")
                        self._show_transfer_results("転送機能が途中で終了しました",
                                                    detail or "端末側で転送済みのファイルがないか確認してください。")
                    else:
                        self.status.config(text="転送前確認中に転送機能が終了しました。転送は開始されていません。アプリを再起動してください。")
                else:
                    self.status.config(text="転送機能が停止しました。アプリを再起動してください。")
                self.refresh_button.config(state="disabled")
                self.transfer_button.config(state="disabled")
                self.source_button.config(state="disabled")
                self.zip_button.config(state="disabled")
                if self.close_after_cancel:
                    self._finish_close()
                elif event.get("returnCode") and detail:
                    self.status.config(text=f"終了コード {event['returnCode']}: {detail}")
            elif kind == "error":
                self.status.config(text=event.get("message", "エラーが発生しました。"))
        if not self.closing:
            if self.bridge_requests:
                key, timeout, started = self.bridge_requests[0]
                if started is not None and time.monotonic() - started > timeout:
                    self._handle_bridge_timeout(key)
        if (self.busy and self.transfer_last_event_at is not None
                and time.monotonic() - self.transfer_last_event_at > self.transfer_stall_timeout):
            self._handle_unresponsive_transfer()
        if not self.closing:
            self.root.after(150, self._poll_events)

    def _handle_unresponsive_transfer(self) -> None:
        """Fail the whole ordered batch when the MTP bridge stops responding."""
        if not self.busy:
            return
        logger.error("transfer_watchdog_timeout index=%s processed=%s total=%s", self.transfer_active_index, self.transfer_processed, self.transfer_total)
        self._stop_transfer_after_disconnect(
            "端末から応答がなくなったため、転送全体を中止しました。"
        )

    def _handle_bridge_timeout(self, request_key: tuple[str, str]) -> None:
        """Unstick folder/metadata/preflight requests that stop returning from MTP."""
        if not self.bridge_available:
            return
        action = request_key[0]
        self.bridge_unresponsive_handled = True
        self.bridge_available = False
        self.bridge_requests.clear()
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
            except OSError:
                pass
        self.folders = []
        self.loaded_folder_ids.clear()
        self.requested_folder_ids.clear()
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
        self.selected_destination.set("未選択（転送機能の再起動が必要）")
        self.refresh_button.config(state="disabled")
        self.transfer_button.config(state="disabled")
        self.source_button.config(state="disabled")
        self.zip_button.config(state="disabled")
        if action == "source_metadata":
            self.metadata_loading = False
        if self.busy and self.transfer_started_at is None:
            self.pending_transfer = None
            self._set_busy(False)
        self.refresh_button.config(state="disabled")
        self.transfer_button.config(state="disabled")
        self.source_button.config(state="disabled")
        self.zip_button.config(state="disabled")
        self.connection_label.config(text="端末の応答がありません。アプリを再起動してください。")
        labels = {"scan": "端末の検索", "children": "フォルダの読み込み",
                  "source_metadata": "メタデータの確認", "preflight": "転送前確認"}
        self.status.config(text=f"{labels.get(action, '端末の処理')}が応答しないため停止しました。アプリを再起動してください。")
        if self.close_after_cancel:
            self._finish_close()

    def _set_transfer_result(self, index: object, status: str) -> None:
        try:
            result_index = int(index) - 1
        except (TypeError, ValueError):
            return
        if 0 <= result_index < len(self.transfer_results):
            self.transfer_results[result_index]["status"] = status

    def _mark_batch_for_rerun(self, failed_index: object = None) -> None:
        try:
            failed = int(failed_index)
        except (TypeError, ValueError):
            failed = self.transfer_active_index
        for index, result in enumerate(self.transfer_results, start=1):
            if failed > 0 and index == failed:
                result["status"] = "失敗（完了未確認）"
            elif result.get("status") in {"完了", "スキップ"}:
                result["status"] = "やり直し"
            elif result.get("status") in {"待機", "転送中"}:
                result["status"] = "未実行"

    def _show_transfer_results(self, summary: str, detail: str = "") -> None:
        if not self.transfer_results:
            return
        for result in self.transfer_results:
            if result["status"] in ("待機", "転送中"):
                result["status"] = "未実行"

        window = tk.Toplevel(self.root)
        window.title("転送結果")
        window.geometry("680x500")
        window.transient(self.root)
        frame = ttk.Frame(window, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=summary, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        if detail:
            ttk.Label(frame, text=detail, wraplength=640, justify="left").pack(anchor="w", pady=(6, 10))
        else:
            ttk.Label(frame, text="一覧は転送順です。",).pack(anchor="w", pady=(4, 10))

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill="both", expand=True)
        table = ttk.Treeview(table_frame, columns=("order", "status", "name", "size"),
                             show="headings", height=18)
        table.heading("order", text="順")
        table.heading("status", text="結果")
        table.heading("name", text="ファイル名")
        table.heading("size", text="サイズ")
        table.column("order", width=48, anchor="e")
        table.column("status", width=100, anchor="center")
        table.column("name", width=400, anchor="w")
        table.column("size", width=90, anchor="e")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for index, result in enumerate(self.transfer_results, 1):
            table.insert("", "end", values=(index, result["status"], result["name"], result["size"]))
        ttk.Button(frame, text="閉じる", command=window.destroy).pack(anchor="e", pady=(10, 0))

    def _show_folders(self, folders: list[dict]) -> None:
        self.folders = folders
        self.loaded_folder_ids.clear()
        self.requested_folder_ids.clear()
        self.folder_tree.delete(*self.folder_tree.get_children())
        self.selected_destination.set("未選択（フォルダを1回クリック）")
        for folder in folders:
            label = folder.get("name", "")
            iid = str(folder["id"])
            self.folder_tree.insert("", "end", iid=iid, text=label, open=False)
            self.folder_tree.insert(iid, "end", iid=f"loading_{iid}", text="フォルダを開くと中身を表示")
        devices = sorted({f.get("device", "") for f in folders if f.get("device")})
        self.connection_label.config(text=("接続先: " + "、".join(devices)) if devices else "端末が見つかりません。USB転送モードを確認してください。")
        if folders:
            self.status.config(text="端末を表示しました。矢印で開いて転送先フォルダを選択してください。")
        else:
            self.status.config(text="端末が見つかりません。USB接続とファイル転送モードを確認してください。")
        self._refresh_transfer_button()

    def _on_folder_select(self, _event: tk.Event) -> None:
        selected = self.folder_tree.selection()
        row = next((folder for folder in self.folders if selected and str(folder["id"]) == selected[0]), None)
        if row and not row.get("isDevice"):
            device = row.get("device", "")
            path = row.get("path", "")
            relative_path = path[len(device):].lstrip("\\/") if path.startswith(device) else path
            shown_path = f"{device} / {relative_path}" if relative_path else device
            self.selected_destination.set(f"選択中: {shown_path}")
        elif row:
            if self.destination_mode.get() == "new":
                self.selected_destination.set(f"作成場所: {row.get('device', row.get('name', ''))}")
            else:
                self.selected_destination.set(f"端末: {row.get('device', row.get('name', ''))}（転送先フォルダを開いて選択）")
        else:
            self.selected_destination.set("未選択（フォルダを1回クリック）")
        self._refresh_transfer_button()

    def _on_folder_open(self, _event: tk.Event) -> None:
        iid = self.folder_tree.focus()
        try:
            folder_id = int(iid)
        except (TypeError, ValueError):
            return
        if folder_id in self.loaded_folder_ids or folder_id in self.requested_folder_ids:
            return
        self.requested_folder_ids.add(folder_id)
        placeholder = f"loading_{folder_id}"
        if self.folder_tree.exists(placeholder):
            self.folder_tree.item(placeholder, text="読み込み中…")
        self.status.config(text="選択したフォルダの中身を読み込んでいます…")
        if not self._send({"action": "children", "id": folder_id}):
            self.requested_folder_ids.discard(folder_id)
            if self.folder_tree.exists(placeholder):
                self.folder_tree.item(placeholder, text="読み込み失敗（再検索してください）")

    def _show_children(self, parent_id: int, folders: list[dict]) -> None:
        self.requested_folder_ids.discard(parent_id)
        self.loaded_folder_ids.add(parent_id)
        placeholder = f"loading_{parent_id}"
        if self.folder_tree.exists(placeholder):
            self.folder_tree.delete(placeholder)
        for folder in folders:
            iid = str(folder["id"])
            self.folders.append(folder)
            self.folder_tree.insert(str(parent_id), "end", iid=iid, text=folder.get("name", ""), open=False)
            self.folder_tree.insert(iid, "end", iid=f"loading_{iid}", text="フォルダを開くと中身を表示")
        if folders:
            self.status.config(text=f"{len(folders)} 個のフォルダを表示しました。転送先を選択してください。")
        else:
            parent = next((folder for folder in self.folders if int(folder["id"]) == parent_id), {})
            if parent.get("isDevice"):
                self.status.config(text="端末は見つかりましたが保存領域を読み取れません。端末のロック解除後に「再検索」してください。")
            else:
                self.status.config(text="この場所にはサブフォルダがありません。ここを転送先に選べます。")
        self._refresh_transfer_button()

    def _choose_source_folder(self) -> None:
        selected = filedialog.askdirectory(title="転送するファイルが入ったフォルダを選択")
        if not selected:
            return
        folder = Path(selected)
        self._cleanup_archive_temp()
        try:
            files = [path for path in folder.iterdir() if path.is_file()]
        except OSError as exc:
            messagebox.showerror("フォルダを読み取れません", str(exc))
            return
        self._set_source(files, selected, folder.name, {str(path): "" for path in files})

    def _choose_source_zip(self) -> None:
        selected = filedialog.askopenfilename(
            title="展開して転送するZIP／CBZを選択",
            filetypes=(("ZIP／CBZファイル", "*.zip *.cbz"), ("すべてのファイル", "*.*")),
        )
        if selected:
            self._load_zip(Path(selected))

    def _load_zip(self, archive: Path) -> None:
        self._cleanup_archive_temp()
        self.zip_request_id += 1
        request_id = self.zip_request_id
        self.zip_loading = True
        self.metadata_request_id += 1
        self.metadata_loading = False
        self.all_source_files = []
        self.source_files = []
        self.relative_paths = {}
        self.ordered_files = []
        self.metadata_by_path = {}
        self.source_label.config(text=f"{archive}（読み込み中）")
        self.preview.delete(*self.preview.get_children())
        self.extension_filter.set("すべて")
        self.extension_combo.configure(values=("すべて",), state="disabled")
        self.status.config(text="ZIPを安全に展開しています…")
        self._refresh_transfer_button()
        self.source_button.config(state="disabled")
        self.zip_button.config(state="disabled")
        self.zip_cancel_event = threading.Event()
        threading.Thread(target=self._extract_zip_worker,
                         args=(request_id, archive, self.zip_cancel_event), daemon=True).start()

    def _extract_zip_worker(self, request_id: int, archive: Path,
                            cancel_event: threading.Event) -> None:
        temp_root: Path | None = None
        try:
            temp_root = Path(tempfile.mkdtemp(prefix="ordered-transfer-zip-"))
            extracted: list[Path] = []
            relative_paths: dict[str, str] = {}
            total_size = 0
            last_zip_progress = 0.0
            with zipfile.ZipFile(archive) as source_zip:
                members = [entry for entry in source_zip.infolist() if not entry.is_dir()]
                if len(members) > 20000:
                    raise ValueError("ZIP内のファイル数が多すぎます（上限20,000件）。")
                extracted_bytes = 0
                for member_index, member in enumerate(members, 1):
                    if cancel_event.is_set():
                        raise InterruptedError("ZIPの読み込みが中止されました。")
                    raw_name = member.filename.replace("\\", "/")
                    relative = PurePosixPath(raw_name)
                    if (relative.is_absolute() or not relative.parts or "\x00" in raw_name
                            or any(part in ("", ".", "..") or any(char in part for char in '<>:"|?*')
                                   or part.endswith((".", " "))
                                   or part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
                                   for part in relative.parts)):
                        raise ValueError(f"安全のため展開できないパスが含まれています: {member.filename}")
                    unix_mode = (member.external_attr >> 16) & 0xFFFF
                    if unix_mode and (unix_mode & 0o170000) == 0o120000:
                        raise ValueError(f"ZIP内のリンクは展開できません: {member.filename}")
                    total_size += member.file_size
                    if total_size > 20 * 1024 ** 3:
                        raise ValueError("ZIPの展開後サイズが上限（20GB）を超えています。")
                    output = temp_root.joinpath(*relative.parts)
                    if output.exists():
                        raise ValueError(f"ZIP内に同じ保存先のファイルが複数あります: {member.filename}")
                    output.parent.mkdir(parents=True, exist_ok=True)
                    actual_member_bytes = 0
                    with source_zip.open(member) as input_stream, output.open("wb") as output_stream:
                        while True:
                            if cancel_event.is_set():
                                raise InterruptedError("ZIPの読み込みが中止されました。")
                            chunk = input_stream.read(1024 * 1024)
                            if not chunk:
                                break
                            actual_member_bytes += len(chunk)
                            extracted_bytes += len(chunk)
                            if actual_member_bytes > member.file_size or extracted_bytes > 20 * 1024 ** 3:
                                raise ValueError("ZIPの実際の展開後サイズが上限を超えています。")
                            output_stream.write(chunk)
                    if actual_member_bytes != member.file_size:
                        raise ValueError(f"ZIP内ファイルのサイズ情報が一致しません: {member.filename}")
                    extracted.append(output)
                    relative_paths[str(output)] = PurePosixPath(*relative.parts[:-1]).as_posix() if len(relative.parts) > 1 else ""
                    now = time.monotonic()
                    if member_index == 1 or member_index == len(members) or now - last_zip_progress >= 0.5:
                        self.events.put({"type": "zip_progress", "index": member_index,
                                         "total": len(members), "name": member.filename})
                        last_zip_progress = now
            if not extracted:
                raise ValueError("ZIP内にファイルがありません。")
            with self.lifecycle_lock:
                should_discard = self.closing or cancel_event.is_set()
                if not should_discard:
                    self.events.put({"type": "zip_ready", "requestId": request_id, "ok": True,
                                     "root": str(temp_root), "files": [str(path) for path in extracted],
                                     "relativePaths": relative_paths, "archive": str(archive)})
            if should_discard:
                shutil.rmtree(temp_root, ignore_errors=True)
                return
        except Exception as exc:
            if temp_root:
                shutil.rmtree(temp_root, ignore_errors=True)
            with self.lifecycle_lock:
                if not self.closing and not cancel_event.is_set():
                    self.events.put({"type": "zip_ready", "requestId": request_id, "ok": False, "message": str(exc)})

    def _finish_zip_load(self, event: dict) -> None:
        if int(event.get("requestId", -1)) != self.zip_request_id:
            return
        self.zip_loading = False
        self.source_button.config(state="normal")
        self.zip_button.config(state="normal")
        self.extension_combo.config(state="readonly")
        if not event.get("ok"):
            self.status.config(text="ZIPを展開できませんでした。")
            messagebox.showerror("ZIPを読み込めません", event.get("message", "ZIPを処理できませんでした。"))
            self._refresh_transfer_button()
            return
        self.archive_temp = Path(event["root"])
        archive = Path(event["archive"])
        files = [Path(path) for path in event["files"]]
        self._set_source(files, f"{archive}（展開して転送）", archive.stem, event["relativePaths"])

    def _set_source(self, files: list[Path], label: str, default_folder_name: str,
                    relative_paths: dict[str, str]) -> None:
        self.all_source_files = files
        self.relative_paths = relative_paths
        self.source_label.config(text=label)
        self.new_folder_name.set(default_folder_name)
        extensions = sorted({path.suffix.lower() for path in files if path.suffix}, key=str.casefold)
        if any(not path.suffix for path in files):
            extensions.append("拡張子なし")
        filter_values = ("すべて",) + tuple(extensions)
        self.extension_combo.configure(values=filter_values)
        self.extension_combo.config(state="readonly")
        self.extension_filter.set("すべて")
        self.source_files = list(files)
        self.last_moved_path = None
        self.sort_by.set("名前")
        self.direction_combo.config(state="readonly")
        self.metadata_by_path = {}
        self.metadata_request_id += 1
        self.metadata_loading = bool(self.source_files)
        self.sort_combo.configure(values=BASE_SORT_OPTIONS)
        if self.sort_by.get() not in BASE_SORT_OPTIONS:
            self.sort_by.set("名前")
        self._update_preview()
        self.status.config(text="ファイルの共通メタデータを調べています…")
        if self.source_files:
            if not self._send({"action": "source_metadata", "requestId": self.metadata_request_id,
                               "files": [str(path) for path in self.source_files]}):
                self.metadata_loading = False
        else:
            self.status.config(text="選択したフォルダにファイルがありません。")
        self._refresh_transfer_button()

    def _apply_extension_filter(self) -> None:
        extension = self.extension_filter.get()
        if extension == "すべて":
            self.source_files = list(self.all_source_files)
        elif extension == "拡張子なし":
            self.source_files = [path for path in self.all_source_files if not path.suffix]
        else:
            self.source_files = [path for path in self.all_source_files if path.suffix.lower() == extension]
        self._update_common_metadata_options()
        self._update_preview()
        self._refresh_transfer_button()

    def _update_common_metadata_options(self) -> None:
        common = set(METADATA_SORT_TYPES) if self.source_files else set()
        for path in self.source_files:
            values = self.metadata_by_path.get(str(path), {})
            common.intersection_update(key for key in values if values[key] is not None and str(values[key]).strip())
        options = BASE_SORT_OPTIONS + tuple(key for key in METADATA_SORT_TYPES if key in common)
        self.sort_combo.configure(values=options)
        if self.sort_by.get() not in options:
            self.sort_by.set("名前")
        self.direction_combo.config(state="disabled" if self.busy else "readonly")

    def _on_sort_selected(self, _event: tk.Event) -> None:
        self.direction_combo.config(state="disabled" if self.busy else "readonly")
        self._update_preview()

    def _cleanup_archive_temp(self) -> None:
        if self.archive_temp:
            shutil.rmtree(self.archive_temp, ignore_errors=True)
            self.archive_temp = None

    def _finish_source_metadata(self, event: dict) -> None:
        if int(event.get("requestId", -1)) != self.metadata_request_id:
            return
        self.metadata_loading = False
        records = event.get("files", [])
        by_path = {str(row.get("path", "")): row.get("metadata", {}) for row in records}
        self.metadata_by_path = by_path
        self._update_common_metadata_options()
        self._update_preview()
        message = event.get("message")
        self.status.config(text=(f"メタデータを一部取得できませんでした。基本項目で並べ替えできます: {message}"
                                 if message else f"共通メタデータを確認しました。並べ替え項目: {len(self.sort_combo['values'])} 種類"))
        self._refresh_transfer_button()

    def _update_preview(self, preserve_order: bool = False) -> None:
        def natural_key(path: Path) -> tuple[tuple[int, object], ...]:
            parts = re.split(r"(\d+)", path.name.casefold())
            return tuple((1, int(part)) if part.isdigit() else (0, part) for part in parts)

        key = self.sort_by.get()
        if preserve_order:
            files = [path for path in getattr(self, "ordered_files", []) if path in self.source_files]
            files.extend(path for path in self.source_files if path not in files)
        elif key == "拡張子":
            files = sorted(self.source_files, key=lambda p: (p.suffix.casefold(), natural_key(p)))
        elif key == "ファイルサイズ":
            files = sorted(self.source_files, key=lambda p: (self._safe_stat(p, "st_size"), natural_key(p)))
        elif key in METADATA_SORT_TYPES:
            value_type = METADATA_SORT_TYPES[key]

            def metadata_key(path: Path) -> tuple:
                raw = self.metadata_by_path.get(str(path), {}).get(key, "")
                if value_type == "number":
                    number = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", str(raw))
                    return (0, float(number.group(0))) if number else (1, 0)
                if value_type == "date":
                    text = str(raw).replace("Z", "+00:00")
                    try:
                        return (0, datetime.fromisoformat(text).timestamp())
                    except (ValueError, OSError):
                        return (1, 0)
                return (0, natural_key(Path(str(raw))))

            files = sorted(self.source_files, key=lambda p: (metadata_key(p), natural_key(p)))
        elif key == "更新日時":
            files = sorted(self.source_files, key=lambda p: (self._safe_stat_time(p, "st_mtime"), natural_key(p)))
        elif key == "作成日時":
            files = sorted(self.source_files, key=lambda p: (self._safe_stat_time(p, "st_ctime"), natural_key(p)))
        elif key == "アクセス日時":
            files = sorted(self.source_files, key=lambda p: (self._safe_stat_time(p, "st_atime"), natural_key(p)))
        else:
            files = sorted(self.source_files, key=natural_key)
        if not preserve_order and self.direction.get() == "降順":
            files.reverse()
        self.ordered_files = files
        self.preview.delete(*self.preview.get_children())
        moved_row: str | None = None
        for index, path in enumerate(files, 1):
            try:
                size = path.stat().st_size
            except OSError:
                size = -1
            relative = self.relative_paths.get(str(path), "")
            label = f"{relative}/{path.name}" if relative else path.name
            row = f"preview_{index}"
            self.preview.insert("", "end", iid=row,
                                values=(f"{index:03d}", label, "ファイルが見つかりません" if size < 0 else self._format_size(size)))
            if path == self.last_moved_path:
                moved_row = row
        if moved_row:
            self.preview.selection_set(moved_row)
            self.preview.focus(moved_row)

    @staticmethod
    def _safe_stat_time(path: Path, attribute: str) -> float:
        try:
            return float(getattr(path.stat(), attribute))
        except OSError:
            return float("inf")

    @staticmethod
    def _safe_stat(path: Path, attribute: str) -> int | float:
        try:
            return getattr(path.stat(), attribute)
        except (OSError, AttributeError, TypeError, ValueError):
            return float("inf")

    @staticmethod
    def _format_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024
        return str(size)

    def _refresh(self) -> None:
        if not self.busy:
            if not self.bridge_available:
                self.status.config(text="転送機能が停止しています。アプリを再起動してください。")
                return
            self._show_folders([])
            self.connection_label.config(text="端末のフォルダを検索しています…")
            self.refresh_button.config(state="disabled")
            if not self._send({"action": "scan"}):
                self.refresh_button.config(state="normal")

    def _refresh_transfer_button(self) -> None:
        selected = self.folder_tree.selection()
        selected_row = next((folder for folder in self.folders if selected and str(folder["id"]) == selected[0]), None)
        create_new = self.destination_mode.get() == "new"
        selected_is_folder = bool(selected_row and (create_new or not selected_row.get("isDevice")))
        folder_name = self.new_folder_name.get().strip()
        valid = bool(self.bridge_available and self.source_files and not self.metadata_loading and not self.zip_loading and selected_is_folder and self.folders and not self.busy
                     and (not create_new or folder_name))
        self.transfer_button.config(state="normal" if valid else "disabled")

    def _on_destination_mode(self) -> None:
        self.new_folder_entry.config(state="normal" if self.destination_mode.get() == "new" and not self.busy else "disabled")
        self._on_folder_select(None)
        self._refresh_transfer_button()

    def _update_progress(self, bytes_done: int | None = None, bytes_total: int | None = None) -> None:
        if bytes_total and bytes_done is not None and bytes_total > 0:
            done = max(0, min(int(bytes_done), int(bytes_total)))
            total = int(bytes_total)
            self.transfer_bytes_done = max(self.transfer_bytes_done, done)
            done = self.transfer_bytes_done
            self.transfer_bytes_total = total
            percent = min(99 if self.busy else 100, round(done * 100 / total))
            amount = f"{self._format_size(done)}/{self._format_size(total)}"
            detail = f"{amount}・{self.transfer_processed}/{self.transfer_total}件"
        elif self.transfer_total > 0:
            percent = min(99 if self.busy else 100,
                          round(self.transfer_processed * 100 / self.transfer_total))
            detail = f"{self.transfer_processed}/{self.transfer_total}件"
        else:
            percent = 0
            detail = ""
        self.progress_bar.configure(value=percent)
        self.progress_text.config(text=f"{percent}% {detail}".rstrip())

        self._refresh_metrics()

    def _preview_drag_start(self, event: tk.Event) -> None:
        if self.busy:
            return
        row = self.preview.identify_row(event.y)
        self.dragged_preview_row = row or None
        rows = list(self.preview.get_children())
        self.dragged_preview_path = self.ordered_files[rows.index(row)] if row in rows else None
        self.drop_insert_index = None

    def _preview_drag_motion(self, event: tk.Event) -> None:
        if self.busy or not self.dragged_preview_path:
            return
        if self.drag_overlay is None or not self.drag_overlay.winfo_exists():
            self.drag_overlay = tk.Toplevel(self.root)
            self.drag_overlay.overrideredirect(True)
            try:
                self.drag_overlay.attributes("-alpha", 0.86)
                self.drag_overlay.attributes("-topmost", True)
                self.drag_overlay.attributes("-disabled", True)
            except tk.TclError:
                pass
            self.drag_hint = tk.Label(self.drag_overlay, justify="left", anchor="w", padx=9, pady=4,
                                      text="", background="#FFFFFF", foreground="#202020",
                                      relief="solid", borderwidth=1, font=("Segoe UI", 9))
            self.drag_hint.pack()

        rows = list(self.preview.get_children())
        target_row = self.preview.identify_row(event.y)
        if target_row and target_row in rows:
            target_index = rows.index(target_row)
            box = self.preview.bbox(target_row)
            after = bool(box and event.y >= box[1] + box[3] / 2)
            self.drop_insert_index = target_index + (1 if after else 0)
        else:
            if rows:
                first_box = self.preview.bbox(rows[0])
                last_box = self.preview.bbox(rows[-1])
                if first_box and event.y < first_box[1]:
                    self.drop_insert_index = 0
                else:
                    self.drop_insert_index = len(rows)
            else:
                self.drop_insert_index = 0
        self.drag_hint.config(text=self.dragged_preview_path.name)
        overlay_width = max(230, self.drag_overlay.winfo_reqwidth())
        overlay_height = self.drag_overlay.winfo_reqheight()
        x = min(event.x_root + 18, self.root.winfo_screenwidth() - overlay_width - 8)
        y = min(event.y_root + 18, self.root.winfo_screenheight() - overlay_height - 8)
        self.drag_overlay.geometry(f"+{max(0, x)}+{max(0, y)}")
        self._place_drop_marker(rows)

    def _place_drop_marker(self, rows: list[str]) -> None:
        if self.drop_marker is None or not self.drop_marker.winfo_exists():
            self.drop_marker = tk.Toplevel(self.root)
            self.drop_marker.overrideredirect(True)
            try:
                self.drop_marker.attributes("-topmost", True)
                self.drop_marker.attributes("-disabled", True)
            except tk.TclError:
                pass
            marker = tk.Frame(self.drop_marker, background="#1473E6", height=3)
            marker.pack(fill="x")
        index = self.drop_insert_index or 0
        if rows and index < len(rows):
            box = self.preview.bbox(rows[index])
            y = self.preview.winfo_rooty() + box[1] if box else self.preview.winfo_rooty()
        elif rows:
            box = self.preview.bbox(rows[-1])
            y = self.preview.winfo_rooty() + box[1] + box[3] if box else self.preview.winfo_rooty()
        else:
            y = self.preview.winfo_rooty() + 2
        width = max(1, self.preview.winfo_width() - 4)
        self.drop_marker.geometry(f"{width}x3+{self.preview.winfo_rootx()+2}+{y-1}")

    def _preview_drag_end(self, event: tk.Event) -> None:
        source_row = self.dragged_preview_row
        self.dragged_preview_row = None
        dragged_path = self.dragged_preview_path
        self.dragged_preview_path = None
        self._clear_drag_overlay()
        if self.busy or not source_row or not dragged_path or self.drop_insert_index is None:
            self.drop_insert_index = None
            return
        rows = list(self.preview.get_children())
        try:
            source_index = rows.index(source_row)
        except ValueError:
            self.drop_insert_index = None
            return
        insert_index = self.drop_insert_index
        self.drop_insert_index = None
        if insert_index in (source_index, source_index + 1):
            return
        moved = self.ordered_files.pop(source_index)
        if source_index < insert_index:
            insert_index -= 1
        self.ordered_files.insert(insert_index, moved)
        self.last_moved_path = moved
        self._update_preview(preserve_order=True)

    def _clear_drag_overlay(self) -> None:
        if self.drag_overlay is not None:
            try:
                self.drag_overlay.destroy()
            except tk.TclError:
                pass
            self.drag_overlay = None
        if self.drop_marker is not None:
            try:
                self.drop_marker.destroy()
            except tk.TclError:
                pass
            self.drop_marker = None

    @staticmethod
    def _format_duration(seconds: float) -> str:
        value = max(0, int(seconds))
        minutes, remaining = divmod(value, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{remaining:02d}" if hours else f"{minutes:02d}:{remaining:02d}"

    def _refresh_metrics(self) -> None:
        if self.transfer_started_at is None:
            return
        elapsed = max(0.0, time.monotonic() - self.transfer_started_at)
        if self.transfer_bytes_total > 0:
            rate = self.transfer_bytes_done / max(elapsed, 0.001)
            speed = f"{self._format_size(int(rate))}/秒" if self.transfer_bytes_done else "--"
            if self.busy and self.transfer_bytes_done >= self.transfer_bytes_total:
                remaining = "完了確認中"
            elif rate > 0:
                remaining = self._format_duration((self.transfer_bytes_total - self.transfer_bytes_done) / rate)
            else:
                remaining = "--"
        elif self.transfer_total > 0:
            rate = self.transfer_processed / max(elapsed, 0.001)
            speed = f"{rate:.1f}件/秒" if self.transfer_processed else "--"
            remaining = self._format_duration((self.transfer_total - self.transfer_processed) / rate) if rate > 0 else "--"
        else:
            speed = remaining = "--"
        if not self.busy and self.transfer_bytes_total > 0 and self.transfer_bytes_done >= self.transfer_bytes_total:
            remaining = "完了"
        self.metrics_text.config(text=f"経過 {self._format_duration(elapsed)} | 平均速度 {speed} | 残り目安 {remaining}")

    def _tick_metrics(self) -> None:
        if self.busy:
            self._refresh_metrics()
        self.root.after(1000, self._tick_metrics)

    def _transfer(self) -> None:
        if not self.folder_tree.selection() or not self.source_files:
            return
        self._update_preview()
        target_id = int(self.folder_tree.selection()[0])
        target = next((f for f in self.folders if int(f["id"]) == target_id), None)
        if not target:
            return
        create_folder_name = self.new_folder_name.get().strip() if self.destination_mode.get() == "new" else ""
        if create_folder_name and (create_folder_name in {".", ".."} or any(c in create_folder_name for c in '\\/:*?"<>|')):
            messagebox.showerror("フォルダ名を確認", "フォルダ名に使用できない文字が含まれています。")
            return
        if create_folder_name and (create_folder_name.endswith((".", " "))):
            messagebox.showerror("フォルダ名を確認", "フォルダ名の末尾にドットや空白は使えません。")
            return
        self._set_busy(True)
        self.transfer_results = []
        self.cancel_button.config(state="disabled")
        self.transfer_started_at = None
        self.metrics_text.config(text="転送前確認中…")
        transfer_files = list(self.ordered_files)
        if self.reverse_transfer.get():
            transfer_files.reverse()
        files = [str(path) for path in transfer_files]
        self.pending_transfer = {
            "targetId": target_id,
            "target": target,
            "files": files,
            "sortBy": self.sort_by.get(),
            "direction": self.direction.get(),
            "skipExisting": self.skip_existing.get(),
            "reverseOrder": self.reverse_transfer.get(),
            "createFolderName": create_folder_name,
        }
        self.status.config(text="転送前確認: 端末側の同名ファイルを調べています…")
        if not self._send({"action": "preflight", "targetId": target_id, "files": files,
                           "createFolderName": create_folder_name,
                           "relativePaths": [self.relative_paths.get(path, "") for path in files]}):
            self.pending_transfer = None
            self._set_busy(False)

    def _finish_preflight(self, event: dict) -> None:
        pending = self.pending_transfer
        self.pending_transfer = None
        if not pending:
            return
        if not event.get("ok"):
            self._set_busy(False)
            self.status.config(text="転送前確認で停止しました。")
            messagebox.showerror("転送前確認", event.get("message", "端末側のファイルを確認できませんでした。"))
            return

        raw_conflicts = event.get("conflicts", [])
        conflicts = [raw_conflicts] if isinstance(raw_conflicts, str) else list(raw_conflicts)
        if conflicts and not pending["skipExisting"]:
            self._set_busy(False)
            names = "\n".join(conflicts[:12])
            suffix = f"\nほか {len(conflicts) - 12} 個" if len(conflicts) > 12 else ""
            messagebox.showwarning(
                "同名ファイルがあります",
                f"転送先に同名ファイルが {len(conflicts)} 個あります。\n{names}{suffix}\n\n"
                "上書きせずに停止しました。同名ファイルをスキップする場合はチェックを入れてください。",
            )
            self.status.config(text=f"同名ファイル {len(conflicts)} 個を確認しました。設定を選び直してください。")
            return

        files = [Path(path) for path in pending["files"]]
        if not files:
            self._set_busy(False)
            self.status.config(text="転送するファイルがありません。")
            return
        try:
            total_bytes = sum(path.stat().st_size for path in files)
        except OSError as exc:
            self._set_busy(False)
            self.status.config(text="送信元ファイルを読み取れません。選び直してください。")
            messagebox.showerror("送信元ファイルを確認", str(exc))
            return
        order_name = f"{pending['sortBy']}・{pending['direction']}"
        if pending.get("reverseOrder"):
            order_name += "・プレビューの下から転送"
        target = pending["target"]
        device = target.get("device", "")
        path = target.get("path", "")
        relative_path = path[len(device):].lstrip("\\/") if device and path.startswith(device) else path
        destination = f"{device} / {relative_path}" if relative_path else device
        if pending["createFolderName"]:
            destination = f"{destination} / {pending['createFolderName']}" if destination else pending["createFolderName"]
        conflict_line = (f"同名ファイル: {len(conflicts)} 個をスキップ" if conflicts else "同名ファイル: なし")
        destination_action = "新規フォルダを作成して転送" if pending["createFolderName"] else "選択したフォルダへ転送"
        prompt = (
            f"送信元: {self.source_label.cget('text')}\n"
            f"件数: {len(files)} 個\n"
            f"順番: {order_name}（{files[0].name} → {files[-1].name}）\n"
            f"合計サイズ: {self._format_size(total_bytes)}\n"
            f"保存先: {destination}\n"
            f"方法: {destination_action}\n"
            f"{conflict_line}\n\nこの内容で転送しますか？"
        )
        if not messagebox.askyesno("転送内容の確認", prompt):
            self._set_busy(False)
            self.status.config(text="転送を開始しませんでした。")
            return

        try:
            self.transfer_results = [
                {"name": path.name, "size": self._format_size(path.stat().st_size),
                 "sizeBytes": path.stat().st_size, "status": "待機"}
                for path in files
            ]
        except OSError as exc:
            self._set_busy(False)
            self.status.config(text="送信元ファイルを読み取れません。選び直してください。")
            messagebox.showerror("送信元ファイルを確認", str(exc))
            return
        self.transfer_total = len(self.ordered_files)
        self.transfer_processed = 0
        self.transfer_bytes_total = total_bytes
        self.transfer_bytes_done = 0
        self.transfer_started_at = time.monotonic()
        self.transfer_last_event_at = self.transfer_started_at
        self.transfer_stall_timeout = 12.0
        self.transfer_active_index = 0
        self.bridge_unresponsive_handled = False
        self.device_disconnect_handled = False
        self._start_device_disconnect_monitor()
        self.progress_bar.configure(value=0)
        self.progress_text.config(text=f"0% 0/{self.transfer_total}件")
        self._refresh_metrics()
        self.cancel_file = Path(tempfile.gettempdir()) / f"order-transfer-cancel-{uuid.uuid4().hex}.flag"
        self.cancel_file.unlink(missing_ok=True)
        self.status.config(text="転送を準備しています…")
        if not self._send({"action": "transfer", "targetId": pending["targetId"],
                           "files": pending["files"], "cancelFile": str(self.cancel_file),
                           "skipExisting": pending["skipExisting"],
                           "createFolderName": pending["createFolderName"],
                           "relativePaths": [self.relative_paths.get(path, "") for path in pending["files"]]}):
            self._set_busy(False)
            self._remove_cancel_file()
        else:
            self.cancel_button.config(state="normal")

    def _cancel_transfer(self) -> None:
        if not self.busy or self.cancel_file is None:
            return
        if not messagebox.askyesno("転送を中止", "現在転送中のファイルの処理が終わった時点で中止します。次のファイルは送りません。よろしいですか？"):
            return
        logger.warning("user_cancel_requested index=%s", self.transfer_active_index)
        try:
            self.cancel_file.write_text("cancel", encoding="ascii")
        except OSError as exc:
            messagebox.showerror("中止できません", f"中止要求を送れませんでした: {exc}")
            return
        self.cancel_button.config(state="disabled")
        self.status.config(text="中止要求を受け付けました。現在のファイルを確認しています…")

    def _remove_cancel_file(self) -> None:
        if self.cancel_file:
            try:
                self.cancel_file.unlink(missing_ok=True)
            except OSError:
                pass
            self.cancel_file = None

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.source_button.config(state=state)
        self.zip_button.config(state=state)
        self.extension_combo.config(state="disabled" if busy else "readonly")
        self.skip_box.config(state=state)
        self.reverse_transfer_box.config(state=state)
        self.existing_mode_radio.config(state=state)
        self.new_mode_radio.config(state=state)
        self.new_folder_entry.config(state="normal" if not busy and self.destination_mode.get() == "new" else "disabled")
        combo_state = "disabled" if busy else "readonly"
        self.sort_combo.config(state=combo_state)
        self.direction_combo.config(state="disabled" if busy else "readonly")
        self.refresh_button.config(state=state)
        self.transfer_button.config(state="disabled")
        # Preflight is also busy, but cancellation is only available after the
        # actual MTP transfer request has been accepted by the bridge.
        self.cancel_button.config(state="disabled")
        self.folder_tree.config(selectmode="none" if busy else "browse")
        if not busy:
            self._refresh_transfer_button()

    def _close(self) -> None:
        if self.close_after_cancel:
            return
        if self.busy:
            if not messagebox.askyesno("転送中", "閉じると中止要求を送り、現在のファイルの処理が終わるまで待ってからアプリを終了します。よろしいですか？"):
                return
            if self.cancel_file is None:
                # Preflight has not written to the device; it is safe to stop it immediately.
                self.pending_transfer = None
                self._finish_close()
                return
            self.close_after_cancel = True
            logger.warning("window_close_during_transfer index=%s", self.transfer_active_index)
            try:
                self.cancel_file.write_text("cancel", encoding="ascii")
            except OSError as exc:
                self.close_after_cancel = False
                messagebox.showerror("中止できません", f"中止要求を送れないため、アプリを閉じませんでした。\n{exc}")
                return
            self.cancel_button.config(state="disabled")
            self.status.config(text="終了のため中止要求を送信しました。現在のファイルの処理が終わるまで待っています…")
            return
        self._finish_close()

    def _finish_close(self) -> None:
        if self.closing:
            return
        queued_zip_roots: list[str] = []
        with self.lifecycle_lock:
            self.closing = True
            self.device_monitor_stop.set()
            if self.zip_cancel_event:
                self.zip_cancel_event.set()
            while True:
                try:
                    queued_event = self.events.get_nowait()
                except queue.Empty:
                    break
                if queued_event.get("type") == "zip_ready" and queued_event.get("root"):
                    queued_zip_roots.append(str(queued_event["root"]))
        for root in queued_zip_roots:
            shutil.rmtree(root, ignore_errors=True)
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write('{"action":"quit"}\n')
                self.process.stdin.flush()
                self.process.terminate()
            except (OSError, AttributeError):
                pass
        self._cleanup_archive_temp()
        self._clear_drag_overlay()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    app = MtpOrderTransfer(window)
    window.mainloop()
