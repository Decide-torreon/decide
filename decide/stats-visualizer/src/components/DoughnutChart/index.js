import {Chart, ArcElement} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

Chart.register(ArcElement);

const AVAILABLE_COLORS = [
  'rgb(255, 99, 132)',
  'rgb(54, 162, 235)',
  'rgb(255, 205, 86)'
];

const DEFAULT_DATASET_OPTIONS = {
  backgroundColor: AVAILABLE_COLORS,
  hoverOffset: 4,
};

const overrideIfUndefined = (evalValue, defaultValue) => 
  typeof evalValue === 'undefined' ? defaultValue : evalValue;

export default function DoughnutChart({ labels, datasets }) {
  const dataProps = { labels };

  dataProps.datasets = datasets.map((dataset) => ({
    ...dataset,
    ...Object.fromEntries(Object.entries(DEFAULT_DATASET_OPTIONS)
      .map(entry => [entry[0], overrideIfUndefined(dataset[entry[0]], entry[1])]))
  }));

  console.log('dataProps', dataProps);

  return (<Doughnut data={ dataProps }  />)
}