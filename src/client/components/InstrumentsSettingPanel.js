import React, { Component } from 'react';
import ReactDOM from 'react-dom';

import InstrumentsSetting from './InstrumentsSetting.js'
import SaveSettings from '../commons/saveSettings.js';



class InstrumentsSettingPanel extends Component {
  constructor(props){
      super(props);
      this.onSaveSettingsHandler = this.onSaveSettingsHandler.bind(this);
      this.onLoadSettingsHandler = this.onLoadSettingsHandler.bind(this);

    }

    onSaveSettingsHandler (event) {
      this.props.onSaveSettings();
    }

    onLoadSettingsHandler (event) {
      this.props.onLoadSettings();
    }

    //I'm going to fire this for each setting
    renderInstrument(i){
      return(
        <div>

        </div>
      )

    }

    render() {
      return (
      <div>
          <button type='button' onClick={()=>this.onSaveSettingsHandler()}>
            Save
          </button>
          <button type='button' onClick={()=>this.onLoadSettingsHandler()}>
            Apply
          </button>
          <ul className={"list-group border-0"}>
            <InstrumentsSetting/>
          </ul>
        </div>
      );
    }
  }



  export default InstrumentsSettingPanel;
