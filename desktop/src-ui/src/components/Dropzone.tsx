import { useEffect, useRef, useState } from 'react';
import { IconPlus } from '@arco-design/web-react/icon';
import { onFileDrop, pickFiles } from '../api';

interface Props {
  /** pick_files 的 kind（pdf / office） */
  kind: string;
  /** 允许的扩展名（小写、带点） */
  accept: string[];
  multiple?: boolean;
  title: string;
  hint?: string;
  onFiles: (paths: string[]) => void;
}

export default function Dropzone({ kind, accept, multiple = false, title, hint, onFiles }: Props) {
  const [over, setOver] = useState(false);
  const onFilesRef = useRef(onFiles);
  onFilesRef.current = onFiles;

  useEffect(() => {
    const unlistens: Array<() => void> = [];
    onFileDrop(
      (paths) => {
        const ok = paths.filter((p) => accept.some((ext) => p.toLowerCase().endsWith(ext)));
        if (ok.length) onFilesRef.current(multiple ? ok : [ok[0]]);
      },
      setOver,
    ).then((f) => unlistens.push(f));
    return () => unlistens.forEach((f) => f());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accept.join(','), multiple]);

  const browse = async () => {
    const picked = await pickFiles(kind);
    if (picked.length) onFilesRef.current(multiple ? picked : [picked[0]]);
  };

  return (
    <div className={`dropzone ${over ? 'over' : ''}`} onClick={browse} role="button">
      <IconPlus className="dz-icon" />
      <div className="dz-title">{title}</div>
      <div className="dz-hint">{hint ?? '也可以把文件直接拖到这里'}</div>
    </div>
  );
}
