import React from 'react';
// import d3Utils from './utils/d3utils';
// import d3Config from './config';

export default class PriceGraph extends React.Component {
  constructor(props) {
    // We'll fill this out soon
    super();
  }

  componentDidMount() {
    // const { timeSeriesData } = this.props;
    // d3Utils.initializeChart(timeSeriesData, 'monthToDate');
  }

  componentDidUpdate(prevProps) {
    // This too
  }

  componentWillUnmount() {
    // And finally this
  }

  render() {
    return (
      <svg className="line-chart" width="100%" height={500} />
    );
  }
}
