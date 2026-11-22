import { useEffect, useRef, useState } from 'react';
import { onEngineProgress } from './api';

export interface ProgressState {
  percent: number;
  stage: string;
}

/**
 * 引擎进度订阅 + 平滑动画。
 *
 * 引擎的百分比事件是"突发"的（阶段跃变；单文件任务甚至只有 0→100 两个点），
 * 直接渲染会在 0% 停很久。这里用缓动曲线兜底：
 *  - 没有真实进度时，向 90% 缓慢爬行（每 tick 前进剩余距离的 8%），起步即离开 0%
 *  - 真实进度到达后作为下限参与动画（只进不退），≥90% 时上限放开到 100%
 *  - resetProgress 在每次新任务开始时归零
 */
export function useEngineProgress() {
  const [state, setState] = useState<ProgressState>({ percent: 0, stage: '' });
  const enginePercent = useRef<number | null>(null); // 引擎报告的真实进度（null = 尚未收到）
  const display = useRef(0); // 当前展示值（平滑后）

  useEffect(() => {
    const timer = window.setInterval(() => {
      const engine = enginePercent.current;
      const cap = engine !== null && engine >= 90 ? 100 : 90;
      const goal = engine !== null ? Math.max(engine, display.current) : display.current;
      const target = Math.min(goal, cap);
      display.current += (target - display.current) * 0.08;
      if (engine === null) {
        display.current = Math.max(display.current, 3); // 起步别停在 0%
      }
      setState((s) => ({ ...s, percent: Math.min(100, Math.round(display.current)) }));
    }, 180);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let alive = true;
    let un: (() => void) | undefined;
    onEngineProgress((e) => {
      if (!alive) return;
      if (typeof e.percent === 'number') {
        enginePercent.current = Math.max(enginePercent.current ?? 0, e.percent);
      }
      if (e.message) {
        setState((s) => ({ ...s, stage: e.message as string }));
      }
    }).then((f) => {
      if (alive) un = f;
      else f();
    });
    return () => {
      alive = false;
      un?.();
    };
  }, []);

  const resetProgress = () => {
    enginePercent.current = null;
    display.current = 0;
    setState({ percent: 0, stage: '' });
  };

  return { progress: state, resetProgress };
}
