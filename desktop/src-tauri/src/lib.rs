//! OfficeKit 桌面壳层（Tauri 2）。
//!
//! 架构：壳层不实现任何文档逻辑，只负责「选文件 → 调引擎 sidecar → 展示结果」。
//! 引擎（officekit-engine，PyInstaller 打包的 Python sidecar）通过 JSON-RPC over
//! stdin/stdout 通信，协议见 `engine/officekit/serve.py` 模块文档。
//!
//! 当前 v1 采用「每次转换拉起一个 sidecar 进程」的简单模型，损耗约 1-2s 启动时间；
//! 若未来有高频小请求场景，再演进为常驻会话（见 docs/architecture.md）。

use serde_json::{json, Value};
use tauri::{AppHandle, Emitter};
use tauri_plugin_dialog::DialogExt;
use tokio::sync::oneshot;
use tauri_plugin_opener::OpenerExt;
use tauri_plugin_shell::process::{CommandEvent, Command as ShellCommand};
use tauri_plugin_shell::ShellExt;

const REQUEST_ID: u64 = 1;
/// sidecar 落盘路径随构建形态不同：bundle 内被展平为 `Contents/MacOS/officekit-engine`，
/// dev/其他形态可能保留 `binaries/` 前缀 —— 运行时逐个候选解析（见 docs/architecture.md 踩坑记录）。
const SIDECAR_CANDIDATES: [&str; 2] = ["officekit-engine", "binaries/officekit-engine"];

/// 解析并构造引擎 sidecar 命令（serve 模式）。
fn engine_command(app: &AppHandle) -> Result<ShellCommand, String> {
    let shell = app.shell();
    SIDECAR_CANDIDATES
        .iter()
        .find_map(|name| shell.sidecar(name).ok())
        .map(|cmd| cmd.args(["serve"]).kill_on_drop(true))
        .ok_or_else(|| "找不到 officekit-engine 引擎（应用可能安装不完整，请重新安装）".to_string())
}

/// 发起一次 sidecar 请求：拉起 kaiwu-engine（serve 模式），写一行请求，
/// 逐行读 stdout —— 进度事件转发给前端，匹配 id 的行作为最终响应返回。
async fn engine_request(app: AppHandle, method: &str, params: Value) -> Result<Value, String> {
    let (mut rx, mut child) = engine_command(&app)?
        .spawn()
        .map_err(|e| format!("启动引擎失败：{e}"))?;

    let request = json!({ "id": REQUEST_ID, "method": method, "params": params });
    child
        .write(format!("{request}\n").as_bytes())
        .map_err(|e| format!("写入引擎失败：{e}"))?;

    let mut response: Option<Value> = None;
    while let Some(event) = rx.recv().await {
        match event {
            CommandEvent::Stdout(line) => {
                let text = String::from_utf8_lossy(&line).to_string();
                match serde_json::from_str::<Value>(&text) {
                    // 进度/事件行（无 id）→ 转发给前端
                    Ok(v) if v.get("event").is_some() => {
                        let _ = app.emit("engine-progress", v);
                    }
                    // 匹配 id 的响应行 → 本次请求的最终结果。
                    // 一次性请求模型：引擎 serve 循环不会自己退出，拿到响应必须主动
                    // kill，否则等不到 Terminated 事件，前端 Promise 永远不 resolve。
                    Ok(v) if v.get("id") == Some(&json!(REQUEST_ID)) => {
                        response = Some(v);
                        let _ = child.kill();
                        break;
                    }
                    _ => {}
                }
            }
            CommandEvent::Stderr(line) => {
                let _ = app.emit("engine-stderr", String::from_utf8_lossy(&line).to_string());
            }
            CommandEvent::Terminated(_) => break,
            _ => {}
        }
    }

    match response {
        Some(v) if v.get("ok") == Some(&json!(true)) => Ok(v["result"].clone()),
        Some(v) => Err(v
            .get("error")
            .and_then(|e| e.as_str())
            .unwrap_or("引擎返回未知错误")
            .to_string()),
        None => Err("引擎未返回结果（进程意外退出）".into()),
    }
}

#[tauri::command]
async fn engine_status(app: AppHandle) -> Result<Value, String> {
    engine_request(app, "ping", json!({})).await
}

#[tauri::command]
async fn pdf2word(
    app: AppHandle,
    input: String,
    output: Option<String>,
    pages: Option<String>,
) -> Result<Value, String> {
    let mut params = json!({ "input": input });
    if let Some(o) = output.filter(|s| !s.trim().is_empty()) {
        params["output"] = json!(o);
    }
    if let Some(p) = pages.filter(|s| !s.trim().is_empty()) {
        params["pages"] = json!(p);
    }
    engine_request(app, "pdf2word", params).await
}

#[tauri::command]
async fn office2pdf(
    app: AppHandle,
    inputs: Vec<String>,
    outdir: Option<String>,
) -> Result<Value, String> {
    let mut params = json!({ "inputs": inputs });
    if let Some(d) = outdir.filter(|s| !s.trim().is_empty()) {
        params["outdir"] = json!(d);
    }
    engine_request(app, "office2pdf", params).await
}

fn dialog_filters(kind: &str) -> (&'static str, Vec<&'static str>) {
    match kind {
        "pdf" => ("PDF 文件", vec!["pdf"]),
        "docx" => ("Word 文档", vec!["docx"]),
        "office" => (
            "Office 文档",
            vec!["docx", "doc", "xlsx", "xls", "pptx", "ppt"],
        ),
        _ => ("所有文件", vec!["*"]),
    }
}

/// 注意：文件对话框绝不能用 blocking_* 变体 —— macOS 上同步命令会在主线程的
/// IPC 分发中执行，blocking_* 等待一个只能在主线程打开的对话框，直接死锁
/// （现象：点「选择文件」后应用整体卡死）。统一用回调式 API + oneshot 通道，
/// 命令本身为 async（跑在 tokio 工作线程，不占主线程）。
#[tauri::command]
async fn pick_files(app: AppHandle, kind: String) -> Result<Vec<String>, String> {
    let (name, exts) = dialog_filters(&kind);
    let (tx, rx) = oneshot::channel();
    app.dialog()
        .file()
        .add_filter(name, &exts)
        .pick_files(move |picked| {
            let paths = picked
                .unwrap_or_default()
                .into_iter()
                .filter_map(|fp| fp.into_path().ok())
                .map(|p| p.to_string_lossy().into_owned())
                .collect();
            let _ = tx.send(paths);
        });
    rx.await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn pick_save(
    app: AppHandle,
    kind: String,
    default_name: Option<String>,
) -> Result<Option<String>, String> {
    let (name, exts) = dialog_filters(&kind);
    let (tx, rx) = oneshot::channel();
    let mut builder = app.dialog().file().add_filter(name, &exts);
    if let Some(n) = default_name {
        builder = builder.set_file_name(n);
    }
    builder.pick_file(move |picked| {
        let path = picked
            .and_then(|fp| fp.into_path().ok())
            .map(|p| p.to_string_lossy().into_owned());
        let _ = tx.send(path);
    });
    rx.await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn pick_dir(app: AppHandle) -> Result<Option<String>, String> {
    let (tx, rx) = oneshot::channel();
    app.dialog().file().pick_folder(move |picked| {
        let path = picked
            .and_then(|fp| fp.into_path().ok())
            .map(|p| p.to_string_lossy().into_owned());
        let _ = tx.send(path);
    });
    rx.await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn open_path(app: AppHandle, path: String) -> Result<(), String> {
    // opener 内部会走 NSWorkspace：放到阻塞线程池执行，避免在主线程分发中同步等待
    tauri::async_runtime::spawn_blocking(move || {
        app.opener()
            .open_path(path, None::<&str>)
            .map_err(|e| e.to_string())
    })
    .await
    .map_err(|e| e.to_string())?
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            engine_status,
            pdf2word,
            office2pdf,
            pick_files,
            pick_save,
            pick_dir,
            open_path
        ])
        .run(tauri::generate_context!())
        .expect("启动开物失败");
}
