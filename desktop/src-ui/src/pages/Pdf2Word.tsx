import { useState } from 'react';
import { Button, Input, Message, Progress, Result, Space, Typography } from '@arco-design/web-react';
import { IconClose, IconFilePdf, IconFolder } from '@arco-design/web-react/icon';
import Dropzone from '../components/Dropzone';
import { useEngineProgress } from '../hooks';
import { basename, dirname, openPath, pdf2word, pickSave } from '../api';

const { Text } = Typography;

export default function Pdf2Word() {
  const [file, setFile] = useState<string | null>(null);
  const [outFile, setOutFile] = useState<string | null>(null);
  const [pages, setPages] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { progress, resetProgress } = useEngineProgress();

  const run = async () => {
    if (!file || running) return;
    setRunning(true);
    resetProgress();
    setResult(null);
    setError(null);
    try {
      const r = await pdf2word(file, outFile, pages.trim() || null);
      setResult(r.output);
    } catch (e) {
      setError(String(e));
      Message.error('转换失败');
    }
    setRunning(false);
  };

  if (!file) {
    return (
      <div className="page">
        <Dropzone
          kind="pdf"
          accept={['.pdf']}
          title="点击选择 PDF 文件"
          hint="支持 .pdf，转换后即可编辑；也可以把文件直接拖到这里"
          onFiles={(ps) => {
            setFile(ps[0]);
            setOutFile(null);
            setResult(null);
            setError(null);
          }}
        />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="file-card">
        <IconFilePdf className="file-icon pdf" />
        <div className="file-info">
          <Text bold>{basename(file)}</Text>
          <Text type="secondary" className="file-path">
            {file}
          </Text>
        </div>
        <Button
          icon={<IconClose />}
          circle
          size="mini"
          disabled={running}
          onClick={() => {
            setFile(null);
            setResult(null);
            setError(null);
          }}
        />
      </div>

      <div className="card">
        <div className="form-row">
          <span className="form-label">页码范围</span>
          <Input
            value={pages}
            onChange={setPages}
            placeholder="如 1-5,8（留空 = 全部页）"
            style={{ width: 260 }}
            disabled={running}
          />
        </div>
        <div className="form-row">
          <span className="form-label">输出为</span>
          <span className="form-value">{outFile ?? '与源文件同目录同名'}</span>
          <Button
            size="mini"
            disabled={running}
            onClick={async () => {
              const p = await pickSave('docx', basename(file).replace(/\.pdf$/i, '') + '.docx');
              if (p) setOutFile(p);
            }}
          >
            更改…
          </Button>
        </div>
        <Space size={14} style={{ marginTop: 18 }}>
          <Button type="primary" size="large" loading={running} onClick={run}>
            开始转换
          </Button>
          {!running && <span className="hint">首次转换需拉起本地引擎，约 1-2 秒</span>}
        </Space>
      </div>

      {running && (
        <div className="card">
          <Progress percent={progress.percent} showText />
          <div className="progress-msg">{progress.stage || '正在转换…'}</div>
        </div>
      )}

      {result && !running && (
        <Result
          className="result-card"
          status="success"
          title="转换完成"
          subTitle={result}
          extra={[
            <Button key="open" type="primary" onClick={() => openPath(result).catch((e) => Message.error(String(e)))}>
              打开文件
            </Button>,
            <Button key="folder" icon={<IconFolder />} onClick={() => openPath(dirname(result)).catch(() => {})}>
              打开所在文件夹
            </Button>,
          ]}
        />
      )}

      {error && !running && (
        <Result
          className="result-card"
          status="error"
          title="转换失败"
          subTitle={error}
          extra={<Button onClick={() => setError(null)}>知道了</Button>}
        />
      )}
    </div>
  );
}
