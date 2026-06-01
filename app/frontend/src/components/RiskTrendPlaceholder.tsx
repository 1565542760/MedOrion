'use client';

import ReactECharts from 'echarts-for-react';

export default function RiskTrendPlaceholder() {
  const option = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['06:00', '08:00', '10:00', '12:00', '14:00', '16:00'] },
    yAxis: { type: 'value', min: 0, max: 1 },
    series: [{ name: 'Risk', type: 'line', smooth: true, data: [0.42, 0.51, 0.58, 0.66, 0.63, 0.61] }]
  };
  return <ReactECharts option={option} style={{ height: 300 }} />;
}
