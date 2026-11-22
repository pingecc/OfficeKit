// 壳层命令封装：所有 Tauri invoke 集中在这里，UI 组件不直接碰 @tauri-apps/api。
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { getCurrentWebview } from '@tauri-apps/api/webview';

export interface EngineStatus {
  version: string;
  soffice: boolean;
}

export interface OfficeResultItem {
  input: string;
  ok: boolean;
  output: string | null;
  error: string | null;
}

export const engineStatus = () => invoke<EngineStatus>('engine_status');
export const pickFiles = (kind: string) => invoke<string[]>('pick_files', { kind });
export const pickSave = (kind: string, defaultName?: string) =>
  invoke<string | null>('pick_save', { kind, defaultName: defaultName ?? null });
export const pickDir = () => invoke<string | null>('pick_dir');
export const openPath = (path: string) => invoke<void>('open_path', { path });

export const pdf2word = (input: string, output: string | null, pages: string | null) =>
  invoke<{ output: string }>('pdf2word', { input, output, pages });

export const office2pdf = (inputs: string[], outdir: string | null) =>
  invoke<{ results: OfficeResultItem[] }>('office2pdf', { inputs, outdir });

export interface EngineProgress {
  event: string;
  percent?: number;
  message?: string;
}

/** 引擎进度事件（sidecar stdout 的 JSON 行转发而来）；percent 缺省表示不推进进度条 */
export function onEngineProgress(cb: (p: EngineProgress) => void): Promise<() => void> {
  return listen<EngineProgress>('engine-progress', (e) => cb(e.payload));
}

/** 文件拖拽：Tauri 的 webview 拖拽不走 HTML5 事件，走原生事件 */
export function onFileDrop(
  onDrop: (paths: string[]) => void,
  onOverChange?: (over: boolean) => void,
): Promise<() => void> {
  return getCurrentWebview().onDragDropEvent((event) => {
    const t = event.payload.type;
    if (t === 'drop') onDrop(event.payload.paths);
    else if (t === 'enter') onOverChange?.(true);
    else if (t === 'leave') onOverChange?.(false);
  });
}

export function basename(p: string) {
  return p.split('/').pop() || p;
}

export function dirname(p: string) {
  const parts = p.split('/');
  parts.pop();
  return parts.join('/');
}
