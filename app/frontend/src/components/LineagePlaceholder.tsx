'use client';

import ReactFlow, { Background, Controls, Edge, MiniMap, Node } from 'reactflow';
import 'reactflow/dist/style.css';

const nodes: Node[] = [
  { id: 'n1', position: { x: 40, y: 120 }, data: { label: '输入数据' } },
  { id: 'n2', position: { x: 260, y: 120 }, data: { label: '缺失值处理' } },
  { id: 'n3', position: { x: 500, y: 120 }, data: { label: '小模型输出' } },
  { id: 'n4', position: { x: 740, y: 120 }, data: { label: 'LLM解释' } }
];

const edges: Edge[] = [
  { id: 'e1-2', source: 'n1', target: 'n2', label: 'trace' },
  { id: 'e2-3', source: 'n2', target: 'n3', label: 'features' },
  { id: 'e3-4', source: 'n3', target: 'n4', label: 'evidence' }
];

export default function LineagePlaceholder() {
  return <div style={{ height: 500, border: '1px solid #d9d9d9', borderRadius: 6 }}><ReactFlow nodes={nodes} edges={edges} fitView><MiniMap /><Controls /><Background /></ReactFlow></div>;
}
