import { useEffect, useState } from 'react';
import { getVersion } from '@tauri-apps/api/app';
import { Layout, Menu, Tag, Typography } from '@arco-design/web-react';
import { IconCopy, IconFile, IconFilePdf, IconImage, IconThunderbolt } from '@arco-design/web-react/icon';
import { engineStatus, type EngineStatus } from './api';
import Pdf2Word from './pages/Pdf2Word';
import Office2Pdf from './pages/Office2Pdf';

const { Sider, Content } = Layout;
const { Text } = Typography;

const PAGE_META: Record<string, { title: string; desc: string }> = {
  pdf2word: { title: 'PDF 转 Word', desc: '把 PDF 转成可编辑的 .docx 文档 · 本地处理，文件不出电脑' },
  office2pdf: { title: 'Office 转 PDF', desc: 'Word / Excel / PPT 一键转 PDF · 支持批量' },
};

export default function App() {
  const [page, setPage] = useState('pdf2word');
  const [engine, setEngine] = useState<EngineStatus | null>(null);
  const [version, setVersion] = useState('');

  useEffect(() => {
    engineStatus()
      .then(setEngine)
      .catch(() => setEngine({ version: '?', soffice: false }));
    getVersion().then(setVersion).catch(() => {});
  }, []);

  const meta = PAGE_META[page];

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider width={228} className="sider">
        <div className="brand">
          <span className="brand-cn">OfficeKit</span>
          <span className="brand-en">办公工具箱</span>
        </div>
        <Menu theme="dark" selectedKeys={[page]} onClickMenuItem={(k) => setPage(k)} style={{ width: '100%' }}>
          <Menu.Item key="pdf2word">
            <IconFilePdf /> PDF 转 Word
          </Menu.Item>
          <Menu.Item key="office2pdf">
            <IconFile /> Office 转 PDF
          </Menu.Item>
          <Menu.Item disabled key="ocr">
            <IconImage /> 图片转文字
          </Menu.Item>
          <Menu.Item disabled key="pdftools">
            <IconCopy /> PDF 合并 / 拆分
          </Menu.Item>
          <Menu.Item disabled key="ai">
            <IconThunderbolt /> AI 助手
          </Menu.Item>
        </Menu>
        <div className="sider-footer">
          <Tag color={engine ? 'green' : 'gray'} size="small">
            {engine ? `引擎 v${engine.version}` : '引擎连接中…'}
          </Tag>
          <Tag color={engine?.soffice ? 'green' : 'orange'} size="small">
            LibreOffice {engine?.soffice ? '就绪' : '未安装'}
          </Tag>
          {version && (
            <Text className="ver">v{version}</Text>
          )}
        </div>
      </Sider>
      <Content className="content">
        <div className="page-head">
          <h1>{meta.title}</h1>
          <p>{meta.desc}</p>
        </div>
        {page === 'pdf2word' ? <Pdf2Word /> : <Office2Pdf engine={engine} />}
      </Content>
    </Layout>
  );
}
