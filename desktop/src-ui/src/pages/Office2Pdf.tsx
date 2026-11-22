import { useState } from 'react';
import { Alert, Button, Message, Progress, Tag, Typography } from '@arco-design/web-react';
import { IconClose, IconFile, IconFolder } from '@arco-design/web-react/icon';
import Dropzone from '../components/Dropzone';
import { useEngineProgress } from '../hooks';
import { basename, dirname, office2pdf, openPath, pickDir, type EngineStatus, type OfficeResultItem } from '../api';

const { Text } = Typography;

const OFFICE_EXTS = ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'];

export default function Office2Pdf({ engine }: { engine: EngineStatus | null }) {
  const [files, setFiles] = useState<string[]>([]);
  const [outDir, setOutDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<OfficeResultItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { progress, resetProgress } = useEngineProgress();

  const addFiles = (ps: string[]) =>
    setFiles((old) => [...old, ...ps.filter((p) => !old.includes(p))]);

  const run = async () => {
    if (!files.length || running) return;
    setRunning(true);
    resetProgress();
    setResults(null);
    setError(null);
    try {
      const r = await office2pdf(files, outDir);
      setResults(r.results);
      if (r.results.some((x) => !x.ok)) Message.warning('部分文件转换失败，见下方详情');
    } catch (e) {
      setError(String(e));
      Message.error('转换失败');
    }
    setRunning(false);
  };

  if (engine && !engine.soffice) {
    return (
      <div className="page">
        <Alert
          type="warning"
          title="未检测到 LibreOffice"
          content="本功能依赖 LibreOffice 转换引擎。安装：brew install --cask libreoffice（安装后重启应用即可）。"
        />
      </div>
    );
  }

  return (
    <div className="page">
      <Dropzone
        kind="office"
        accept={OFFICE_EXTS}
        multiple
        title="点击选择文件（可多选）"
        hint="支持 Word / Excel / PPT；也可以一次拖入多个文件"
        onFiles={addFiles}
      />

      {files.length > 0 && (
        <div className="card">
          <div className="section-title">待转换（{files.length}）</div>
          {files.map((f) => (
            <div className="file-row" key={f}>
              <IconFile className="file-icon office" />
              <div className="file-info">
                <Text bold={false}>{basename(f)}</Text>
                <Text type="secondary" className="file-path">
                  {f}
                </Text>
              </div>
              <Button
                icon={<IconClose />}
                circle
                size="mini"
                disabled={running}
                onClick={() => setFiles((old) => old.filter((x) => x !== f))}
              />
            </div>
          ))}
          <div className="form-row" style={{ marginTop: 14 }}>
            <span className="form-label">输出到</span>
            <span className="form-value">{outDir ?? '各自输出到源文件所在目录'}</span>
            <Button
              size="mini"
              disabled={running}
              onClick={async () => {
                const d = await pickDir();
                if (d) setOutDir(d);
              }}
            >
              更改…
            </Button>
          </div>
          <Button type="primary" size="large" loading={running} style={{ marginTop: 14 }} onClick={run}>
            开始转换{files.length > 0 && !running ? `（${files.length} 个文件）` : ''}
          </Button>
        </div>
      )}

      {running && (
        <div className="card">
          <Progress percent={progress.percent} showText />
          <div className="progress-msg">{progress.stage || '正在转换…'}</div>
        </div>
      )}

      {results && !running && (
        <div className="card">
          <div className="section-title">转换结果</div>
          {results.map((r) => (
            <div className={`result-row ${r.ok ? 'ok' : 'err'}`} key={r.input}>
              <Tag color={r.ok ? 'green' : 'red'} size="small">
                {r.ok ? '成功' : '失败'}
              </Tag>
              <span className="path">{r.ok ? r.output : `${basename(r.input)}：${r.error}`}</span>
              {r.ok && r.output && (
                <span style={{ display: 'inline-flex', gap: 6 }}>
                  <Button size="mini" onClick={() => openPath(r.output!).catch((e) => Message.error(String(e)))}>
                    打开
                  </Button>
                  <Button size="mini" icon={<IconFolder />} onClick={() => openPath(dirname(r.output!)).catch(() => {})} />
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {error && !running && (
        <div className="card">
          <Alert type="error" title="转换失败" content={error} />
        </div>
      )}
    </div>
  );
}
