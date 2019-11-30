import React, { Component } from 'react';
import ReactDOM from 'react-dom';

class BodiesParamMonitor extends Component {
  constructor(props){
      super(props);
      this.bodyParam = this.props.bodyParam;
    }

    render() {
      return (
          <ul className={"list-group border-0"}>
            <li className={"list-group-item border-0"}>{this.bodyParam.cx}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.cy}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.cy}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.hlx}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.hly}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.hrx}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.hry}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.hocx}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.hocy}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.Scx}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.Scy}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.Fcx}</li>
            <li className={"list-group-item border-0"}>{this.bodyParam.Fcy}</li>
          </ul>
      );
    }
  }

export default BodiesParamMonitor;
