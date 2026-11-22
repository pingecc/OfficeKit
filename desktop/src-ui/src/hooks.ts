import { useEffect, useState } from 'react';
import { onEngineProgress } from './api';

export interface ProgressState {
  percent: number;
  stage: string;
}

/** 订阅引擎进度事件；事件缺 percent 时保持进度条原位，只更新文案。 */
export function useEngineProgress() {
  const [state, setState] = useState<ProgressState>({ percent: 0, stage: '' });

  useEffect(() => {
    let alive = true;
    let un: (() => void) | undefined;
    onEngineProgress((e) => {
      if (!alive) return;
      setState((s) => ({
        percent: typeof e.percent === 'number' ? e.percent : s.percent,
        stage: e.message ?? s.stage,
      }));
    }).then((f) => {
      if (alive) un = f;
      else f();
    });
    return () => {
      alive = false;
      un?.();
    };
  }, []);

  const resetProgress = () => setState({ percent: 0, stage: '' });
  return { progress: state, resetProgress };
}
