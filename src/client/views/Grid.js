import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';

import _ from 'lodash';
import axios from 'axios';
import { GridComp } from '../components';
import * as Actions from '../actions/Space';
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
      cuurSpaceId: 2,
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
  }

  componentDidMount() {
    this.loadGridRecord(this.state.cuurSpaceId);
  }

  // space grid start
  async getFromLS(spaceId) {
    // TODO:  Testing
    let result = null;
    await axios.get(`http://localhost:8080/api/grid/space/${spaceId}`)
      .then((response) => {
        if (response.data.payload.layouts != null && response.data.payload.layouts.length > 0) {
          result = response.data.payload;
        }
      }).catch((error) => {
        console.log(`ERROR: ${error}`);
      });
    return result;
  }

  saveToLS(spaceId) {
    const allowAttr = ['x', 'y', 'w', 'h', 'i'];
    const layouts = [];
    for (const el of this.state.tempLayouts) {
      for (const [key, value] of Object.entries(el)) {
        if (!allowAttr.includes(key)) {
          delete el[key];
        }
      }
      layouts.push(el);
    }

    axios.post('http://localhost:8080/api/grid/', {
      spaceId,
      layouts
    }).then((response) => {
      console.log(`Save ${JSON.stringify(response.data)}`);
      this.loadGridRecord(spaceId);
    }).catch((error) => {
      console.log(`ERROR: ${error}`);
    });
  }

  deleteGrid(gridId) {
    axios.delete(`http://localhost:8080/api/grid/${gridId}`, {
      gridId
    }).then((response) => {
      console.log(`Delete ${JSON.stringify(response.data)}`);
    }).catch((error) => {
      console.log(`ERROR: ${error}`);
    });
  }

  handleCancel() {
    this.loadGridRecord(this.state.cuurSpaceId);
  }

  handleUpdateLayout(layout) {
    this.setState({ tempLayouts: layout });
    this.setState({ isDirtyWrite: true });
  }

  handleSelect(gridId) {
    console.log(`handleSelect: ${JSON.stringify(gridId)}`);
    this.props.history.push('/item');
  }

  handleSave() {
    this.saveToLS(this.state.cuurSpaceId, this.state.tempLayouts);
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

    if (data === null) {
      // no record from db
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
      if (data.imgPath != null) {
        gridImgPath = data.imgPath;
      }

      // load data and set as view mode
      currMode = Constants.FORM_READONLY_MODE;
      originalLayouts = data.layouts.map(l => ({ ...l, static: true }));

      // extract tagslist to form map
      for (const layout of originalLayouts) {
        // get unique tags list
        const tagList = [];
        for (const tag of layout.tagsList) {
          const tagsArr = tag.split(',');
          for (const el of tagsArr) {
            if (!tagList.includes(el)) {
              tagList.push(el);
            }
          }
        }

        // form object
        const record = {};
        record.tagList = tagList;
        record.itemCount = layout.itemCount;

        // push in map for component to form UI
        dataMap.set(layout.i, record);


        // remove tag list from each layout
        delete layout.tagsList;
      }
    }

    this.setState({
      itemCount: counter,
      tempLayouts: originalLayouts,
      dataMap,
      gridImgPath,
      currMode
    });

    this.setState({ isDirtyWrite: false });
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

    let tempList = [...this.state.tempLayouts];
    tempList = tempList.filter(el => el.i !== itemKey);

    this.setState({
      tempLayouts: tempList
    });

    if (itemKey > 0) {
      this.deleteGrid(itemKey);
    }
  }

  handleToggleMode(currMode) {
    const list = this.state.tempLayouts.map(l => ({ ...l, static: (currMode === Constants.FORM_READONLY_MODE) }));

    this.setState({
      tempLayouts: list,
      currMode
    });
  }

  // space grid end

  render() {
    const spaceId = 1;

    const {
      tempLayouts, dataMap, gridImgPath, isDirtyWrite, currMode
    } = this.state;
    const { editStatus, formState } = this.props;
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
          spaceId={spaceId}
          formState={formState}
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
  // //TODO: testing
  const userId = 1;

  const { editStatus } = state.Space;

  const inState = state.Space;
  const formState = {
    formMode: inState.formMode,
    spaceId: inState.spaceId,
    name: inState.name,
    colorCode: inState.colorCode,
    imgPath: inState.imgPath,
    tags: inState.tags,
    location: inState.location,
    sizeUnit: inState.sizeUnit,
    sizeWidth: inState.sizeWidth,
    sizeHeight: inState.sizeHeight,
    sizeDepth: inState.sizeDepth
  };

  return {
    userId,
    editStatus,
    formState
  };
};

const mapDispatchToProps = dispatch => ({
  // sagaGetSpaceList: (userId) => {
  //   dispatch(Actions.sagaGetSpaceList(userId));
  // },
  // sagaUpdateSpace: (space, fileMap) => {
  //   dispatch(Actions.sagaUpdateSpace(space, fileMap));
  // },
  // sagaAddSpace: (space, fileMap) => {
  //   dispatch(Actions.sagaAddSpace(space, fileMap));
  // },
  // sagaDeleteSpace: (userId, spaceId) => {
  //   dispatch(Actions.sagaDeleteSpace(userId, spaceId));
  // },
  // sagaGetSpace: (spaceId) => {
  //   dispatch(Actions.sagaGetSpace(spaceId));
  // },
  // sagaRemoveSpaceImg: (spaceId) => {
  //   dispatch(Actions.sagaRemoveSpaceImg(spaceId));
  // },
  // updateFormMode: (mode) => {
  //   dispatch(Actions.updateFormMode(mode));
  // }
});


Grid.propTypes = {
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  userId: PropTypes.number.isRequired

  // sagaGetSpaceList: PropTypes.func.isRequired,
  // sagaUpdateSpace: PropTypes.func.isRequired,
  // sagaAddSpace: PropTypes.func.isRequired,
  // sagaDeleteSpace: PropTypes.func.isRequired,
  // sagaGetSpace: PropTypes.func.isRequired,
  // sagaRemoveSpaceImg: PropTypes.func.isRequired,
  // updateFormMode: PropTypes.func.isRequired
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(Grid));
