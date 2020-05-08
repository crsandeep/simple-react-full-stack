import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';

import _ from 'lodash';
import axios from 'axios';
import { GridComp } from '../components';
import * as Actions from '../actions/Grid';
import * as Constants from '../constants/Grid';


export class Grid extends React.Component {
  constructor(props) {
    super(props);

    // space grid
    this.state = {
      itemCount: 0,
      tempLayouts: [],
      dataMap: new Map(),
      gridImgPath: null,
      isResetLayout: false,
      isDirtyWrite: false,
      currMode: Constants.FORM_READONLY_MODE
    };

    this.handleNew = this.handleNew.bind(this);
    this.handleSave = this.handleSave.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleUpdateLayout = this.handleUpdateLayout.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleToggleMode = this.handleToggleMode.bind(this);
    this.handleRemove = this.handleRemove.bind(this);
    this.handleGoBack = this.handleGoBack.bind(this);
  }

  componentDidMount() {
    this.loadGridRecord(this.props.spaceId);
  }

  componentDidUpdate(prevProps, prevState) {
    // clear side effect
    if (prevProps.editStatus.isSuccess !== this.props.editStatus.isSuccess
      && prevProps.editStatus.isSuccess == null) {
      // delete case
      if (this.props.editStatus.operation === Constants.OPERATION_DELETE) {
        if (this.props.editStatus.isSuccess) {
          // delete success - remove in UI
          this.deleteGridInUI(`${this.props.editStatus.data.gridId}`);
        }

        setTimeout(() => this.props.clearEditStatus(), 5000);
      }
    }
  }

  // space grid start
  async getFromLS(spaceId) {
    // TODO:  Testing
    let result = null;
    await axios.get(`http://localhost:8080/api/grid/space/${spaceId}`)
      .then((response) => {
        if (response.data.payload != null && response.data.payload.length > 0) {
          result = response.data.payload;
        }
      }).catch((error) => {
        console.log(`ERROR: ${error}`);
      });
    return result;
  }

  saveToLS(spaceId) {
    const allowAttr = ['x', 'y', 'w', 'h', 'i'];
    const grids = [];
    for (const el of this.state.tempLayouts) {
      for (const [key, value] of Object.entries(el)) {
        if (!allowAttr.includes(key)) {
          delete el[key];
        }
      }
      // generate each grid
      const grid = {
        layout: el,
        gridId: (parseInt(el.i, 10) < 0 ? null : parseInt(el.i, 10)),
        spaceId
      };

      // push as list
      grids.push(grid);
    }

    axios.post('http://localhost:8080/api/grid/', {
      grids
    }).then((response) => {
      console.log(`Save ${JSON.stringify(response.data)}`);
      this.loadGridRecord(spaceId);
    }).catch((error) => {
      console.log(`ERROR: ${error}`);
    });
  }

  handleCancel() {
    this.loadGridRecord(this.props.spaceId);
  }

  handleGoBack() {
    this.props.history.push('/space');
  }

  handleUpdateLayout(layout) {
    this.setState({ tempLayouts: layout });
    if (this.state.isResetLayout) {
      // update layout by reset data from backend
      this.setState({ isResetLayout: false });
    } else {
      // this update layout not triggered by reset data
      this.setState({ isDirtyWrite: true });
    }
  }

  handleSelect(gridId) {
    this.props.history.push('/item');
  }

  handleSave() {
    this.saveToLS(this.props.spaceId, this.state.tempLayouts);
    this.setState({ isDirtyWrite: false });
  }
  // ------------------------------------------


  async loadGridRecord(spaceId) {
    const data = await this.getFromLS(spaceId);
    let originalLayouts = null;
    let gridImgPath = null;
    let currMode = null;
    const dataMap = new Map();
    const counter = -1;

    // no record from db
    if (data === null || data.length === 0) {
      // add one as default

      originalLayouts = [{
        w: 2,
        h: 1,
        x: 0,
        y: 0, // puts it at the bottom
        i: '-1'
      }];
      currMode = Constants.FORM_EDIT_MODE;
    } else {
      // load record from db

      // extract image path for display
      gridImgPath = data[0].gridImgPath;

      const layouts = [];
      for (const grid of data) {
        // prepare grid layouts
        layouts.push(grid.layout);

        // prepare unique item tags list
        const tagList = [];
        for (const tag of grid.itemTags) {
          const tagsArr = tag.split(',');
          for (const el of tagsArr) {
            if (!tagList.includes(el)) {
              tagList.push(el);
            }
          }
        }

        // add tagsList into grid for UI proess
        grid.tagList = tagList;

        // push in map for component to form UI
        dataMap.set(`${grid.gridId}`, grid);
      }

      // load data and set as view mode
      currMode = Constants.FORM_READONLY_MODE;
      originalLayouts = layouts.map(el => ({ ...el, static: true }));
    }


    this.setState({
      itemCount: counter,
      tempLayouts: originalLayouts,
      dataMap,
      gridImgPath,
      currMode,
      isDirtyWrite: false,
      isResetLayout: true // prevent cause dirty write by layout reload
    });
  }

  handleNew() {
    let nextId = this.state.itemCount;
    nextId -= 1;

    const newGrid = {
      w: 2,
      h: 1,
      x: 0,
      y: Infinity, // puts it at the bottom
      i: `${nextId}`
    };

    const tempList = [...this.state.tempLayouts].map(l => ({ ...l, static: false }));
    tempList.push(newGrid);

    this.setState({
      itemCount: nextId,
      tempLayouts: tempList,
      currMode: Constants.FORM_EDIT_MODE
    });
  }

  handleRemove(itemKey) {
    // keep at least 1 element
    if (this.state.tempLayouts.length === 1) {
      alert('Fail to delete, at least one grid in your space!');
      return;
    }

    if (itemKey > 0) {
      // delete from db first
      this.props.sagaDeleteGrid(itemKey);
    } else {
      // delete directly (new grid)
      this.deleteGridInUI(itemKey);
    }
  }

  deleteGridInUI(itemKey) {
    // filter item by i(grid id in String)
    const orignList = [...this.state.tempLayouts];
    const tempList = orignList.filter(el => el.i !== itemKey);

    this.setState({
      tempLayouts: tempList,
      isResetLayout: true // prevent cause dirty write by layout reload
    });
  }

  handleToggleMode(currMode) {
    if (currMode === Constants.FORM_READONLY_MODE && this.state.isDirtyWrite) {
      alert('Please save your change before change back to View Mode.');
      return;
    }

    const list = this.state.tempLayouts.map(l => ({ ...l, static: (currMode === Constants.FORM_READONLY_MODE) }));

    this.setState({
      tempLayouts: list,
      currMode
    });
  }

  // space grid end

  render() {
    const {
      tempLayouts, dataMap, gridImgPath, isDirtyWrite, currMode
    } = this.state;
    const { editStatus, pageLoading } = this.props;
    return (
      <div>
        <GridComp
          handleNew={this.handleNew}
          handleToggleMode={this.handleToggleMode}
          handleSave={this.handleSave}
          handleCancel={this.handleCancel}
          handleUpdateLayout={this.handleUpdateLayout}
          handleRemove={this.handleRemove}
          handleSelect={this.handleSelect}
          handleGoBack={this.handleGoBack}
          editStatus={editStatus}
          pageLoading={pageLoading}
          tempLayouts={tempLayouts}
          dataMap={dataMap}
          gridImgPath={gridImgPath}
          isDirtyWrite={isDirtyWrite}
          currMode={currMode}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  // TODO: testing
  const spaceId = 2;

  const { editStatus, pageLoading } = state.Grid;

  return {
    spaceId,
    editStatus,
    pageLoading
  };
};

const mapDispatchToProps = dispatch => ({
  sagaGetGridList: (spaceId) => {
    dispatch(Actions.sagaGetGridList(spaceId));
  },
  sagaSaveGrids: (grids) => {
    dispatch(Actions.sagaSaveGrids(grids));
  },
  sagaDeleteGrid: (gridId) => {
    dispatch(Actions.sagaDeleteGrid(gridId));
  },
  clearEditStatus: () => {
    dispatch(Actions.clearEditStatus());
  }
});


Grid.propTypes = {
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  history: PropTypes.oneOfType([PropTypes.object]).isRequired,
  spaceId: PropTypes.number.isRequired,
  pageLoading: PropTypes.bool.isRequired,
  sagaSaveGrids: PropTypes.func.isRequired,
  sagaGetGridList: PropTypes.func.isRequired,
  sagaDeleteGrid: PropTypes.func.isRequired,
  clearEditStatus: PropTypes.func.isRequired
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(Grid));
